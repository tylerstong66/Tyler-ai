import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import requests

import app_v2_17 as v217


v217.base.VERSION = '2.17.1-human-gated-production-promotion'
v217.base.VERSION_SHORT = 'v2.17.1'

base = v217.base
app = v217.app
ENGINE = v217.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v217.EXECUTOR
DRILL_EXECUTOR = v217.DRILL_EXECUTOR
PLANNER = v217.PLANNER
OPS = v217.OPS
REVIEW_GATE = v217.REVIEW_GATE
PROMOTION = v217.PROMOTION
MERGE_GATE = v217.MERGE_GATE
v210 = v217.v210

CATEGORY = 'maintenance_production'
WORKFLOW_PATH = 'v2_17_1_production_deploy.yml'
SERVICE_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://tyler-ai.onrender.com').rstrip('/')
TIMEOUT = max(3, min(int(os.environ.get('MAINTENANCE_PRODUCTION_TIMEOUT_SECONDS', '10')), 30))
TTL_MINUTES = max(5, min(int(os.environ.get('MAINTENANCE_PRODUCTION_APPROVAL_TTL_MINUTES', '30')), 120))
base.SPECIAL_MEMORY_CATEGORIES.add(CATEGORY)


def _now():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.isoformat() if value else None


def _parse(value):
    try:
        out = datetime.fromisoformat(str(value or '').replace('Z', '+00:00'))
        return out if out.tzinfo else out.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _sha(value):
    text = str(value or '').strip().lower()
    return text if re.fullmatch(r'[0-9a-f]{40}', text) else ''


def _deployment_id(merge_id, merge_sha):
    raw = f"{str(merge_id or '').upper()}:{_sha(merge_sha)}"
    return 'DPL-' + hashlib.sha256(raw.encode()).hexdigest()[:10].upper()


def _github_headers():
    token = str(os.environ.get('GITHUB_MAINTENANCE_TOKEN', '')).strip()
    headers = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers


def _github(method, path, **kwargs):
    repo = os.environ.get('GITHUB_MAINTENANCE_REPOSITORY', 'tylerstong66/Tyler-ai')
    return requests.request(method, f'https://api.github.com/repos/{repo}{path}', headers=_github_headers(), timeout=TIMEOUT, **kwargs)


def _post(record):
    if not base.SUPABASE_URL:
        return False
    try:
        response = requests.post(
            f"{base.SUPABASE_URL.rstrip('/')}/rest/v1/memories",
            headers={**base.supabase_headers(), 'Prefer': 'return=minimal'},
            json={'memories': json.dumps(record, separators=(',', ':'), sort_keys=True), 'category': CATEGORY, 'importance': 10},
            timeout=TIMEOUT,
        )
        return bool(response.ok)
    except Exception:
        return False


def _recent(limit=40):
    if not base.SUPABASE_URL:
        return []
    try:
        response = requests.get(
            f"{base.SUPABASE_URL.rstrip('/')}/rest/v1/memories",
            headers=base.supabase_headers(),
            params={'select': 'id,created_at,memories', 'category': f'eq.{CATEGORY}', 'order': 'created_at.desc', 'limit': max(1, min(int(limit), 100))},
            timeout=TIMEOUT,
        )
        if not response.ok:
            return []
        latest = {}
        for row in response.json() or []:
            try:
                item = json.loads(str(row.get('memories') or ''))
            except Exception:
                continue
            key = str(item.get('deployment_id') or '').upper() if isinstance(item, dict) else ''
            if key and key not in latest:
                latest[key] = item
        return list(latest.values())
    except Exception:
        return []


def _record(deployment_id):
    target = str(deployment_id or '').upper()
    return next((x for x in _recent(80) if str(x.get('deployment_id') or '').upper() == target), None)


def _auto_deploy_off():
    return str(os.environ.get('RENDER_AUTO_DEPLOY_DISABLED_CONFIRMED', '')).strip().lower() in {'1', 'true', 'yes', 'on'}


def _runtime_commit():
    return _sha(os.environ.get('RENDER_GIT_COMMIT', ''))


