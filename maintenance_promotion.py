import hashlib
import hmac
import json
import os
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone

import requests


MAINTENANCE_PROMOTION_CATEGORY = 'maintenance_promotion'
MAINTENANCE_PROMOTION_SCHEMA = 'tyler_maintenance_promotion_v1'
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_APPROVAL_TTL_MINUTES = 30


def _utcnow():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.isoformat() if value else None


def _safe_text(value, limit=500):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    text = re.sub(
        r'(?i)\b(api[_-]?key|token|password|secret|authorization)\s*[:=]\s*[^,;|]+',
        r'\1=<redacted>',
        text,
    )
    text = re.sub(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+', 'Bearer <redacted>', text)
    return text[:limit]


def promotion_id_for(execution_id, proposal_commit_sha):
    raw = f"{str(execution_id or '').upper()}:{str(proposal_commit_sha or '').lower()}"
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:10].upper()
    return f'PRO-{digest}'


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


class MaintenancePromotionCoordinator:
    """Human-gated promotion from a READY review into a GitHub pull request."""

    def __init__(
        self,
        review_gate,
        supabase_url_fn,
        headers_fn,
        version_fn,
        github_token_fn=None,
        github_repository_fn=None,
        github_base_branch_fn=None,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        approval_ttl_minutes=DEFAULT_APPROVAL_TTL_MINUTES,
        now_fn=None,
    ):
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
        self.timeout_seconds = max(3, min(int(timeout_seconds), 30))
        self.approval_ttl_minutes = max(5, min(int(approval_ttl_minutes), 120))
        self.now_fn = now_fn or _utcnow
        self._lock = threading.RLock()
        self._prepared_this_process = 0
        self._approved_this_process = 0
        self._prs_created_this_process = 0
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

    def status(self):
        with self._lock:
            return {
                'persistence_configured': self.persistence_configured(),
                'github_token_present': self.github_token_present(),
                'prepared_this_process': int(self._prepared_this_process),
                'approved_this_process': int(self._approved_this_process),
                'pull_requests_created_this_process': int(self._prs_created_this_process),
                'last_error_category': self._last_error_category,
                'fresh_ready_review_required': True,
                'fresh_human_approval_required': True,
                'separate_execute_command_required_after_approval': True,
                'pull_request_permission_verified_only_on_execution': True,
                'automatic_pull_request_creation_enabled': False,
                'automatic_merge_enabled': False,
                'direct_main_write_enabled': False,
                'automatic_production_deployment_enabled': False,
                'blind_retry_after_unknown_pr_outcome_enabled': False,
            }

    def _post_memory(self, payload, importance=9):
        if not self.persistence_configured():
            self._last_error_category = 'persistence_not_configured'
            return False
        try:
            response = requests.post(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers={**self.headers_fn(), 'Prefer': 'return=minimal'},
                json={
                    'memories': json.dumps(payload, separators=(',', ':'), sort_keys=True),
                    'category': MAINTENANCE_PROMOTION_CATEGORY,
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
                    'category': f'eq.{MAINTENANCE_PROMOTION_CATEGORY}',
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
            key = str(item.get('promotion_id') or '').upper()
            if key and key not in latest:
                latest[key] = item
        return list(latest.values())[:max(1, min(int(limit), 50))]

    def promotion(self, promotion_id):
        target = str(promotion_id or '').strip().upper()
        for item in self.recent(limit=50):
            if str(item.get('promotion_id') or '').upper() == target:
                return item
        return None

    def _fresh_ready_review(self, execution_id):
        result = self.review_gate.review(str(execution_id or '').upper(), persist=False)
        if not result.get('success'):
            return None, str(result.get('error') or 'review_failed')
        review = dict(result.get('review') or {})
        if str(review.get('gate_status') or '').lower() != 'ready':
            return review, f"review_{str(review.get('gate_status') or 'not_ready').lower()}"
        return review, None

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
    def _same_identity(promotion, review):
        expected = {
            'review_id': str(promotion.get('review_id') or ''),
            'execution_id': str(promotion.get('execution_id') or '').upper(),
            'repository': str(promotion.get('repository') or ''),
            'base_branch': str(promotion.get('base_branch') or ''),
            'review_branch': str(promotion.get('review_branch') or ''),
            'base_commit_sha': str(promotion.get('base_commit_sha') or ''),
            'proposal_commit_sha': str(promotion.get('proposal_commit_sha') or ''),
        }
        return expected == MaintenancePromotionCoordinator._review_identity(review)

    def prepare(self, execution_id, persist=True):
        review, error = self._fresh_ready_review(execution_id)
        if error:
            return {'success': False, 'error': error, 'review': review}
        identity = self._review_identity(review)
        if identity['repository'] != str(self.github_repository_fn() or '').strip():
            return {'success': False, 'error': 'review_repository_mismatch'}
        if identity['base_branch'] != str(self.github_base_branch_fn() or 'main').strip() or identity['base_branch'] != 'main':
            return {'success': False, 'error': 'review_base_branch_mismatch'}
        if not identity['proposal_commit_sha'] or not identity['review_branch']:
            return {'success': False, 'error': 'review_identity_incomplete'}

        promotion_id = promotion_id_for(identity['execution_id'], identity['proposal_commit_sha'])
        existing = self.promotion(promotion_id) if persist else None
        if existing and str(existing.get('status') or '') in {'awaiting_approval', 'approved', 'pull_request_created'}:
            return {'success': True, 'promotion': existing, 'saved': True, 'existing': True}

        now = self.now_fn()
        promotion = {
            'schema': MAINTENANCE_PROMOTION_SCHEMA,
            'promotion_id': promotion_id,
            **identity,
            'version': str(self.version_fn() or ''),
            'prepared_at': _iso(now),
            'status': 'awaiting_approval',
            'approval_required': True,
            'approval_code': secrets.token_hex(3).upper(),
            'approval_granted': False,
            'approval_expires_at': None,
            'ready_review_revalidated_at': _iso(now),
            'github_write_performed': False,
            'pull_request_created': False,
            'automatic_merge_performed': False,
            'direct_main_write_performed': False,
            'production_deployment_performed': False,
            'unknown_side_effect_retry_performed': False,
        }
        saved = self._post_memory(promotion, importance=9) if persist else False
        if persist and not saved:
            return {'success': False, 'error': 'promotion_not_persisted', 'promotion': promotion}
        with self._lock:
            self._prepared_this_process += 1
        return {'success': True, 'promotion': promotion, 'saved': bool(saved), 'existing': False}

    def approve(self, promotion_id, approval_code):
        promotion = self.promotion(promotion_id)
        if not promotion:
            return {'success': False, 'error': 'promotion_not_found'}
        if str(promotion.get('status') or '') != 'awaiting_approval':
            return {'success': False, 'error': 'promotion_not_awaiting_approval', 'promotion': promotion}
        supplied = str(approval_code or '').strip().upper()
        expected = str(promotion.get('approval_code') or '').strip().upper()
        if not expected or not hmac.compare_digest(expected, supplied):
            return {'success': False, 'error': 'approval_code_invalid'}

        review, error = self._fresh_ready_review(promotion.get('execution_id'))
        if error:
            return {'success': False, 'error': f'fresh_review_failed:{error}', 'review': review}
        if not self._same_identity(promotion, review):
            return {'success': False, 'error': 'review_identity_drift'}

        now = self.now_fn()
        updated = dict(promotion)
        updated.update({
            'status': 'approved',
            'approval_granted': True,
            'approved_at': _iso(now),
            'approval_expires_at': _iso(now + timedelta(minutes=self.approval_ttl_minutes)),
            'ready_review_revalidated_at': _iso(now),
        })
        if not self._post_memory(updated, importance=10):
            return {'success': False, 'error': 'promotion_approval_not_persisted'}
        with self._lock:
            self._approved_this_process += 1
        return {'success': True, 'promotion': updated}

    def cancel(self, promotion_id):
        promotion = self.promotion(promotion_id)
        if not promotion:
            return {'success': False, 'error': 'promotion_not_found'}
        if str(promotion.get('status') or '') in {'pull_request_created', 'cancelled'}:
            return {'success': False, 'error': 'promotion_not_cancellable', 'promotion': promotion}
        updated = dict(promotion)
        updated.update({
            'status': 'cancelled',
            'approval_granted': False,
            'cancelled_at': _iso(self.now_fn()),
        })
        if not self._post_memory(updated, importance=8):
            return {'success': False, 'error': 'promotion_cancellation_not_persisted'}
        return {'success': True, 'promotion': updated}

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

    def _find_existing_open_pr(self, promotion):
        repo = str(promotion.get('repository') or '')
        owner = repo.split('/', 1)[0] if '/' in repo else ''
        branch = str(promotion.get('review_branch') or '')
        base = str(promotion.get('base_branch') or 'main')
        response = self._github_request(
            'GET',
            '/pulls',
            params={'state': 'open', 'head': f'{owner}:{branch}', 'base': base, 'per_page': 30},
        )
        if not response.ok:
            raise RuntimeError(f'github_pr_lookup_http_{response.status_code}')
        for pr in response.json() or []:
            head = dict(pr.get('head') or {})
            base_obj = dict(pr.get('base') or {})
            if (
                str(head.get('ref') or '') == branch
                and str(head.get('sha') or '') == str(promotion.get('proposal_commit_sha') or '')
                and str(base_obj.get('ref') or '') == base
            ):
                return pr
        return None

    @staticmethod
    def _pr_summary(pr):
        return {
            'number': pr.get('number'),
            'html_url': pr.get('html_url'),
            'state': pr.get('state'),
            'draft': bool(pr.get('draft')),
            'head_ref': str((pr.get('head') or {}).get('ref') or ''),
            'head_sha': str((pr.get('head') or {}).get('sha') or ''),
            'base_ref': str((pr.get('base') or {}).get('ref') or ''),
        }

    def _persist_pr_result(self, promotion, pr, created_by_this_call, verified_after_unknown=False):
        summary = self._pr_summary(pr)
        if (
            summary['head_ref'] != str(promotion.get('review_branch') or '')
            or summary['head_sha'] != str(promotion.get('proposal_commit_sha') or '')
            or summary['base_ref'] != str(promotion.get('base_branch') or 'main')
        ):
            return {'success': False, 'error': 'created_pr_identity_mismatch', 'pull_request': summary}

        updated = dict(promotion)
        updated.update({
            'status': 'pull_request_created',
            'pull_request_created': True,
            'github_write_performed': bool(created_by_this_call),
            'pull_request_number': summary.get('number'),
            'pull_request_url': summary.get('html_url'),
            'pull_request_head_sha': summary.get('head_sha'),
            'pull_request_base_branch': summary.get('base_ref'),
            'pull_request_created_at': _iso(self.now_fn()),
            'pr_verified_after_unknown_outcome': bool(verified_after_unknown),
            'automatic_merge_performed': False,
            'direct_main_write_performed': False,
            'production_deployment_performed': False,
            'unknown_side_effect_retry_performed': False,
        })
        if not self._post_memory(updated, importance=10):
            return {'success': False, 'error': 'pull_request_result_not_persisted', 'promotion': updated}
        if created_by_this_call:
            with self._lock:
                self._prs_created_this_process += 1
        return {'success': True, 'promotion': updated, 'pull_request': summary}

    def _verify_after_unknown_outcome(self, promotion):
        try:
            existing = self._find_existing_open_pr(promotion)
        except Exception:
            existing = None
        if existing:
            return self._persist_pr_result(
                promotion,
                existing,
                created_by_this_call=True,
                verified_after_unknown=True,
            )
        return {
            'success': False,
            'error': 'github_pr_outcome_unknown',
            'retry_blocked': True,
            'promotion': promotion,
        }

    def execute(self, promotion_id):
        promotion = self.promotion(promotion_id)
        if not promotion:
            return {'success': False, 'error': 'promotion_not_found'}
        if str(promotion.get('status') or '') == 'pull_request_created':
            return {'success': True, 'promotion': promotion, 'existing': True}
        if str(promotion.get('status') or '') != 'approved' or not promotion.get('approval_granted'):
            return {'success': False, 'error': 'promotion_not_approved', 'promotion': promotion}

        expires_at = _parse_iso(promotion.get('approval_expires_at'))
        if not expires_at or self.now_fn() > expires_at:
            return {'success': False, 'error': 'promotion_approval_expired', 'promotion': promotion}

        review, error = self._fresh_ready_review(promotion.get('execution_id'))
        if error:
            return {'success': False, 'error': f'fresh_review_failed:{error}', 'review': review}
        if not self._same_identity(promotion, review):
            return {'success': False, 'error': 'review_identity_drift'}

        if not self.github_token_present():
            return {'success': False, 'error': 'github_token_not_configured'}

        try:
            existing = self._find_existing_open_pr(promotion)
        except Exception as exc:
            return {'success': False, 'error': _safe_text(exc, 160)}
        if existing:
            return self._persist_pr_result(promotion, existing, created_by_this_call=False)

        title = f"Tyler maintenance {promotion.get('execution_id')} — approved proposal"
        body = (
            'Tyler AI human-gated maintenance promotion.\n\n'
            f"- Execution: `{promotion.get('execution_id')}`\n"
            f"- Review: `{promotion.get('review_id')}`\n"
            f"- Promotion: `{promotion.get('promotion_id')}`\n"
            f"- Exact reviewed commit: `{promotion.get('proposal_commit_sha')}`\n"
            f"- Approved base commit: `{promotion.get('base_commit_sha')}`\n\n"
            'The v2.15 automated review gate was re-run immediately before PR creation and returned READY. '
            'This PR creation does not merge the branch and does not deploy production. '
            'Any future merge step must revalidate the exact head commit and current base again.'
        )
        payload = {
            'title': title,
            'head': str(promotion.get('review_branch') or ''),
            'base': str(promotion.get('base_branch') or 'main'),
            'body': body,
            'draft': False,
            'maintainer_can_modify': False,
        }

        try:
            response = self._github_request('POST', '/pulls', json=payload)
        except requests.Timeout:
            return self._verify_after_unknown_outcome(promotion)
        except requests.RequestException:
            return self._verify_after_unknown_outcome(promotion)

        if response.status_code == 201:
            try:
                pr = response.json()
            except Exception:
                return self._verify_after_unknown_outcome(promotion)
            return self._persist_pr_result(promotion, pr, created_by_this_call=True)

        if response.status_code == 403:
            return {
                'success': False,
                'error': 'github_pull_request_permission_denied',
                'detail': 'Pull Requests write permission is required for GITHUB_MAINTENANCE_TOKEN.',
            }

        if response.status_code == 422:
            try:
                existing = self._find_existing_open_pr(promotion)
            except Exception:
                existing = None
            if existing:
                return self._persist_pr_result(promotion, existing, created_by_this_call=False)
            return {'success': False, 'error': 'github_pull_request_unprocessable'}

        return {
            'success': False,
            'error': f'github_pull_request_http_{response.status_code}',
            'detail': _safe_text(getattr(response, 'text', ''), 180),
        }
