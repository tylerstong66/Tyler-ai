import hashlib
import hmac
import json
import os
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone

import requests


MAINTENANCE_MERGE_CATEGORY = 'maintenance_merge'
MAINTENANCE_MERGE_SCHEMA = 'tyler_maintenance_merge_v1'
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_APPROVAL_TTL_MINUTES = 30


def _utcnow():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.isoformat() if value else None


def _parse_iso(value):
    text = str(value or '').strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _safe_text(value, limit=500):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    text = re.sub(
        r'(?i)\b(api[_-]?key|token|password|secret|authorization)\s*[:=]\s*[^,;|]+',
        r'\1=<redacted>',
        text,
    )
    text = re.sub(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+', 'Bearer <redacted>', text)
    return text[:limit]


def merge_id_for(promotion_id, proposal_commit_sha):
    raw = f"{str(promotion_id or '').upper()}:{str(proposal_commit_sha or '').lower()}"
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:10].upper()
    return f'MRG-{digest}'


class MaintenanceMergeCoordinator:
    """Human-gated merge for an exact v2.16-created maintenance pull request.

    Safety invariant: merge is impossible unless Render auto-deploy has been
    explicitly confirmed disabled. This keeps GitHub merge and production
    deployment as separate human-controlled actions.
    """

    def __init__(
        self,
        promotion_loader,
        review_gate,
        supabase_url_fn,
        headers_fn,
        version_fn,
        github_token_fn=None,
        github_repository_fn=None,
        github_base_branch_fn=None,
        render_auto_deploy_disabled_fn=None,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        approval_ttl_minutes=DEFAULT_APPROVAL_TTL_MINUTES,
        now_fn=None,
    ):
        self.promotion_loader = promotion_loader
        self.review_gate = review_gate
        self.supabase_url_fn = supabase_url_fn
        self.headers_fn = headers_fn
        self.version_fn = version_fn
        self.github_token_fn = github_token_fn or (lambda: os.environ.get('GITHUB_MAINTENANCE_TOKEN', ''))
        self.github_repository_fn = github_repository_fn or (
            lambda: os.environ.get('GITHUB_MAINTENANCE_REPOSITORY', 'tylerstong66/Tyler-ai')
        )
        self.github_base_branch_fn = github_base_branch_fn or (
            lambda: os.environ.get('GITHUB_MAINTENANCE_BASE_BRANCH', 'main')
        )
        self.render_auto_deploy_disabled_fn = render_auto_deploy_disabled_fn or (
            lambda: str(os.environ.get('RENDER_AUTO_DEPLOY_DISABLED_CONFIRMED', '')).strip().lower()
            in {'1', 'true', 'yes', 'on'}
        )
        self.timeout_seconds = max(3, min(int(timeout_seconds), 30))
        self.approval_ttl_minutes = max(5, min(int(approval_ttl_minutes), 120))
        self.now_fn = now_fn or _utcnow
        self._lock = threading.RLock()
        self._prepared_this_process = 0
        self._approved_this_process = 0
        self._merged_this_process = 0
        self._last_error_category = None

    def persistence_configured(self):
        try:
            return bool(self.supabase_url_fn() and self.headers_fn())
        except Exception:
            return False

    def github_token_present(self):
        try:
            repo = str(self.github_repository_fn() or '').strip()
            token = str(self.github_token_fn() or '').strip()
            return bool(token and re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo))
        except Exception:
            return False

    def render_auto_deploy_confirmed_disabled(self):
        try:
            return bool(self.render_auto_deploy_disabled_fn())
        except Exception:
            return False

    def status(self):
        with self._lock:
            return {
                'persistence_configured': self.persistence_configured(),
                'github_token_present': self.github_token_present(),
                'render_auto_deploy_confirmed_disabled': self.render_auto_deploy_confirmed_disabled(),
                'prepared_this_process': int(self._prepared_this_process),
                'approved_this_process': int(self._approved_this_process),
                'merged_this_process': int(self._merged_this_process),
                'last_error_category': self._last_error_category,
                'fresh_ready_review_required': True,
                'exact_pull_request_identity_required': True,
                'current_main_must_match_approved_base': True,
                'human_merge_approval_required': True,
                'separate_execute_command_required_after_approval': True,
                'render_auto_deploy_must_be_disabled_before_merge': True,
                'automatic_merge_enabled': False,
                'automatic_production_deployment_enabled': False,
                'blind_retry_after_unknown_merge_outcome_enabled': False,
            }

    def _post_memory(self, payload, importance=10):
        if not self.persistence_configured():
            self._last_error_category = 'persistence_not_configured'
            return False
        try:
            response = requests.post(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers={**self.headers_fn(), 'Prefer': 'return=minimal'},
                json={
                    'memories': json.dumps(payload, separators=(',', ':'), sort_keys=True),
                    'category': MAINTENANCE_MERGE_CATEGORY,
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

    def _load_rows(self, limit=100):
        if not self.persistence_configured():
            return []
        try:
            response = requests.get(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers=self.headers_fn(),
                params={
                    'select': 'id,created_at,memories',
                    'category': f'eq.{MAINTENANCE_MERGE_CATEGORY}',
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

    def recent(self, limit=20):
        latest = {}
        for item in self._load_rows(limit=max(30, int(limit) * 4)):
            key = str(item.get('merge_id') or '').upper()
            if key and key not in latest:
                latest[key] = item
        return list(latest.values())[:max(1, min(int(limit), 50))]

    def merge_record(self, merge_id):
        target = str(merge_id or '').strip().upper()
        for item in self.recent(limit=50):
            if str(item.get('merge_id') or '').upper() == target:
                return item
        return None

    def _github_headers(self):
        token = str(self.github_token_fn() or '').strip()
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    def _github_request(self, method, path, **kwargs):
        repo = str(self.github_repository_fn() or '').strip()
        return requests.request(
            method,
            f'https://api.github.com/repos/{repo}{path}',
            headers=self._github_headers(),
            timeout=self.timeout_seconds,
            **kwargs,
        )

    @staticmethod
    def _review_identity(review):
        review = dict(review or {})
        return {
            'review_id': str(review.get('review_id') or ''),
            'execution_id': str(review.get('execution_id') or '').upper(),
            'repository': str(review.get('repository') or ''),
            'base_branch': str(review.get('base_branch') or ''),
            'review_branch': str(review.get('review_branch') or ''),
            'base_commit_sha': str(review.get('base_commit_sha') or ''),
            'proposal_commit_sha': str(review.get('proposal_commit_sha') or ''),
        }

    @staticmethod
    def _promotion_identity(promotion):
        promotion = dict(promotion or {})
        return {
            'review_id': str(promotion.get('review_id') or ''),
            'execution_id': str(promotion.get('execution_id') or '').upper(),
            'repository': str(promotion.get('repository') or ''),
            'base_branch': str(promotion.get('base_branch') or ''),
            'review_branch': str(promotion.get('review_branch') or ''),
            'base_commit_sha': str(promotion.get('base_commit_sha') or ''),
            'proposal_commit_sha': str(promotion.get('proposal_commit_sha') or ''),
        }

    def _fresh_ready_review(self, promotion):
        result = self.review_gate.review(str(promotion.get('execution_id') or '').upper(), persist=False)
        if not result.get('success'):
            return None, str(result.get('error') or 'review_failed')
        review = dict(result.get('review') or {})
        if str(review.get('gate_status') or '').lower() != 'ready':
            return review, f"review_{str(review.get('gate_status') or 'not_ready').lower()}"
        if self._review_identity(review) != self._promotion_identity(promotion):
            return review, 'review_identity_drift'
        return review, None

    @staticmethod
    def _pr_summary(pr):
        return {
            'number': pr.get('number'),
            'html_url': pr.get('html_url'),
            'state': str(pr.get('state') or ''),
            'draft': bool(pr.get('draft')),
            'merged': bool(pr.get('merged')),
            'merged_at': pr.get('merged_at'),
            'merge_commit_sha': str(pr.get('merge_commit_sha') or ''),
            'head_ref': str((pr.get('head') or {}).get('ref') or ''),
            'head_sha': str((pr.get('head') or {}).get('sha') or ''),
            'base_ref': str((pr.get('base') or {}).get('ref') or ''),
            'base_sha': str((pr.get('base') or {}).get('sha') or ''),
            'mergeable': pr.get('mergeable'),
        }

    def _load_and_validate_pr(self, promotion):
        number = promotion.get('pull_request_number')
        if not number:
            return None, 'promotion_pull_request_missing'
        try:
            response = self._github_request('GET', f'/pulls/{int(number)}')
        except requests.RequestException:
            return None, 'github_pull_request_lookup_failed'
        if not response.ok:
            return None, f'github_pull_request_lookup_http_{response.status_code}'
        try:
            pr = self._pr_summary(response.json() or {})
        except Exception:
            return None, 'github_pull_request_lookup_invalid_json'

        if pr['head_ref'] != str(promotion.get('review_branch') or ''):
            return pr, 'pull_request_head_branch_drift'
        if pr['head_sha'] != str(promotion.get('proposal_commit_sha') or ''):
            return pr, 'pull_request_head_sha_drift'
        if pr['base_ref'] != str(promotion.get('base_branch') or 'main') or pr['base_ref'] != 'main':
            return pr, 'pull_request_base_branch_drift'
        if pr['draft']:
            return pr, 'pull_request_is_draft'
        if pr['merged']:
            return pr, 'pull_request_already_merged'
        if pr['state'] != 'open':
            return pr, 'pull_request_not_open'
        if pr['mergeable'] is False:
            return pr, 'pull_request_not_mergeable'
        return pr, None

    def _load_promotion(self, promotion_id):
        promotion = self.promotion_loader(str(promotion_id or '').upper())
        if not promotion:
            return None, 'promotion_not_found'
        if str(promotion.get('status') or '') != 'pull_request_created' or not promotion.get('pull_request_created'):
            return promotion, 'promotion_has_no_created_pull_request'
        if str(promotion.get('repository') or '') != str(self.github_repository_fn() or '').strip():
            return promotion, 'promotion_repository_mismatch'
        if str(promotion.get('base_branch') or '') != str(self.github_base_branch_fn() or 'main').strip():
            return promotion, 'promotion_base_branch_mismatch'
        return promotion, None

    def _validate_before_merge(self, promotion):
        if not self.render_auto_deploy_confirmed_disabled():
            return None, None, 'render_auto_deploy_not_confirmed_disabled'
        review, error = self._fresh_ready_review(promotion)
        if error:
            return review, None, f'fresh_review_failed:{error}'
        pr, error = self._load_and_validate_pr(promotion)
        if error:
            return review, pr, error
        return review, pr, None

    def prepare(self, promotion_id, persist=True):
        promotion, error = self._load_promotion(promotion_id)
        if error:
            return {'success': False, 'error': error, 'promotion': promotion}
        review, pr, error = self._validate_before_merge(promotion)
        if error:
            return {'success': False, 'error': error, 'promotion': promotion, 'review': review, 'pull_request': pr}

        merge_id = merge_id_for(promotion.get('promotion_id'), promotion.get('proposal_commit_sha'))
        existing = self.merge_record(merge_id) if persist else None
        if existing and str(existing.get('status') or '') in {'awaiting_approval', 'approved', 'merged'}:
            return {'success': True, 'merge': existing, 'saved': True, 'existing': True}

        now = self.now_fn()
        record = {
            'schema': MAINTENANCE_MERGE_SCHEMA,
            'merge_id': merge_id,
            'promotion_id': str(promotion.get('promotion_id') or '').upper(),
            'execution_id': str(promotion.get('execution_id') or '').upper(),
            'review_id': str(promotion.get('review_id') or ''),
            'repository': str(promotion.get('repository') or ''),
            'base_branch': str(promotion.get('base_branch') or ''),
            'review_branch': str(promotion.get('review_branch') or ''),
            'base_commit_sha': str(promotion.get('base_commit_sha') or ''),
            'proposal_commit_sha': str(promotion.get('proposal_commit_sha') or ''),
            'pull_request_number': pr.get('number'),
            'pull_request_url': pr.get('html_url'),
            'version': str(self.version_fn() or ''),
            'prepared_at': _iso(now),
            'status': 'awaiting_approval',
            'approval_required': True,
            'approval_code': secrets.token_hex(3).upper(),
            'approval_granted': False,
            'approval_expires_at': None,
            'ready_review_revalidated_at': _iso(now),
            'pull_request_revalidated_at': _iso(now),
            'render_auto_deploy_confirmed_disabled': True,
            'human_gated_merge_performed': False,
            'automatic_merge_performed': False,
            'production_deployment_performed': False,
            'unknown_side_effect_retry_performed': False,
        }
        saved = self._post_memory(record, importance=10) if persist else False
        if persist and not saved:
            return {'success': False, 'error': 'merge_preparation_not_persisted', 'merge': record}
        with self._lock:
            self._prepared_this_process += 1
        return {'success': True, 'merge': record, 'saved': bool(saved), 'existing': False}

    def approve(self, merge_id, approval_code):
        record = self.merge_record(merge_id)
        if not record:
            return {'success': False, 'error': 'merge_record_not_found'}
        if str(record.get('status') or '') != 'awaiting_approval':
            return {'success': False, 'error': 'merge_not_awaiting_approval', 'merge': record}
        supplied = str(approval_code or '').strip().upper()
        expected = str(record.get('approval_code') or '').strip().upper()
        if not expected or not hmac.compare_digest(expected, supplied):
            return {'success': False, 'error': 'approval_code_invalid'}

        promotion, error = self._load_promotion(record.get('promotion_id'))
        if error:
            return {'success': False, 'error': error, 'promotion': promotion}
        if str(promotion.get('proposal_commit_sha') or '') != str(record.get('proposal_commit_sha') or ''):
            return {'success': False, 'error': 'promotion_identity_drift'}
        review, pr, error = self._validate_before_merge(promotion)
        if error:
            return {'success': False, 'error': error, 'review': review, 'pull_request': pr}

        now = self.now_fn()
        updated = dict(record)
        updated.update({
            'status': 'approved',
            'approval_granted': True,
            'approved_at': _iso(now),
            'approval_expires_at': _iso(now + timedelta(minutes=self.approval_ttl_minutes)),
            'ready_review_revalidated_at': _iso(now),
            'pull_request_revalidated_at': _iso(now),
        })
        if not self._post_memory(updated, importance=10):
            return {'success': False, 'error': 'merge_approval_not_persisted'}
        with self._lock:
            self._approved_this_process += 1
        return {'success': True, 'merge': updated}

    def cancel(self, merge_id):
        record = self.merge_record(merge_id)
        if not record:
            return {'success': False, 'error': 'merge_record_not_found'}
        if str(record.get('status') or '') in {'merged', 'cancelled'}:
            return {'success': False, 'error': 'merge_not_cancellable', 'merge': record}
        updated = dict(record)
        updated.update({
            'status': 'cancelled',
            'approval_granted': False,
            'cancelled_at': _iso(self.now_fn()),
        })
        if not self._post_memory(updated, importance=9):
            return {'success': False, 'error': 'merge_cancellation_not_persisted'}
        return {'success': True, 'merge': updated}

    def _persist_merged(self, record, pr, merge_commit_sha, performed_by_this_call, verified_after_unknown=False):
        summary = self._pr_summary(pr)
        if summary['head_sha'] != str(record.get('proposal_commit_sha') or ''):
            return {'success': False, 'error': 'merged_pr_head_sha_mismatch', 'pull_request': summary}
        if summary['base_ref'] != str(record.get('base_branch') or 'main'):
            return {'success': False, 'error': 'merged_pr_base_branch_mismatch', 'pull_request': summary}
        if not summary['merged']:
            return {'success': False, 'error': 'pull_request_not_confirmed_merged', 'pull_request': summary}

        updated = dict(record)
        updated.update({
            'status': 'merged',
            'approval_granted': False,
            'merged_at': summary.get('merged_at') or _iso(self.now_fn()),
            'merge_commit_sha': str(merge_commit_sha or summary.get('merge_commit_sha') or ''),
            'human_gated_merge_performed': bool(performed_by_this_call),
            'automatic_merge_performed': False,
            'production_deployment_performed': False,
            'merge_verified_after_unknown_outcome': bool(verified_after_unknown),
            'unknown_side_effect_retry_performed': False,
        })
        if not updated['merge_commit_sha']:
            return {'success': False, 'error': 'merge_commit_sha_missing'}
        if not self._post_memory(updated, importance=10):
            return {'success': False, 'error': 'merge_result_not_persisted', 'merge': updated}
        if performed_by_this_call:
            with self._lock:
                self._merged_this_process += 1
        return {'success': True, 'merge': updated, 'pull_request': summary}

    def _verify_after_unknown_outcome(self, record):
        number = record.get('pull_request_number')
        try:
            response = self._github_request('GET', f'/pulls/{int(number)}')
        except Exception:
            response = None
        if response is not None and response.ok:
            try:
                pr = response.json() or {}
                summary = self._pr_summary(pr)
            except Exception:
                summary = None
            if summary and summary.get('merged') and summary.get('head_sha') == str(record.get('proposal_commit_sha') or ''):
                return self._persist_merged(
                    record,
                    pr,
                    summary.get('merge_commit_sha'),
                    performed_by_this_call=True,
                    verified_after_unknown=True,
                )
        return {
            'success': False,
            'error': 'github_merge_outcome_unknown',
            'retry_blocked': True,
            'merge': record,
        }

    def execute(self, merge_id):
        record = self.merge_record(merge_id)
        if not record:
            return {'success': False, 'error': 'merge_record_not_found'}
        if str(record.get('status') or '') == 'merged':
            return {'success': True, 'merge': record, 'existing': True}
        if str(record.get('status') or '') != 'approved' or not record.get('approval_granted'):
            return {'success': False, 'error': 'merge_not_approved', 'merge': record}

        expires_at = _parse_iso(record.get('approval_expires_at'))
        if not expires_at or self.now_fn() > expires_at:
            return {'success': False, 'error': 'merge_approval_expired', 'merge': record}

        promotion, error = self._load_promotion(record.get('promotion_id'))
        if error:
            return {'success': False, 'error': error, 'promotion': promotion}
        if str(promotion.get('proposal_commit_sha') or '') != str(record.get('proposal_commit_sha') or ''):
            return {'success': False, 'error': 'promotion_identity_drift'}
        review, pr, error = self._validate_before_merge(promotion)
        if error:
            return {'success': False, 'error': error, 'review': review, 'pull_request': pr}
        if not self.github_token_present():
            return {'success': False, 'error': 'github_token_not_configured'}

        number = int(record.get('pull_request_number'))
        payload = {
            'sha': str(record.get('proposal_commit_sha') or ''),
            'merge_method': 'merge',
            'commit_title': f"Merge Tyler maintenance {record.get('execution_id')}",
            'commit_message': (
                f"Human-gated merge for {record.get('promotion_id')} / {record.get('merge_id')}. "
                'Production deployment remains a separate action.'
            ),
        }
        try:
            response = self._github_request('PUT', f'/pulls/{number}/merge', json=payload)
        except requests.Timeout:
            return self._verify_after_unknown_outcome(record)
        except requests.RequestException:
            return self._verify_after_unknown_outcome(record)

        if response.status_code == 200:
            try:
                result = response.json() or {}
            except Exception:
                return self._verify_after_unknown_outcome(record)
            if not result.get('merged'):
                return {'success': False, 'error': 'github_merge_not_completed', 'detail': _safe_text(result.get('message'), 180)}
            try:
                pr_response = self._github_request('GET', f'/pulls/{number}')
                pr_payload = pr_response.json() if pr_response.ok else None
            except Exception:
                pr_payload = None
            if not isinstance(pr_payload, dict):
                return self._verify_after_unknown_outcome(record)
            return self._persist_merged(
                record,
                pr_payload,
                result.get('sha'),
                performed_by_this_call=True,
            )

        if response.status_code == 403:
            return {
                'success': False,
                'error': 'github_merge_permission_denied',
                'detail': 'GitHub merge permission is required for GITHUB_MAINTENANCE_TOKEN.',
            }
        if response.status_code in {405, 409}:
            return {'success': False, 'error': 'github_pull_request_not_mergeable'}
        if response.status_code == 422:
            return {'success': False, 'error': 'github_merge_sha_or_validation_mismatch'}
        return {
            'success': False,
            'error': f'github_merge_http_{response.status_code}',
            'detail': _safe_text(getattr(response, 'text', ''), 180),
        }