def _main_sha():
    try:
        r = _github('GET', '/git/ref/heads/main')
        if not r.ok:
            return ''
        return _sha(((r.json() or {}).get('object') or {}).get('sha'))
    except Exception:
        return ''


def _merged_record(merge_id):
    item = MERGE_GATE.merge_record(str(merge_id or '').upper())
    if not item:
        return None, 'merge_not_found'
    if str(item.get('status') or '') != 'merged' or not item.get('human_gated_merge_performed'):
        return item, 'merge_not_complete'
    if item.get('automatic_merge_performed'):
        return item, 'automatic_merge_not_eligible'
    if not _sha(item.get('merge_commit_sha')):
        return item, 'merge_commit_missing'
    return item, None


def _validate(merge, expected_runtime=None):
    if not _auto_deploy_off():
        return None, 'render_auto_deploy_not_confirmed_disabled'
    target = _sha(merge.get('merge_commit_sha'))
    main = _main_sha()
    if not main:
        return None, 'current_main_lookup_failed'
    if main != target:
        return {'current_main': main, 'target': target}, 'current_main_drift'
    runtime = _runtime_commit()
    if not runtime:
        return {'current_main': main, 'target': target}, 'runtime_commit_missing'
    if expected_runtime and runtime != _sha(expected_runtime):
        return {'current_main': main, 'target': target, 'runtime': runtime}, 'runtime_commit_drift'
    return {'current_main': main, 'target': target, 'runtime': runtime}, None


def _find_run(deployment_id):
    try:
        r = _github('GET', f'/actions/workflows/{WORKFLOW_PATH}/runs', params={'event': 'repository_dispatch', 'per_page': 100})
        if not r.ok:
            return None
        title = f"Tyler production {str(deployment_id or '').upper()}"
        for run in (r.json() or {}).get('workflow_runs') or []:
            if str(run.get('display_title') or '') == title:
                return {'id': run.get('id'), 'status': str(run.get('status') or ''), 'conclusion': str(run.get('conclusion') or ''), 'html_url': run.get('html_url')}
    except Exception:
        pass
    return None


def _runtime_status():
    try:
        r = requests.get(SERVICE_URL + '/status', timeout=TIMEOUT)
        if not r.ok:
            return None
        data = r.json() or {}
        return {'commit': _sha(data.get('render_git_commit')), 'version': str(data.get('version_short') or '')}
    except Exception:
        return None


def production_status():
    return {
        'github_token_present': bool(os.environ.get('GITHUB_MAINTENANCE_TOKEN')),
        'render_auto_deploy_confirmed_disabled': _auto_deploy_off(),
        'runtime_commit_present': bool(_runtime_commit()),
        'workflow_path': WORKFLOW_PATH,
        'workflow_secret_required': 'RENDER_DEPLOY_HOOK_URL',
        'automatic_production_deployment_enabled': False,
        'blind_retry_after_unknown_dispatch_outcome_enabled': False,
    }


def prepare_production(merge_id):
    merge, error = _merged_record(merge_id)
    if error:
        return {'success': False, 'error': error, 'merge': merge}
    check, error = _validate(merge)
    if error:
        return {'success': False, 'error': error, 'validation': check}
    deployment_id = _deployment_id(merge.get('merge_id'), merge.get('merge_commit_sha'))
    existing = _record(deployment_id)
    if existing and str(existing.get('status') or '') in {'awaiting_approval', 'approved', 'deployment_dispatched', 'deployed', 'rolled_back'}:
        return {'success': True, 'deployment': existing, 'existing': True}
    record = {
        'deployment_id': deployment_id,
        'merge_id': str(merge.get('merge_id') or '').upper(),
        'promotion_id': str(merge.get('promotion_id') or '').upper(),
        'execution_id': str(merge.get('execution_id') or '').upper(),
        'review_id': str(merge.get('review_id') or ''),
        'pull_request_number': merge.get('pull_request_number'),
        'target_commit_sha': _sha(merge.get('merge_commit_sha')),
        'rollback_commit_sha': check['runtime'],
        'status': 'awaiting_approval',
        'approval_code': secrets.token_hex(3).upper(),
        'approval_granted': False,
        'approval_expires_at': None,
        'prepared_at': _iso(_now()),
        'deployment_dispatched': False,
        'production_deployment_performed': False,
        'post_deploy_health_verified': False,
        'rollback_performed': False,
        'unknown_dispatch_retry_performed': False,
    }
    return {'success': _post(record), 'deployment': record}


