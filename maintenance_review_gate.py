import base64
import hashlib
import json
import os
import re
import threading
from datetime import datetime, timezone
from urllib.parse import quote

import requests


MAINTENANCE_REVIEW_CATEGORY = 'maintenance_review_gate'
MAINTENANCE_REVIEW_SCHEMA = 'tyler_maintenance_review_v1'
DEFAULT_TIMEOUT_SECONDS = 10
REVIEW_WORKFLOW_PATH = '.github/workflows/v2_15_review_gate.yml'
REVIEW_WORKFLOW_NAME = 'Tyler AI v2.15 review gate'

_SECRET_PATTERNS = [
    re.compile(r'(?i)\bgh[pousr]_[A-Za-z0-9]{20,}\b'),
    re.compile(r'(?i)\bsk-[A-Za-z0-9_-]{20,}\b'),
    re.compile(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{24,}\b'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
]


def _utcnow():
    return datetime.now(timezone.utc)


def _safe_text(value, limit=500):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    text = re.sub(
        r'(?i)\b(api[_-]?key|token|password|secret|authorization)\s*[:=]\s*[^,;|]+',
        r'\1=<redacted>',
        text,
    )
    text = re.sub(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+', 'Bearer <redacted>', text)
    return text[:limit]


def review_id_for(execution_id, proposal_commit_sha):
    raw = f"{str(execution_id or '').upper()}:{str(proposal_commit_sha or '').lower()}"
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:10].upper()
    return f'REV-{digest}'


def _contains_secret_literal(text):
    value = str(text or '')
    return any(pattern.search(value) for pattern in _SECRET_PATTERNS)


class MaintenanceReviewGate:
    """Read-only review gate for approved maintenance proposal branches.

    This class never creates, updates, deletes, merges, or deploys anything.
    It verifies provenance, exact diff scope, source safety, and dedicated CI.
    """

    def __init__(
        self,
        execution_loader,
        supabase_url_fn,
        headers_fn,
        version_fn,
        github_token_fn=None,
        github_repository_fn=None,
        github_base_branch_fn=None,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        now_fn=None,
    ):
        self.execution_loader = execution_loader
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
        self.now_fn = now_fn or _utcnow
        self._lock = threading.RLock()
        self._reviews_this_process = 0
        self._last_error_category = None

    def persistence_configured(self):
        try:
            return bool(self.supabase_url_fn() and self.headers_fn())
        except Exception:
            return False

    def github_read_configured(self):
        try:
            repo = str(self.github_repository_fn() or '').strip()
            return bool(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo))
        except Exception:
            return False

    def status(self):
        with self._lock:
            return {
                'persistence_configured': self.persistence_configured(),
                'github_read_configured': self.github_read_configured(),
                'reviews_this_process': int(self._reviews_this_process),
                'last_error_category': self._last_error_category,
                'automatic_merge_enabled': False,
                'automatic_pull_request_creation_enabled': False,
                'automatic_production_deployment_enabled': False,
                'automatic_branch_mutation_enabled': False,
                'review_requires_ci_success': True,
                'review_requires_exact_diff_scope': True,
                'review_requires_current_base': True,
            }

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
                    'category': MAINTENANCE_REVIEW_CATEGORY,
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
                    'category': f'eq.{MAINTENANCE_REVIEW_CATEGORY}',
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
        for item in self._load_rows(limit=max(20, int(limit) * 4)):
            key = str(item.get('review_id') or '')
            if key and key not in latest:
                latest[key] = item
        return list(latest.values())[:max(1, min(int(limit), 50))]

    def _github_headers(self, authenticated=True):
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }
        token = str(self.github_token_fn() or '').strip()
        if authenticated and token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    def _github_get(self, path, params=None, allow_public_fallback=False):
        repo = str(self.github_repository_fn() or '').strip()
        url = f'https://api.github.com/repos/{repo}{path}'
        response = requests.get(
            url,
            headers=self._github_headers(authenticated=True),
            params=params,
            timeout=self.timeout_seconds,
        )
        if allow_public_fallback and response.status_code in {401, 403, 404}:
            response = requests.get(
                url,
                headers=self._github_headers(authenticated=False),
                params=params,
                timeout=self.timeout_seconds,
            )
        return response

    def _json_or_raise(self, response, category):
        if not response.ok:
            raise RuntimeError(f'{category}_http_{response.status_code}')
        try:
            return response.json()
        except Exception as exc:
            raise RuntimeError(f'{category}_invalid_json') from exc

    def _fetch_ref_sha(self, branch):
        response = self._github_get(f'/git/ref/heads/{quote(str(branch), safe="")}')
        data = self._json_or_raise(response, 'github_ref')
        sha = str((data.get('object') or {}).get('sha') or '')
        if not sha:
            raise RuntimeError('github_ref_sha_missing')
        return sha

    def _fetch_commit(self, sha):
        response = self._github_get(f'/git/commits/{quote(str(sha), safe="")}')
        return self._json_or_raise(response, 'github_commit')

    def _compare(self, base_sha, head_sha):
        response = self._github_get(
            f'/compare/{quote(str(base_sha), safe="")}...{quote(str(head_sha), safe="")}'
        )
        return self._json_or_raise(response, 'github_compare')

    def _fetch_text(self, path, ref):
        response = self._github_get(
            f'/contents/{quote(str(path), safe="/")}',
            params={'ref': ref},
        )
        data = self._json_or_raise(response, 'github_content')
        encoded = str(data.get('content') or '').replace('\n', '')
        if not encoded:
            raise RuntimeError('github_content_missing')
        try:
            return base64.b64decode(encoded).decode('utf-8')
        except Exception as exc:
            raise RuntimeError('github_content_decode_failed') from exc

    def _ci_status(self, proposal_sha, branch):
        response = self._github_get(
            '/actions/runs',
            params={'head_sha': proposal_sha, 'per_page': 100},
            allow_public_fallback=True,
        )
        data = self._json_or_raise(response, 'github_actions')
        candidates = []
        for run in data.get('workflow_runs') or []:
            path = str(run.get('path') or '')
            name = str(run.get('name') or '')
            head_sha = str(run.get('head_sha') or '')
            head_branch = str(run.get('head_branch') or '')
            if head_sha != proposal_sha:
                continue
            if head_branch and head_branch != branch:
                continue
            if path == REVIEW_WORKFLOW_PATH or name == REVIEW_WORKFLOW_NAME:
                candidates.append(run)
        if not candidates:
            return {
                'state': 'pending',
                'reason': 'review_ci_not_observed_yet',
                'workflow': REVIEW_WORKFLOW_NAME,
                'run_id': None,
            }
        candidates.sort(key=lambda item: str(item.get('created_at') or ''), reverse=True)
        run = candidates[0]
        status = str(run.get('status') or '').lower()
        conclusion = str(run.get('conclusion') or '').lower()
        if status != 'completed':
            return {
                'state': 'pending',
                'reason': f'review_ci_{status or "running"}',
                'workflow': name or REVIEW_WORKFLOW_NAME,
                'run_id': run.get('id'),
                'html_url': run.get('html_url'),
            }
        if conclusion == 'success':
            return {
                'state': 'success',
                'reason': 'review_ci_passed',
                'workflow': name or REVIEW_WORKFLOW_NAME,
                'run_id': run.get('id'),
                'html_url': run.get('html_url'),
            }
        return {
            'state': 'failure',
            'reason': f'review_ci_{conclusion or "failed"}',
            'workflow': name or REVIEW_WORKFLOW_NAME,
            'run_id': run.get('id'),
            'html_url': run.get('html_url'),
        }

    def review(self, execution_id, persist=True):
        package = self.execution_loader(str(execution_id or '').upper())
        if not package:
            return {'success': False, 'error': 'execution_not_found'}
        if str(package.get('status') or '') != 'published_for_review':
            return {'success': False, 'error': 'execution_not_published_for_review', 'package': package}

        publish = dict(package.get('github_publish') or {})
        target = dict(package.get('target') or {})
        patch = dict(package.get('patch_spec') or {})
        execution_id = str(package.get('execution_id') or '').upper()
        repository = str(publish.get('repository') or target.get('repository') or '')
        base_branch = str(publish.get('base_branch') or target.get('base_branch') or 'main')
        branch = str(publish.get('branch') or '')
        base_commit_sha = str(publish.get('base_commit_sha') or '')
        proposal_sha = str(publish.get('proposal_commit_sha') or '')
        expected_files = sorted(
            str(item.get('path') or '')
            for item in (patch.get('changed_files') or [])
            if str(item.get('path') or '').strip()
        )

        review = {
            'schema': MAINTENANCE_REVIEW_SCHEMA,
            'review_id': review_id_for(execution_id, proposal_sha),
            'execution_id': execution_id,
            'maintenance_plan_id': package.get('maintenance_plan_id'),
            'incident_id': package.get('incident_id'),
            'repository': repository,
            'base_branch': base_branch,
            'review_branch': branch,
            'base_commit_sha': base_commit_sha,
            'proposal_commit_sha': proposal_sha,
            'expected_files': expected_files,
            'gate_status': 'not_ready',
            'reviewed_at': self.now_fn().isoformat(),
            'version': str(self.version_fn() or ''),
            'automatic_merge_performed': False,
            'pull_request_created': False,
            'production_deployment_performed': False,
            'branch_mutation_performed': False,
            'checks': {},
            'reasons': [],
        }
        reasons = review['reasons']
        checks = review['checks']

        configured_repo = str(self.github_repository_fn() or '').strip()
        configured_base = str(self.github_base_branch_fn() or 'main').strip()
        safe_branch = f'tyler-maintenance/{execution_id.lower()}'
        checks['repository_matches'] = repository == configured_repo
        checks['base_branch_matches'] = base_branch == configured_base == 'main'
        checks['safe_review_branch'] = branch == safe_branch
        checks['proposal_identity_present'] = bool(base_commit_sha and proposal_sha)
        checks['expected_files_present'] = bool(expected_files)
        checks['package_reports_no_production_change'] = not bool(
            publish.get('production_branch_changed')
            or package.get('production_deployment_performed')
            or package.get('configuration_change_performed')
            or package.get('external_side_effect_retry_performed')
        )
        for name, ok in list(checks.items()):
            if not ok:
                reasons.append(name)

        if reasons:
            if persist:
                review['saved'] = bool(self._post_memory(review, importance=9))
            return {'success': True, 'review': review}

        try:
            branch_sha = self._fetch_ref_sha(branch)
            main_sha = self._fetch_ref_sha(base_branch)
            commit = self._fetch_commit(proposal_sha)
            parents = [str(item.get('sha') or '') for item in (commit.get('parents') or [])]
            compare = self._compare(base_commit_sha, proposal_sha)
        except Exception as exc:
            reasons.append(_safe_text(exc, 140))
            review['checks']['github_provenance_readable'] = False
            if persist:
                review['saved'] = bool(self._post_memory(review, importance=9))
            return {'success': True, 'review': review}

        checks['github_provenance_readable'] = True
        checks['branch_points_to_proposal'] = branch_sha == proposal_sha
        checks['proposal_parent_matches_base'] = bool(parents and parents[0] == base_commit_sha)
        checks['main_still_at_review_base'] = main_sha == base_commit_sha
        checks['single_commit_proposal'] = int(compare.get('ahead_by') or 0) == 1 and int(compare.get('behind_by') or 0) == 0

        changed_files = []
        statuses = {}
        for item in compare.get('files') or []:
            name = str(item.get('filename') or '')
            if name:
                changed_files.append(name)
                statuses[name] = str(item.get('status') or '')
        changed_files = sorted(changed_files)
        review['changed_files'] = changed_files
        review['file_statuses'] = statuses
        checks['exact_diff_scope'] = changed_files == expected_files
        checks['only_existing_files_modified'] = bool(changed_files) and all(
            statuses.get(name) == 'modified' for name in changed_files
        )

        for name in [
            'branch_points_to_proposal',
            'proposal_parent_matches_base',
            'main_still_at_review_base',
            'single_commit_proposal',
            'exact_diff_scope',
            'only_existing_files_modified',
        ]:
            if not checks.get(name):
                reasons.append(name)

        source_risks = []
        if not reasons:
            for path in changed_files:
                try:
                    text = self._fetch_text(path, proposal_sha)
                except Exception as exc:
                    source_risks.append(f'{path}:unreadable:{_safe_text(exc, 80)}')
                    continue
                if len(text) > 300000:
                    source_risks.append(f'{path}:file_too_large')
                if _contains_secret_literal(text):
                    source_risks.append(f'{path}:secret_like_literal')
        review['source_risks'] = source_risks
        checks['source_safety_scan_passed'] = not source_risks
        if source_risks:
            reasons.append('source_safety_scan_failed')

        ci = {'state': 'not_checked', 'reason': 'structural_checks_failed'}
        if not reasons:
            try:
                ci = self._ci_status(proposal_sha, branch)
            except Exception as exc:
                ci = {
                    'state': 'pending',
                    'reason': f'ci_status_unavailable:{_safe_text(exc, 100)}',
                    'workflow': REVIEW_WORKFLOW_NAME,
                    'run_id': None,
                }
        review['ci'] = ci
        checks['review_ci_passed'] = ci.get('state') == 'success'

        if reasons:
            review['gate_status'] = 'not_ready'
        elif ci.get('state') == 'success':
            review['gate_status'] = 'ready'
        elif ci.get('state') == 'failure':
            review['gate_status'] = 'not_ready'
            reasons.append(str(ci.get('reason') or 'review_ci_failed'))
        else:
            review['gate_status'] = 'pending'
            reasons.append(str(ci.get('reason') or 'review_ci_pending'))

        if persist and review['gate_status'] in {'ready', 'not_ready'}:
            review['saved'] = bool(self._post_memory(review, importance=10 if review['gate_status'] == 'ready' else 9))
        else:
            review['saved'] = False

        with self._lock:
            self._reviews_this_process += 1
        return {'success': True, 'review': review}
