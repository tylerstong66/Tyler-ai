import os
import re
import secrets
from pathlib import Path

import app_v2_14 as v214
from maintenance_execution_drill import (
    DRILL_CATEGORY,
    DRILL_TARGET_FILE,
    SafeMaintenanceExecutionDrillCoordinator,
    deterministic_drill_patch,
    make_drill_plan,
)


# v2.14.1 adds a safe, explicit three-stage execution drill for the newly
# configured GitHub review-branch publisher. The drill uses a dedicated source
# target and dedicated Supabase category. It never writes to main and never
# deploys production.
v214.base.VERSION = '2.14.1-safe-maintenance-execution-drill'
v214.base.VERSION_SHORT = 'v2.14.1'

base = v214.base
app = v214.app
ENGINE = v214.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v214.EXECUTOR
PLANNER = v214.PLANNER
OPS = v214.OPS
v210 = v214.v210
base.SPECIAL_MEMORY_CATEGORIES.add(DRILL_CATEGORY)


_DRILL_PLANS = {}


def _new_plan_id():
    return 'MNT-' + secrets.token_hex(5).upper()


def _drill_plan_loader(plan_id):
    return _DRILL_PLANS.get(str(plan_id or '').upper())


DRILL_EXECUTOR = SafeMaintenanceExecutionDrillCoordinator(
    plan_loader=_drill_plan_loader,
    safe_source_files_fn=lambda: [DRILL_TARGET_FILE],
    patch_generator_fn=deterministic_drill_patch,
    supabase_url_fn=lambda: base.SUPABASE_URL,
    headers_fn=base.supabase_headers,
    version_fn=lambda: base.VERSION_SHORT,
    source_root=Path(__file__).resolve().parent,
    timeout_seconds=int(os.environ.get('MAINTENANCE_EXECUTION_TIMEOUT_SECONDS', '10')),
    approval_ttl_minutes=int(os.environ.get('MAINTENANCE_APPROVAL_TTL_MINUTES', '30')),
    github_token_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_TOKEN', ''),
    github_repository_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_REPOSITORY', 'tylerstong66/Tyler-ai'),
    github_base_branch_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_BASE_BRANCH', 'main'),
)


# Include the drill implementation in Tyler's future verified source grounding.
_ORIGINAL_SAFE_SOURCE_FILES = v210.v297._safe_source_files


def _safe_source_files_v2141():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    for name in [
        'maintenance_execution_drill.py',
        'maintenance_execution_drill_target.py',
        'app_v2_14_1.py',
    ]:
        if name not in names:
            names.append(name)
    return sorted(set(names))


v210.v297._safe_source_files = _safe_source_files_v2141
EXECUTOR.safe_source_files_fn = _safe_source_files_v2141


def _norm(message):
    return re.sub(r'\s+', ' ', str(message or '')).strip().lower()


def _drill_approval_parts(message):
    match = re.search(
        r'\bapprove\s+maintenance\s+execution\s+drill\s+(EXE-[A-Fa-f0-9]{10})\s+code\s+([A-Fa-f0-9]{6})\b',
        str(message or ''),
        flags=re.I,
    )
    if not match:
        return None, None
    return match.group(1).upper(), match.group(2).upper()


def _drill_execute_id(message):
    match = re.search(
        r'\bexecute\s+approved\s+maintenance\s+drill\s+(EXE-[A-Fa-f0-9]{10})\b',
        str(message or ''),
        flags=re.I,
    )
    return match.group(1).upper() if match else None


def _render_drill(package):
    package = dict(package or {})
    publish = dict(package.get('github_publish') or {})
    status = str(package.get('status') or 'unknown')
    lines = [
        'Safe maintenance execution drill',
        f"Execution: {package.get('execution_id') or 'unknown'}",
        f"Status: {status.upper()}",
        'Target: dedicated harmless drill file only',
        'Direct write to main: no',
        'Production deployment: no',
        'Automatic pull request creation: no',
    ]
    if status == 'awaiting_approval':
        lines.extend([
            '',
            'PREPARE STAGE PASSED — no GitHub write has occurred.',
            f"Approval code: {package.get('approval_code')}",
            'Approve with:',
            f"Approve maintenance execution drill {package.get('execution_id')} code {package.get('approval_code')}",
            '',
            'Approval still will not write to GitHub. A separate execute command is required.',
        ])
    elif status == 'approved':
        lines.extend([
            '',
            'APPROVAL STAGE PASSED — no GitHub write has occurred.',
            f"Approval expires: {package.get('approval_expires_at')}",
            'Execute the isolated review-branch write with:',
            f"Execute approved maintenance drill {package.get('execution_id')}",
        ])
    elif status == 'published_for_review':
        lines.extend([
            '',
            'EXECUTION STAGE COMPLETE.',
            f"Review branch: {publish.get('branch') or 'unknown'}",
            f"Proposal commit: {publish.get('proposal_commit_sha') or 'unknown'}",
            'Main changed: no',
            'Render production deployed: no',
        ])
    return '\n'.join(lines)