def approve_production(deployment_id, code):
    record = _record(deployment_id)
    if not record:
        return {'success': False, 'error': 'deployment_not_found'}
    if str(record.get('status') or '') != 'awaiting_approval':
        return {'success': False, 'error': 'deployment_not_awaiting_approval', 'deployment': record}
    if not secrets.compare_digest(str(record.get('approval_code') or '').upper(), str(code or '').upper()):
        return {'success': False, 'error': 'approval_code_mismatch', 'deployment': record}
    merge, error = _merged_record(record.get('merge_id'))
    if error:
        return {'success': False, 'error': error, 'deployment': record}
    check, error = _validate(merge, record.get('rollback_commit_sha'))
    if error:
        return {'success': False, 'error': error, 'validation': check, 'deployment': record}
    updated = dict(record)
    updated.update({'status': 'approved', 'approval_granted': True, 'approved_at': _iso(_now()), 'approval_expires_at': _iso(_now() + timedelta(minutes=TTL_MINUTES))})
    return {'success': _post(updated), 'deployment': updated}


def execute_production(deployment_id):
    record = _record(deployment_id)
    if not record:
        return {'success': False, 'error': 'deployment_not_found'}
    state = str(record.get('status') or '')
    if state in {'deployment_dispatched', 'deployed', 'rolled_back'}:
        return {'success': True, 'deployment': record, 'existing': True}
    if state == 'dispatch_outcome_unknown':
        return {'success': False, 'error': 'github_dispatch_outcome_unknown_retry_blocked', 'deployment': record}
    if state != 'approved' or not record.get('approval_granted'):
        return {'success': False, 'error': 'deployment_not_approved', 'deployment': record}
    expires = _parse(record.get('approval_expires_at'))
    if not expires or _now() >= expires:
        return {'success': False, 'error': 'deployment_approval_expired', 'deployment': record}
    merge, error = _merged_record(record.get('merge_id'))
    if error:
        return {'success': False, 'error': error, 'deployment': record}
    check, error = _validate(merge, record.get('rollback_commit_sha'))
    if error:
        return {'success': False, 'error': error, 'validation': check, 'deployment': record}
    payload = {'event_type': 'tyler-production-deploy', 'client_payload': {'deployment_id': str(record.get('deployment_id') or '').upper(), 'target_sha': _sha(record.get('target_commit_sha')), 'rollback_sha': _sha(record.get('rollback_commit_sha')), 'service_url': SERVICE_URL}}
    unknown = False
    try:
        r = _github('POST', '/dispatches', json=payload)
        if r.status_code != 204:
            return {'success': False, 'error': f'github_repository_dispatch_http_{r.status_code}', 'deployment': record}
    except requests.RequestException:
        unknown = True
    if unknown and not _find_run(record.get('deployment_id')):
        updated = dict(record)
        updated.update({'status': 'dispatch_outcome_unknown', 'unknown_dispatch_outcome': True, 'unknown_dispatch_retry_performed': False})
        _post(updated)
        return {'success': False, 'error': 'github_dispatch_outcome_unknown', 'deployment': updated}
    updated = dict(record)
    updated.update({'status': 'deployment_dispatched', 'deployment_dispatched': True, 'dispatched_at': _iso(_now()), 'dispatch_verified_after_unknown_outcome': bool(unknown)})
    return {'success': _post(updated), 'deployment': updated}


