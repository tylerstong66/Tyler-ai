import ast
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests


MAINTENANCE_EXECUTION_CATEGORY = 'maintenance_execution'
MAINTENANCE_EXECUTION_SCHEMA = 'tyler_maintenance_execution_v1'
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_APPROVAL_TTL_MINUTES = 30
MAX_CHANGES = 8
MAX_FIND_CHARS = 40000
MAX_REPLACE_CHARS = 80000
MAX_CONTEXT_CHARS = 18000

_SECRET_PATTERNS = [
    re.compile(r'(?i)\bgh[pousr]_[A-Za-z0-9]{20,}\b'),
    re.compile(r'(?i)\bsk-[A-Za-z0-9_-]{20,}\b'),
    re.compile(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{24,}\b'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
]


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


def _sha256_text(text):
    return hashlib.sha256(str(text).encode('utf-8')).hexdigest()


def execution_id_for(plan_id):
    digest = hashlib.sha256(str(plan_id or '').upper().encode('utf-8')).hexdigest()[:10].upper()
    return f'EXE-{digest}'


def _contains_secret_literal(text):
    value = str(text or '')
    return any(pattern.search(value) for pattern in _SECRET_PATTERNS)


def _parse_json_object(value):
    if isinstance(value, dict):
        return value
    text = str(value or '').strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)
        text = re.sub(r'\s*```$', '', text)
    start = text.find('{')
    end = text.rfind('}')
    if start < 0 or end < start:
        raise ValueError('patch_generator_did_not_return_json')
    parsed = json.loads(text[start:end + 1])
    if not isinstance(parsed, dict):
        raise ValueError('patch_generator_json_not_object')
    return parsed