def drill_status_payload():
    items = DRILL_EXECUTOR.recent(limit=10)
    status = DRILL_EXECUTOR.status()
    lines = [
        'Safe maintenance execution drill status',
        f"GitHub review-branch publishing configured: {'yes' if status.get('github_write_configured') else 'no'}",
        f"Stored drill packages: {len(items)}",
        'Drill target isolated from production source: yes',
        'Drill history isolated from real maintenance history: yes',
        'Approval required before GitHub write: yes',
        'Separate execute command required after approval: yes',
        'Direct writes to main: disabled',
        'Automatic production deployment: disabled',
    ]
    return base.base_payload(
        'maintenance_execution_drill',
        '\n'.join(lines),
        used_tools=['maintenance_execution_drill'],
        success=True,
    ) | {'maintenance_execution_drill_status': status, 'maintenance_execution_drills': items}


def prepare_drill_payload():
    if not DRILL_EXECUTOR.github_configured():
        return base.base_payload(
            'maintenance_execution_drill',
            'Safe execution drill cannot start because GitHub review-branch publishing is not configured. No change occurred.',
            used_tools=['maintenance_execution_drill'],
            success=False,
        ), 409
    plan_id = _new_plan_id()
    _DRILL_PLANS[plan_id] = make_drill_plan(plan_id)
    result = DRILL_EXECUTOR.prepare(plan_id, persist=True)
    if not result.get('success'):
        return base.base_payload(
            'maintenance_execution_drill',
            f"Safe execution drill did not prepare. Reason: {result.get('error') or 'prepare_failed'}. No GitHub or production change occurred.",
            used_tools=['maintenance_execution_drill'],
            success=False,
        ) | {'maintenance_execution_drill_result': result}, 409
    package = result.get('package') or {}
    return base.base_payload(
        'maintenance_execution_drill',
        _render_drill(package),
        used_tools=['maintenance_execution_drill'],
        success=True,
    ) | {'maintenance_execution_drill': package}, 200


def approve_drill_payload(execution_id, code):
    result = DRILL_EXECUTOR.approve(execution_id, code)
    if not result.get('success'):
        return base.base_payload(
            'maintenance_execution_drill',
            f"Safe execution drill {execution_id} was not approved. Reason: {result.get('error') or 'approval_failed'}. No GitHub write occurred.",
            used_tools=['maintenance_execution_drill'],
            success=False,
        ) | {'maintenance_execution_drill_result': result}, 409
    package = result.get('package') or {}
    return base.base_payload(
        'maintenance_execution_drill',
        _render_drill(package),
        used_tools=['maintenance_execution_drill'],
        success=True,
    ) | {'maintenance_execution_drill': package}, 200


def execute_drill_payload(execution_id):
    result = DRILL_EXECUTOR.execute_approved(execution_id)
    if not result.get('success'):
        return base.base_payload(
            'maintenance_execution_drill',
            f"Safe execution drill {execution_id} was not published. Reason: {result.get('error') or 'execution_failed'}. Main and Render production were not intentionally changed.",
            used_tools=['maintenance_execution_drill'],
            success=False,
        ) | {'maintenance_execution_drill_result': result}, 409

    package = result.get('package') or {}
    verification = DRILL_EXECUTOR.verify_published_drill(package)
    if not verification.get('success'):
        reply = (
            _render_drill(package)
            + '\n\nPOST-PUBLISH VERIFICATION DID NOT PASS. Do not merge the review branch. '
              'Main was not intentionally written by the drill. Inspect the review branch before any further action.'
        )
        return base.base_payload(
            'maintenance_execution_drill',
            reply,
            used_tools=['maintenance_execution_drill'],
            success=False,
        ) | {
            'maintenance_execution_drill': package,
            'maintenance_execution_drill_verification': verification,
        }, 409

    reply = (
        _render_drill(package)
        + '\n\nResult: PASS — review-branch publishing verified end-to-end.'
        + '\nReview branch changed: yes'
        + '\nMain verified unchanged: yes'
        + '\nProduction deployment performed: no'
        + '\nThe harmless review branch remains available for inspection; it was not merged.'
    )
    return base.base_payload(
        'maintenance_execution_drill',
        reply,
        used_tools=['maintenance_execution_drill'],
        success=True,
    ) | {
        'maintenance_execution_drill': package,
        'maintenance_execution_drill_verification': verification,
    }, 200


_PREVIOUS_HANDLE_MESSAGE = v214.handle_message_v214


def handle_message_v2141(message):
    normalized = _norm(message)
    approval_id, approval_code = _drill_approval_parts(message)
    execution_id = _drill_execute_id(message)

    if normalized in {
        'show maintenance execution drill',
        'show maintenance execution test',
        'maintenance execution drill status',
    }:
        return drill_status_payload(), 200

    if normalized in {
        'run maintenance execution test',
        'run maintenance execution drill',
        'prepare maintenance execution drill',
    }:
        return prepare_drill_payload()

    if approval_id and approval_code:
        return approve_drill_payload(approval_id, approval_code)

    if execution_id:
        return execute_drill_payload(execution_id)

    return _PREVIOUS_HANDLE_MESSAGE(message)


base.handle_message = handle_message_v2141


# Keep status/health version reporting current where earlier layers captured a
# previous version string.
_PREVIOUS_STATUS_VIEW = app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = app.view_functions.get('health')


def status_v2141():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    if 'safe_maintenance_execution_drill' not in capabilities:
        capabilities.append('safe_maintenance_execution_drill')
    return base.jsonify(data)


def health_v2141():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


if _PREVIOUS_STATUS_VIEW is not None:
    app.view_functions['status'] = status_v2141
if _PREVIOUS_HEALTH_VIEW is not None:
    app.view_functions['health'] = health_v2141