def verify_production(deployment_id):
    record = _record(deployment_id)
    if not record:
        return {'success': False, 'error': 'deployment_not_found'}
    if str(record.get('status') or '') == 'deployed':
        return {'success': True, 'deployment': record, 'terminal': True, 'existing': True}
    if str(record.get('status') or '') not in {'deployment_dispatched', 'dispatch_outcome_unknown'}:
        return {'success': False, 'error': 'deployment_not_dispatched', 'deployment': record}
    run = _find_run(record.get('deployment_id'))
    if not run or run.get('status') != 'completed':
        return {'success': True, 'pending': True, 'deployment': record, 'workflow_run': run}
    runtime = _runtime_status()
    target = _sha(record.get('target_commit_sha'))
    rollback = _sha(record.get('rollback_commit_sha'))
    if run.get('conclusion') == 'success' and runtime and runtime.get('commit') == target:
        updated = dict(record)
        updated.update({'status': 'deployed', 'production_deployment_performed': True, 'post_deploy_health_verified': True, 'verified_runtime_commit_sha': target, 'workflow_run_url': run.get('html_url'), 'deployed_at': _iso(_now())})
        return {'success': _post(updated), 'deployment': updated, 'workflow_run': run, 'terminal': True}
    if runtime and runtime.get('commit') == rollback:
        updated = dict(record)
        updated.update({'status': 'rolled_back', 'rollback_performed': True, 'verified_runtime_commit_sha': rollback, 'workflow_run_url': run.get('html_url'), 'rolled_back_at': _iso(_now())})
        _post(updated)
        return {'success': False, 'error': 'deployment_failed_and_rolled_back', 'deployment': updated, 'workflow_run': run, 'terminal': True}
    updated = dict(record)
    updated.update({'status': 'verification_failed', 'workflow_run_url': run.get('html_url'), 'verified_runtime_commit_sha': (runtime or {}).get('commit') or ''})
    _post(updated)
    return {'success': False, 'error': 'production_verification_failed', 'deployment': updated, 'workflow_run': run, 'terminal': True}


def cancel_production(deployment_id):
    record = _record(deployment_id)
    if not record:
        return {'success': False, 'error': 'deployment_not_found'}
    if str(record.get('status') or '') not in {'awaiting_approval', 'approved'}:
        return {'success': False, 'error': 'deployment_cannot_be_cancelled', 'deployment': record}
    updated = dict(record)
    updated.update({'status': 'cancelled', 'approval_granted': False, 'cancelled_at': _iso(_now())})
    return {'success': _post(updated), 'deployment': updated}


_ORIGINAL_SAFE_SOURCE_FILES = v217._safe_source_files_v217

def _safe_source_files_v2171():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ['app_v2_17_1.py']))

v210.v297._safe_source_files = _safe_source_files_v2171
EXECUTOR.safe_source_files_fn = _safe_source_files_v2171


def _id(pattern, message):
    m = re.search(pattern, str(message or ''), flags=re.I)
    return m.group(1).upper() if m else None


def _render(record, heading):
    record = dict(record or {})
    lines = [
        f"{heading}: {str(record.get('status') or 'unknown').upper()}",
        f"Deployment: {record.get('deployment_id') or 'unknown'}",
        f"Merge: {record.get('merge_id') or 'unknown'}",
        f"Pull request: #{record.get('pull_request_number') or 'unknown'}",
        f"Exact target commit: {record.get('target_commit_sha') or 'unknown'}",
        f"Rollback commit: {record.get('rollback_commit_sha') or 'unknown'}",
        '',
        'Render Auto Deploy must remain disabled: yes',
        'Current main must exactly match target: yes',
        'Fresh human production approval required: yes',
        'Exact-commit deployment required: yes',
        'Post-deploy health and commit verification required: yes',
        'Rollback to pinned previous commit on failed target health: yes',
        f"Deployment dispatched: {'yes' if record.get('deployment_dispatched') else 'no'}",
        f"Production deployment verified: {'yes' if record.get('production_deployment_performed') and record.get('post_deploy_health_verified') else 'no'}",
        f"Rollback performed: {'yes' if record.get('rollback_performed') else 'no'}",
    ]
    return '\n'.join(lines)


_PREVIOUS_HANDLE = v217.handle_message_v217