def _function_excerpt(path, names, max_chars=5000):
    try:
        text = Path(path).read_text(encoding='utf-8', errors='replace')
        tree = ast.parse(text, filename=str(path))
    except Exception:
        return ''
    lines = text.splitlines(keepends=True)
    wanted = set(str(name or '').split('.')[-1] for name in (names or []))
    chunks = []
    for node in tree.body:
        candidates = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            candidates.append(node)
        elif isinstance(node, ast.ClassDef):
            candidates.extend(
                child for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
        for child in candidates:
            if wanted and child.name not in wanted:
                continue
            start = max(1, int(getattr(child, 'lineno', 1)) - 3)
            end = min(len(lines), int(getattr(child, 'end_lineno', start)) + 3)
            chunks.append(''.join(lines[start - 1:end]))
    if not chunks:
        return text[:max_chars]
    return '\n\n'.join(chunks)[:max_chars]


class MaintenanceExecutionCoordinator:
    def __init__(
        self,
        plan_loader,
        safe_source_files_fn,
        patch_generator_fn,
        supabase_url_fn,
        headers_fn,
        version_fn,
        source_root=None,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        approval_ttl_minutes=DEFAULT_APPROVAL_TTL_MINUTES,
        now_fn=None,
        github_token_fn=None,
        github_repository_fn=None,
        github_base_branch_fn=None,
    ):
        self.plan_loader = plan_loader
        self.safe_source_files_fn = safe_source_files_fn
        self.patch_generator_fn = patch_generator_fn
        self.supabase_url_fn = supabase_url_fn
        self.headers_fn = headers_fn
        self.version_fn = version_fn
        self.source_root = Path(source_root or Path(__file__).resolve().parent)
        self.timeout_seconds = max(3, min(int(timeout_seconds), 30))
        self.approval_ttl_minutes = max(5, min(int(approval_ttl_minutes), 120))
        self.now_fn = now_fn or _utcnow
        self.github_token_fn = github_token_fn or (lambda: os.environ.get('GITHUB_MAINTENANCE_TOKEN', ''))
        self.github_repository_fn = github_repository_fn or (
            lambda: os.environ.get('GITHUB_MAINTENANCE_REPOSITORY', 'tylerstong66/Tyler-ai')
        )
        self.github_base_branch_fn = github_base_branch_fn or (
            lambda: os.environ.get('GITHUB_MAINTENANCE_BASE_BRANCH', 'main')
        )
        self._lock = threading.RLock()
        self._prepared_this_process = 0
        self._approved_this_process = 0
        self._published_this_process = 0
        self._last_error_category = None

    def persistence_configured(self):
        try:
            return bool(self.supabase_url_fn() and self.headers_fn())
        except Exception:
            return False

    def github_configured(self):
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
                'github_write_configured': self.github_configured(),
                'prepared_this_process': int(self._prepared_this_process),
                'approved_this_process': int(self._approved_this_process),
                'published_this_process': int(self._published_this_process),
                'last_error_category': self._last_error_category,
                'automatic_patch_generation_enabled': False,
                'automatic_github_writes_enabled': False,
                'automatic_production_deployment_enabled': False,
                'approval_required_before_github_write': True,
                'separate_execute_command_required_after_approval': True,
                'writes_to_main_branch_directly': False,
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
                    'category': MAINTENANCE_EXECUTION_CATEGORY,
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
                    'category': f'eq.{MAINTENANCE_EXECUTION_CATEGORY}',
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
            execution_id = str(item.get('execution_id') or '').upper()
            if execution_id and execution_id not in latest:
                latest[execution_id] = item
        return list(latest.values())[:max(1, min(int(limit), 50))]

    def execution(self, execution_id):
        target = str(execution_id or '').strip().upper()
        for item in self.recent(limit=50):
            if str(item.get('execution_id') or '').upper() == target:
                return item
        return None

    def _affected_files(self, plan):
        safe = set(self.safe_source_files_fn() or [])
        files = []
        for item in list((plan or {}).get('affected_code') or []):
            name = str(item.get('file') or '').strip()
            if not name or name not in safe:
                continue
            path = self.source_root / name
            try:
                path.resolve().relative_to(self.source_root.resolve())
            except Exception:
                continue
            if path.is_file() and name.endswith('.py'):
                files.append((name, list(item.get('functions') or [])))
        unique = []
        seen = set()
        for name, functions in files:
            if name in seen:
                continue
            seen.add(name)
            unique.append((name, functions))
        return unique[:6]

    def _source_manifest(self, plan):
        manifest = []
        for name, functions in self._affected_files(plan):
            text = (self.source_root / name).read_text(encoding='utf-8', errors='replace')
            try:
                ast.parse(text, filename=name)
                syntax_valid = True
            except Exception:
                syntax_valid = False
            manifest.append({
                'path': name,
                'sha256': _sha256_text(text),
                'size_bytes': len(text.encode('utf-8')),
                'syntax_valid': syntax_valid,
                'functions': functions[:12],
            })
        return manifest

    def _source_context(self, plan):
        parts = []
        used = 0
        for name, functions in self._affected_files(plan):
            excerpt = _function_excerpt(self.source_root / name, functions, max_chars=5500)
            if not excerpt:
                continue
            block = f'FILE: {name}\n{excerpt}'
            remaining = MAX_CONTEXT_CHARS - used
            if remaining <= 0:
                break
            block = block[:remaining]
            parts.append(block)
            used += len(block)
        return '\n\n'.join(parts)

    def _validate_patch_spec(self, plan, manifest, raw_patch):
        payload = _parse_json_object(raw_patch)
        changes = payload.get('changes')
        if not isinstance(changes, list) or not changes:
            raise ValueError('patch_has_no_changes')
        if len(changes) > MAX_CHANGES:
            raise ValueError('patch_has_too_many_changes')

        allowed = {item['path']: item for item in manifest}
        if not allowed:
            raise ValueError('no_verified_affected_source')

        working = {}
        original = {}
        for path in allowed:
            text = (self.source_root / path).read_text(encoding='utf-8', errors='replace')
            working[path] = text
            original[path] = text

        normalized = []
        for index, change in enumerate(changes):
            if not isinstance(change, dict):
                raise ValueError(f'patch_change_{index}_not_object')
            path = str(change.get('path') or '').strip()
            find = str(change.get('find') or '')
            replace = str(change.get('replace') or '')
            reason = _safe_text(change.get('reason'), 240)
            if path not in allowed:
                raise ValueError('patch_path_not_allowed')
            if not find or len(find) > MAX_FIND_CHARS or len(replace) > MAX_REPLACE_CHARS:
                raise ValueError('patch_change_size_invalid')
            if _contains_secret_literal(replace):
                raise ValueError('patch_contains_secret_literal')
            count = working[path].count(find)
            if count != 1:
                raise ValueError('patch_find_must_match_exactly_once')
            working[path] = working[path].replace(find, replace, 1)
            normalized.append({
                'path': path,
                'find': find,
                'replace': replace,
                'reason': reason,
            })

        changed_files = []
        for path, final_text in working.items():
            if final_text == original[path]:
                continue
            try:
                ast.parse(final_text, filename=path)
            except Exception as exc:
                raise ValueError(f'patch_syntax_invalid:{path}:{type(exc).__name__}')
            changed_files.append({
                'path': path,
                'original_sha256': allowed[path]['sha256'],
                'proposed_sha256': _sha256_text(final_text),
                'size_bytes': len(final_text.encode('utf-8')),
            })

        if not changed_files:
            raise ValueError('patch_does_not_change_source')

        summary = _safe_text(payload.get('summary'), 600)
        return {
            'summary': summary or 'Source-grounded maintenance patch prepared.',
            'changes': normalized,
            'changed_files': changed_files,
        }

    def _rebuild_patch(self, package):
        manifest = list(package.get('source_manifest') or [])
        manifest_by_path = {item.get('path'): item for item in manifest if item.get('path')}
        patch_spec = dict(package.get('patch_spec') or {})
        changes = list(patch_spec.get('changes') or [])
        working = {}
        for path, item in manifest_by_path.items():
            full_path = self.source_root / path
            if not full_path.is_file():
                raise ValueError('local_source_missing')
            text = full_path.read_text(encoding='utf-8', errors='replace')
            if _sha256_text(text) != item.get('sha256'):
                raise ValueError('local_source_drift')
            working[path] = text
        for change in changes:
            path = str(change.get('path') or '')
            find = str(change.get('find') or '')
            replace = str(change.get('replace') or '')
            if path not in working or working[path].count(find) != 1:
                raise ValueError('patch_no_longer_applies_cleanly')
            working[path] = working[path].replace(find, replace, 1)
        output = {}
        changed_meta = {item.get('path'): item for item in patch_spec.get('changed_files') or []}
        for path, text in working.items():
            if path not in changed_meta:
                continue
            if _sha256_text(text) != changed_meta[path].get('proposed_sha256'):
                raise ValueError('proposed_hash_mismatch')
            ast.parse(text, filename=path)
            output[path] = text
        if not output:
            raise ValueError('no_changed_files_after_rebuild')
        return output

    def prepare(self, plan_id, persist=True):
        plan = self.plan_loader(str(plan_id or '').upper())
        if not plan:
            return {'success': False, 'error': 'maintenance_plan_not_found'}
        if plan.get('simulation'):
            return {'success': False, 'error': 'simulation_plan_not_executable'}
        if str(plan.get('kind') or '') == 'unknown_external_outcome':
            return {'success': False, 'error': 'outcome_verification_required_before_patch'}
        if not plan.get('source_grounded'):
            return {'success': False, 'error': 'maintenance_plan_not_source_grounded'}

        plan_id = str(plan.get('maintenance_plan_id') or plan_id or '').upper()
        execution_id = execution_id_for(plan_id)
        existing = self.execution(execution_id) if persist else None
        if existing and str(existing.get('status') or '') not in {'cancelled', 'expired'}:
            return {'success': True, 'package': existing, 'saved': True, 'existing': True}

        manifest = self._source_manifest(plan)
        if not manifest or not all(item.get('syntax_valid') for item in manifest):
            return {'success': False, 'error': 'verified_source_not_ready'}
        source_context = self._source_context(plan)
        if not source_context:
            return {'success': False, 'error': 'source_context_unavailable'}

        try:
            generated = self.patch_generator_fn(plan, source_context, execution_id)
            patch_spec = self._validate_patch_spec(plan, manifest, generated)
        except Exception as exc:
            self._last_error_category = _safe_text(type(exc).__name__ + ':' + str(exc), 160)
            return {'success': False, 'error': 'patch_generation_or_validation_failed', 'detail': self._last_error_category}

        now = self.now_fn()
        package = {
            'schema': MAINTENANCE_EXECUTION_SCHEMA,
            'execution_id': execution_id,
            'maintenance_plan_id': plan_id,
            'incident_id': str(plan.get('incident_id') or '').upper(),
            'service': plan.get('service'),
            'severity': plan.get('severity'),
            'kind': plan.get('kind'),
            'version': str(self.version_fn() or ''),
            'prepared_at': _iso(now),
            'status': 'awaiting_approval',
            'source_grounded': True,
            'source_manifest': manifest,
            'source_fingerprint': _sha256_text(json.dumps(manifest, sort_keys=True)),
            'patch_spec': patch_spec,
            'test_plan': list(plan.get('test_plan') or []),
            'rollback_plan': list(plan.get('rollback_plan') or []),
            'deployment_plan': list(plan.get('deployment_plan') or []),
            'approval_required': True,
            'approval_code': secrets.token_hex(3).upper(),
            'approval_granted': False,
            'approval_expires_at': None,
            'github_publish_performed': False,
            'production_deployment_performed': False,
            'configuration_change_performed': False,
            'external_side_effect_retry_performed': False,
            'target': {
                'repository': str(self.github_repository_fn() or ''),
                'base_branch': str(self.github_base_branch_fn() or 'main'),
                'publish_mode': 'new_review_branch_only',
                'direct_main_write': False,
                'pull_request_created_automatically': False,
            },
        }
        saved = self._post_memory(package, importance=9) if persist else False
        if persist and not saved:
            return {'success': False, 'error': 'execution_package_not_persisted', 'package': package, 'saved': False}
        with self._lock:
            self._prepared_this_process += 1
        self._last_error_category = None
        return {'success': True, 'package': package, 'saved': bool(saved), 'existing': False}

    def approve(self, execution_id, approval_code):
        package = self.execution(execution_id)
        if not package:
            return {'success': False, 'error': 'execution_not_found'}
        if str(package.get('status') or '') != 'awaiting_approval':
            return {'success': False, 'error': 'execution_not_awaiting_approval', 'package': package}
        expected = str(package.get('approval_code') or '')
        supplied = str(approval_code or '').strip().upper()
        if not expected or not hmac.compare_digest(expected, supplied):
            return {'success': False, 'error': 'approval_code_invalid'}

        try:
            self._rebuild_patch(package)
        except Exception as exc:
            return {'success': False, 'error': 'source_or_patch_drift', 'detail': _safe_text(exc, 120)}

        now = self.now_fn()
        updated = dict(package)
        updated.update({
            'status': 'approved',
            'approval_granted': True,
            'approved_at': _iso(now),
            'approval_expires_at': _iso(now + timedelta(minutes=self.approval_ttl_minutes)),
        })
        if not self._post_memory(updated, importance=10):
            return {'success': False, 'error': 'approval_not_durably_persisted'}
        with self._lock:
            self._approved_this_process += 1
        return {'success': True, 'package': updated}

    def cancel(self, execution_id):
        package = self.execution(execution_id)
        if not package:
            return {'success': False, 'error': 'execution_not_found'}
        if str(package.get('status') or '') in {'published_for_review', 'cancelled'}:
            return {'success': False, 'error': 'execution_not_cancellable', 'package': package}
        updated = dict(package)
        updated.update({
            'status': 'cancelled',
            'approval_granted': False,
            'cancelled_at': _iso(self.now_fn()),
        })
        if not self._post_memory(updated, importance=8):
            return {'success': False, 'error': 'cancellation_not_persisted'}
        return {'success': True, 'package': updated}

    def _github_headers(self):
        return {
            'Authorization': f'Bearer {str(self.github_token_fn()).strip()}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }

    def _github_request(self, method, path, **kwargs):
        repo = str(self.github_repository_fn() or '').strip()
        url = f'https://api.github.com/repos/{repo}{path}'
        return requests.request(
            method,
            url,
            headers=self._github_headers(),
            timeout=self.timeout_seconds,
            **kwargs,
        )

    def _publish_atomic_review_branch(self, package, final_files):
        if not self.github_configured():
            raise RuntimeError('github_write_not_configured')
        repo = str(self.github_repository_fn() or '').strip()
        base_branch = str(self.github_base_branch_fn() or 'main').strip()
        execution_id = str(package.get('execution_id') or '').upper()
        branch = f'tyler-maintenance/{execution_id.lower()}'

        ref = self._github_request('GET', f'/git/ref/heads/{quote(base_branch, safe="")}')
        if not ref.ok:
            raise RuntimeError(f'github_base_ref_http_{ref.status_code}')
        base_commit_sha = str((ref.json().get('object') or {}).get('sha') or '')
        if not base_commit_sha:
            raise RuntimeError('github_base_commit_missing')

        commit = self._github_request('GET', f'/git/commits/{base_commit_sha}')
        if not commit.ok:
            raise RuntimeError(f'github_base_commit_http_{commit.status_code}')
        base_tree_sha = str((commit.json().get('tree') or {}).get('sha') or '')
        if not base_tree_sha:
            raise RuntimeError('github_base_tree_missing')

        manifest = {item.get('path'): item for item in package.get('source_manifest') or []}
        for path in final_files:
            content_response = self._github_request(
                'GET',
                f'/contents/{quote(path, safe="/")}',
                params={'ref': base_commit_sha},
            )
            if not content_response.ok:
                raise RuntimeError(f'github_source_http_{content_response.status_code}')
            encoded = str(content_response.json().get('content') or '').replace('\n', '')
            try:
                remote_text = base64.b64decode(encoded).decode('utf-8')
            except Exception as exc:
                raise RuntimeError('github_source_decode_failed') from exc
            if _sha256_text(remote_text) != str((manifest.get(path) or {}).get('sha256') or ''):
                raise RuntimeError('github_source_drift')

        tree_entries = []
        for path, text in final_files.items():
            blob = self._github_request(
                'POST',
                '/git/blobs',
                json={'content': text, 'encoding': 'utf-8'},
            )
            if not blob.ok:
                raise RuntimeError(f'github_blob_http_{blob.status_code}')
            blob_sha = str(blob.json().get('sha') or '')
            if not blob_sha:
                raise RuntimeError('github_blob_sha_missing')
            tree_entries.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': blob_sha})

        tree = self._github_request(
            'POST',
            '/git/trees',
            json={'base_tree': base_tree_sha, 'tree': tree_entries},
        )
        if not tree.ok:
            raise RuntimeError(f'github_tree_http_{tree.status_code}')
        tree_sha = str(tree.json().get('sha') or '')
        if not tree_sha:
            raise RuntimeError('github_tree_sha_missing')

        new_commit = self._github_request(
            'POST',
            '/git/commits',
            json={
                'message': f'Tyler AI maintenance proposal {execution_id}',
                'tree': tree_sha,
                'parents': [base_commit_sha],
            },
        )
        if not new_commit.ok:
            raise RuntimeError(f'github_commit_http_{new_commit.status_code}')
        proposal_commit_sha = str(new_commit.json().get('sha') or '')
        if not proposal_commit_sha:
            raise RuntimeError('github_proposal_commit_missing')

        new_ref = self._github_request(
            'POST',
            '/git/refs',
            json={'ref': f'refs/heads/{branch}', 'sha': proposal_commit_sha},
        )
        if not new_ref.ok:
            if new_ref.status_code == 422:
                raise RuntimeError('github_review_branch_already_exists')
            raise RuntimeError(f'github_ref_http_{new_ref.status_code}')

        return {
            'repository': repo,
            'base_branch': base_branch,
            'branch': branch,
            'base_commit_sha': base_commit_sha,
            'proposal_commit_sha': proposal_commit_sha,
            'pull_request_created': False,
            'production_branch_changed': False,
        }

    def execute_approved(self, execution_id):
        package = self.execution(execution_id)
        if not package:
            return {'success': False, 'error': 'execution_not_found'}
        if str(package.get('status') or '') != 'approved' or not package.get('approval_granted'):
            return {'success': False, 'error': 'execution_not_approved', 'package': package}

        expires = str(package.get('approval_expires_at') or '')
        try:
            expiry = datetime.fromisoformat(expires.replace('Z', '+00:00'))
        except Exception:
            expiry = None
        if not expiry or self.now_fn() > expiry:
            expired = dict(package)
            expired.update({'status': 'expired', 'approval_granted': False})
            self._post_memory(expired, importance=9)
            return {'success': False, 'error': 'approval_expired', 'package': expired}

        try:
            final_files = self._rebuild_patch(package)
        except Exception as exc:
            return {'success': False, 'error': 'source_or_patch_drift', 'detail': _safe_text(exc, 120)}

        if not self.github_configured():
            return {'success': False, 'error': 'github_write_not_configured', 'package': package}

        try:
            publish = self._publish_atomic_review_branch(package, final_files)
        except Exception as exc:
            category = _safe_text(exc, 140)
            failed = dict(package)
            failed.update({
                'status': 'publish_failed',
                'last_publish_error_category': category,
                'github_publish_performed': False,
                'production_deployment_performed': False,
            })
            self._post_memory(failed, importance=9)
            return {'success': False, 'error': 'github_publish_failed', 'detail': category, 'package': failed}

        updated = dict(package)
        updated.update({
            'status': 'published_for_review',
            'published_at': _iso(self.now_fn()),
            'github_publish_performed': True,
            'github_publish': publish,
            'production_deployment_performed': False,
            'configuration_change_performed': False,
            'external_side_effect_retry_performed': False,
        })
        persisted = self._post_memory(updated, importance=10)
        with self._lock:
            self._published_this_process += 1
        return {
            'success': True,
            'package': updated,
            'saved': bool(persisted),
            'persistence_warning': None if persisted else 'review_branch_created_but_state_persistence_failed',
        }
