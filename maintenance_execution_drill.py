import base64
import json
from urllib.parse import quote

import requests

from maintenance_execution import MaintenanceExecutionCoordinator


DRILL_CATEGORY = 'maintenance_execution_drill'
DRILL_TARGET_FILE = 'maintenance_execution_drill_target.py'
DRILL_FIND = 'DRILL_MARKER = "base"'
DRILL_REPLACE = 'DRILL_MARKER = "review-branch-test"'


class SafeMaintenanceExecutionDrillCoordinator(MaintenanceExecutionCoordinator):
    """Maintenance executor isolated from real maintenance-execution history."""

    def _post_memory(self, payload, importance=8):
        if not self.persistence_configured():
            self._last_error_category = 'persistence_not_configured'
            return False
        try:
            response = requests.post(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers={**self.headers_fn(), 'Prefer': 'return=minimal'},
                json={
                    'memories': json.dumps(payload, separators=(',', ':'), sort_keys=True),
                    'category': DRILL_CATEGORY,
                    'importance': max(1, min(int(importance), 10)),
                },
                timeout=self.timeout_seconds,
            )
            if response.ok:
                self._last_error_category = None
                return True
            self._last_error_category = f'persistence_http_{response.status_code}'
        except requests.Timeout:
            self._last_error_category = 'persistence_timeout'
        except Exception:
            self._last_error_category = 'persistence_write_error'
        return False

    def _load_rows(self, limit=80):
        if not self.persistence_configured():
            return []
        try:
            response = requests.get(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers=self.headers_fn(),
                params={
                    'select': 'id,created_at,memories',
                    'category': f'eq.{DRILL_CATEGORY}',
                    'order': 'created_at.desc',
                    'limit': max(1, min(int(limit), 100)),
                },
                timeout=self.timeout_seconds,
            )
            if not response.ok:
                return []
            output = []
            for row in response.json() or []:
                try:
                    item = json.loads(str(row.get('memories') or ''))
                except Exception:
                    continue
                if isinstance(item, dict):
                    item['row_id'] = row.get('id')
                    item['stored_at'] = row.get('created_at')
                    output.append(item)
            return output
        except Exception:
            return []

    def verify_published_drill(self, package):
        """Verify the proposal changed only the review branch, never main."""
        publish = dict((package or {}).get('github_publish') or {})
        branch = str(publish.get('branch') or '')
        base_branch = str(publish.get('base_branch') or self.github_base_branch_fn() or 'main')
        if not branch or str((package or {}).get('status') or '') != 'published_for_review':
            return {'success': False, 'error': 'drill_not_published_for_review'}

        def fetch_text(ref):
            response = self._github_request(
                'GET',
                f'/contents/{quote(DRILL_TARGET_FILE, safe="/")}',
                params={'ref': ref},
            )
            if not response.ok:
                raise RuntimeError(f'github_verify_http_{response.status_code}')
            encoded = str(response.json().get('content') or '').replace('\n', '')
            return base64.b64decode(encoded).decode('utf-8')

        try:
            main_text = fetch_text(base_branch)
            branch_text = fetch_text(branch)
        except Exception as exc:
            return {'success': False, 'error': 'github_verification_failed', 'detail': type(exc).__name__}

        main_unchanged = DRILL_FIND in main_text and DRILL_REPLACE not in main_text
        review_changed = DRILL_REPLACE in branch_text and DRILL_FIND not in branch_text
        safe_branch = branch.startswith('tyler-maintenance/exe-')
        return {
            'success': bool(main_unchanged and review_changed and safe_branch),
            'main_unchanged': bool(main_unchanged),
            'review_branch_changed': bool(review_changed),
            'safe_review_branch_name': bool(safe_branch),
            'branch': branch,
            'base_branch': base_branch,
            'production_deployment_performed': False,
            'pull_request_created': False,
        }


def deterministic_drill_patch(_plan, _source_context, _execution_id):
    return {
        'summary': 'Harmless v2.14.1 review-branch publication drill.',
        'changes': [
            {
                'path': DRILL_TARGET_FILE,
                'find': DRILL_FIND,
                'replace': DRILL_REPLACE,
                'reason': 'Verify approved review-branch publishing without modifying main.',
            }
        ],
    }


def make_drill_plan(plan_id):
    return {
        'maintenance_plan_id': str(plan_id or '').upper(),
        'incident_id': 'INC-D214100001',
        'service': 'github',
        'severity': 'test',
        'kind': 'safe_review_branch_drill',
        'source_grounded': True,
        'drill': True,
        'affected_code': [
            {
                'file': DRILL_TARGET_FILE,
                'functions': ['drill_marker'],
            }
        ],
        'likely_cause': 'Synthetic drill only; no production fault exists.',
        'proposed_patch': {
            'strategy': 'Change only the dedicated harmless drill marker on a review branch.'
        },
        'test_plan': [
            'Verify the review branch contains the changed drill marker.',
            'Verify main still contains the base drill marker.',
        ],
        'rollback_plan': [
            'Delete the isolated review branch if no longer needed; main requires no rollback.'
        ],
        'deployment_plan': [
            'No production deployment is part of this drill.'
        ],
        'approval_required_before_execution': True,
        'automatic_changes_performed': False,
        'automatic_deployment_performed': False,
    }