def handle_message_v2171(message):
    text = re.sub(r'\s+', ' ', str(message or '')).strip().lower()
    merge_id = _id(r'\b(MRG-[A-Fa-f0-9]{10})\b', message)
    deployment_id = _id(r'\b(DPL-[A-Fa-f0-9]{10})\b', message)
    code = _id(r'\bcode\s+([A-Fa-f0-9]{6})\b', message)

    if text in {'show production promotion gate', 'show maintenance production gate', 'show production gate'}:
        status = production_status()
        reply = '\n'.join([
            'Human-gated production promotion status',
            f"Stored production records: {len(_recent(20))}",
            f"GitHub maintenance token present: {'yes' if status['github_token_present'] else 'no'}",
            f"Render Auto Deploy confirmed disabled: {'yes' if status['render_auto_deploy_confirmed_disabled'] else 'no'}",
            f"Runtime commit visible: {'yes' if status['runtime_commit_present'] else 'no'}",
            'Merged commit must still be exact current main: yes',
            'One-time human production approval required: yes',
            'Separate execute command required after approval: yes',
            'Render deploy hook remains only in GitHub Actions secret storage: yes',
            'Required workflow secret: RENDER_DEPLOY_HOOK_URL',
            'Deploy exact commit SHA: yes',
            'Post-deploy health + RENDER_GIT_COMMIT verification: yes',
            'Rollback to pinned previous commit on failed target health: yes',
            'Automatic production deployment without approval: disabled',
            'Blind retry after unknown dispatch outcome: disabled',
        ])
        return base.base_payload(CATEGORY, reply, used_tools=['maintenance_production'], success=True) | {'maintenance_production_status': status}, 200

    if re.search(r'\bprepare\s+(?:the\s+)?production\s+(?:promotion|deployment)\b', text):
        if not merge_id:
            return base.base_payload(CATEGORY, 'Prepare production promotion requires an MRG- merge identifier.', used_tools=['maintenance_production'], success=False), 400
        result = prepare_production(merge_id)
        if not result.get('success'):
            return base.base_payload(CATEGORY, f"Production promotion could not be prepared. Reason: {result.get('error') or 'prepare_failed'}.", used_tools=['maintenance_production','github'], success=False) | {'maintenance_production_result': result}, 409
        record = result['deployment']
        reply = _render(record, 'Production promotion prepared') + f"\n\nNo production deployment occurred during preparation.\nApproval code: {record.get('approval_code')}\n\nTo approve this exact target and rollback pair, send:\nApprove production promotion {record.get('deployment_id')} code {record.get('approval_code')}"
        return base.base_payload(CATEGORY, reply, used_tools=['maintenance_production','github'], success=True) | {'maintenance_production': record}, 200

    if re.search(r'\bapprove\s+(?:the\s+)?production\s+(?:promotion|deployment)\b', text):
        if not deployment_id or not code:
            return base.base_payload(CATEGORY, 'Approve production promotion requires a DPL- identifier and six-character code.', used_tools=['maintenance_production'], success=False), 400
        result = approve_production(deployment_id, code)
        if not result.get('success'):
            return base.base_payload(CATEGORY, f"Production promotion was not approved. Reason: {result.get('error') or 'approval_failed'}.", used_tools=['maintenance_production','github'], success=False) | {'maintenance_production_result': result}, 409
        record = result['deployment']
        reply = _render(record, 'Production promotion approval') + f"\n\nApproval expires: {record.get('approval_expires_at')}\nNo production deployment occurred during approval.\nThe approval includes rollback to the pinned previous commit if target health fails.\n\nTo dispatch the exact deployment, send:\nExecute approved production promotion {record.get('deployment_id')}"
        return base.base_payload(CATEGORY, reply, used_tools=['maintenance_production','github'], success=True) | {'maintenance_production': record}, 200

    if re.search(r'\bexecute\s+(?:the\s+)?(?:approved\s+)?production\s+(?:promotion|deployment)\b', text):
        if not deployment_id:
            return base.base_payload(CATEGORY, 'Execute approved production promotion requires a DPL- identifier.', used_tools=['maintenance_production'], success=False), 400
        result = execute_production(deployment_id)
        if not result.get('success'):
            return base.base_payload(CATEGORY, f"Production promotion was not dispatched. Reason: {result.get('error') or 'dispatch_failed'}.", used_tools=['maintenance_production','github'], success=False) | {'maintenance_production_result': result}, 409
        record = result['deployment']
        reply = _render(record, 'Production promotion dispatch') + f"\n\nThe exact deployment workflow was dispatched. Do not dispatch it again.\nAfter the workflow finishes, send:\nVerify production promotion {record.get('deployment_id')}"
        return base.base_payload(CATEGORY, reply, used_tools=['maintenance_production','github'], success=True) | {'maintenance_production': record}, 200

    if re.search(r'\bverify\s+(?:the\s+)?production\s+(?:promotion|deployment)\b', text):
        if not deployment_id:
            return base.base_payload(CATEGORY, 'Verify production promotion requires a DPL- identifier.', used_tools=['maintenance_production'], success=False), 400
        result = verify_production(deployment_id)
        record = result.get('deployment') or {}
        if result.get('pending'):
            reply = _render(record, 'Production promotion verification') + f"\n\nStatus: PENDING — deployment workflow is still running.\nRe-run: Verify production promotion {deployment_id}"
            return base.base_payload(CATEGORY, reply, used_tools=['maintenance_production','github'], success=True) | {'maintenance_production': record}, 200
        if result.get('success'):
            reply = _render(record, 'Production promotion verification') + '\n\nVERIFIED — production is healthy on the exact approved commit. Render Auto Deploy remains disabled.'
            return base.base_payload(CATEGORY, reply, used_tools=['maintenance_production','github'], success=True) | {'maintenance_production': record}, 200
        error = result.get('error') or 'verification_failed'
        suffix = '\n\nTARGET FAILED HEALTH VERIFICATION — rollback to the pinned previous commit was verified.' if error == 'deployment_failed_and_rolled_back' else f"\n\nProduction verification did not pass. Reason: {error}. Do not blindly retry."
        return base.base_payload(CATEGORY, _render(record, 'Production promotion verification') + suffix, used_tools=['maintenance_production','github'], success=False) | {'maintenance_production': record}, 409

    if re.search(r'\bcancel\s+(?:the\s+)?production\s+(?:promotion|deployment)\b', text):
        if not deployment_id:
            return base.base_payload(CATEGORY, 'Cancel production promotion requires a DPL- identifier.', used_tools=['maintenance_production'], success=False), 400
        result = cancel_production(deployment_id)
        record = result.get('deployment') or {}
        return base.base_payload(CATEGORY, _render(record, 'Production promotion cancelled') if result.get('success') else f"Production promotion was not cancelled. Reason: {result.get('error') or 'cancel_failed'}.", used_tools=['maintenance_production'], success=bool(result.get('success'))) | {'maintenance_production_result': result}, 200 if result.get('success') else 409

    return _PREVIOUS_HANDLE(message)


base.handle_message = handle_message_v2171

_PREVIOUS_STATUS = app.view_functions.get('status')
_PREVIOUS_HEALTH = app.view_functions.get('health')

def status_v2171():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    data['render_git_commit'] = os.environ.get('RENDER_GIT_COMMIT', '')
    return base.jsonify(data)

def health_v2171():
    response = _PREVIOUS_HEALTH()
    data = dict(response.get_json() or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    data['render_git_commit'] = os.environ.get('RENDER_GIT_COMMIT', '')
    return base.jsonify(data)

app.view_functions['status'] = status_v2171
app.view_functions['health'] = health_v2171

@app.get('/diagnostics/maintenance/production')
def maintenance_production_diagnostics():
    if not base.authorized() and not base.ui_logged_in():
        return base.jsonify({'success': False, 'error': 'unauthorized'}), 401
    return base.jsonify({'success': True, 'version': base.VERSION, 'version_short': base.VERSION_SHORT, 'render_git_commit': os.environ.get('RENDER_GIT_COMMIT', ''), 'status': production_status(), 'recent': _recent(10)})

__all__ = ['app','base','ENGINE','VERSION','VERSION_SHORT','EXECUTOR','DRILL_EXECUTOR','PLANNER','OPS','REVIEW_GATE','PROMOTION','MERGE_GATE','handle_message_v2171']