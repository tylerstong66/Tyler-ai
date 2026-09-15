import json
import os
import re
from pathlib import Path

import app_v2_13_1 as v2131
from maintenance_execution import (
    MAINTENANCE_EXECUTION_CATEGORY,
    MaintenanceExecutionCoordinator,
)


# v2.14 adds approval-gated maintenance execution. Tyler may explicitly prepare
# a validated source patch package, but it cannot touch GitHub until the user
# approves that exact package with its one-time code and then sends a separate
# execute command. Approved execution publishes only to a new review branch;
# it never writes directly to main and never deploys production.
v2131.base.VERSION = '2.14.0-approval-gated-maintenance-execution'
v2131.base.VERSION_SHORT = 'v2.14.0'

base = v2131.base
app = v2131.app
ENGINE = v2131.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
PLANNER = v2131.PLANNER
OPS = v2131.OPS
v213 = v2131.v213
v210 = v213.v210

MAINTENANCE_EXECUTION_TIMEOUT_SECONDS = int(os.environ.get('MAINTENANCE_EXECUTION_TIMEOUT_SECONDS', '10'))
MAINTENANCE_APPROVAL_TTL_MINUTES = int(os.environ.get('MAINTENANCE_APPROVAL_TTL_MINUTES', '30'))
base.SPECIAL_MEMORY_CATEGORIES.add(MAINTENANCE_EXECUTION_CATEGORY)


def _generate_patch(plan, source_context, execution_id):
    safe_plan = {
        'maintenance_plan_id': plan.get('maintenance_plan_id'),
        'incident_id': plan.get('incident_id'),
        'service': plan.get('service'),
        'severity': plan.get('severity'),
        'kind': plan.get('kind'),
        'likely_cause': plan.get('likely_cause'),
        'proposed_patch': plan.get('proposed_patch'),
        'test_plan': plan.get('test_plan'),
    }
    system = (
        'You are Tyler AI maintenance patch preparation. Produce JSON only. '
        'You are NOT executing code, changing configuration, deploying, retrying side effects, '
        'or writing to GitHub. Build the smallest reversible source-code patch supported by the '
        'verified excerpts. Never invent a file or function. Never include credentials or literal '
        'secrets. Preserve approval gates, receipt verification, passive telemetry, and no-blind-retry '
        'safety. Each find string MUST be copied exactly from the supplied source and must be specific '
        'enough to occur exactly once. Return exactly this shape: '
        '{"summary":"...","changes":[{"path":"existing.py","find":"exact existing text",'
        '"replace":"replacement text","reason":"..."}]}. '
        'Only use file paths visible in VERIFIED SOURCE EXCERPTS. Do not use markdown fences.'
    )
    user = (
        f'Execution package: {execution_id}\n'
        f'MAINTENANCE PLAN:\n{json.dumps(safe_plan, ensure_ascii=False, sort_keys=True)}\n\n'
        f'VERIFIED SOURCE EXCERPTS:\n{source_context}'
    )
    return base.groq(
        [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        tokens=2600,
        temperature=0.1,
        json_mode=True,
    )


EXECUTOR = MaintenanceExecutionCoordinator(
    plan_loader=PLANNER.plan,
    safe_source_files_fn=lambda: v210.v297._safe_source_files(),
    patch_generator_fn=_generate_patch,
    supabase_url_fn=lambda: base.SUPABASE_URL,
    headers_fn=base.supabase_headers,
    version_fn=lambda: base.VERSION_SHORT,
    source_root=Path(__file__).resolve().parent,
    timeout_seconds=MAINTENANCE_EXECUTION_TIMEOUT_SECONDS,
    approval_ttl_minutes=MAINTENANCE_APPROVAL_TTL_MINUTES,
    github_token_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_TOKEN', ''),
    github_repository_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_REPOSITORY', 'tylerstong66/Tyler-ai'),
    github_base_branch_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_BASE_BRANCH', 'main'),
)


# Include this execution layer in future verified Tyler Developer grounding.
_ORIGINAL_SAFE_SOURCE_FILES = v210.v297._safe_source_files


def _safe_source_files_v214():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    for name in ['maintenance_execution.py', 'app_v2_14.py']:
        if name not in names:
            names.append(name)
    return sorted(set(names))


v210.v297._safe_source_files = _safe_source_files_v214
EXECUTOR.safe_source_files_fn = _safe_source_files_v214


def _norm(message):
    return re.sub(r'\s+', ' ', str(message or '')).strip().lower()


def _extract_identifier(message):
    match = re.search(r'\b((?:INC|MNT|EXE)-[A-Fa-f0-9]{10})\b', str(message or ''))
    return match.group(1).upper() if match else None


def execution_status_request(message):
    return _norm(message) in {
        'show maintenance execution',
        'show maintenance executions',
        'show maintenance execution status',
        'maintenance execution',
        'maintenance execution status',
    }


def prepare_execution_request(message):
    return bool(re.search(r'\b(?:prepare|build|create)\s+(?:a\s+)?maintenance\s+execution\b', _norm(message)))


def show_execution_request(message):
    return bool(re.search(r'\b(?:show|review|display|open)\s+(?:the\s+)?maintenance\s+execution\b', _norm(message)))


def execute_request(message):
    return bool(re.search(r'\bexecute\s+(?:the\s+)?approved\s+maintenance\b', _norm(message)))


def cancel_request(message):
    return bool(re.search(r'\bcancel\s+(?:the\s+)?maintenance\s+execution\b', _norm(message)))


def _approval_parts(message):
    match = re.search(
        r'\bapprove\s+maintenance\s+execution\s+(EXE-[A-Fa-f0-9]{10})\s+code\s+([A-Fa-f0-9]{6})\b',
        str(message or ''),
        flags=re.I,
    )
    if not match:
        return None, None
    return match.group(1).upper(), match.group(2).upper()


def _render_execution(package):
    package = dict(package or {})
    patch = dict(package.get('patch_spec') or {})
    changed = [item.get('path') for item in patch.get('changed_files') or [] if item.get('path')]
    target = dict(package.get('target') or {})
    github_publish = dict(package.get('github_publish') or {})
    lines = [
        f"Maintenance execution {package.get('execution_id')}",
        f"Maintenance plan: {package.get('maintenance_plan_id')}",
        f"Incident: {package.get('incident_id') or 'unknown'}",
        f"Service: {package.get('service') or 'unknown'}",
        f"Status: {str(package.get('status') or 'unknown').upper()}",
        '',
        'Patch package:',
        str(patch.get('summary') or 'No patch summary available.'),
        f"Changed files: {', '.join(changed) if changed else 'none'}",
        '',
        f"Target repository: {target.get('repository') or 'not configured'}",
        f"Base branch: {target.get('base_branch') or 'main'}",
        'Direct write to main: no',
        'Automatic pull request creation: no',
        'Automatic production deployment: no',
    ]
    status = str(package.get('status') or '')
    if status == 'awaiting_approval':
        lines.extend([
            '',
            'APPROVAL REQUIRED BEFORE ANY GITHUB WRITE.',
            f"Approval code: {package.get('approval_code')}",
            'Approve with:',
            f"Approve maintenance execution {package.get('execution_id')} code {package.get('approval_code')}",
            '',
            'Approval alone does not execute the patch. A separate execute command is required afterward.',
        ])
    elif status == 'approved':
        lines.extend([
            '',
            f"Approval expires: {package.get('approval_expires_at')}",
            'No GitHub write has occurred yet.',
            'To publish the approved patch to a new review branch:',
            f"Execute approved maintenance {package.get('execution_id')}",
        ])
    elif status == 'published_for_review':
        lines.extend([
            '',
            f"Review branch: {github_publish.get('branch') or 'unknown'}",
            f"Proposal commit: {github_publish.get('proposal_commit_sha') or 'unknown'}",
            'Production branch changed: no',
            'Production deployment performed: no',
        ])
    return '\n'.join(lines)


def execution_status_payload():
    items = EXECUTOR.recent(limit=10)
    status = EXECUTOR.status()
    lines = [
        'Approval-gated maintenance execution status',
        f"Stored execution packages: {len(items)}",
        f"GitHub review-branch publishing configured: {'yes' if status.get('github_write_configured') else 'no'}",
        'Automatic patch generation: disabled',
        'Automatic GitHub writes: disabled',
        'Direct writes to main: disabled',
        'Automatic production deployment: disabled',
        'Approval required before GitHub write: yes',
        'Separate execute command after approval: yes',
    ]
    if items:
        lines.extend(['', 'Recent maintenance executions:'])
        for item in items[:5]:
            lines.append(
                f"- {item.get('execution_id')} · {item.get('maintenance_plan_id')} · "
                f"{str(item.get('service') or '').upper()} · {str(item.get('status') or '').upper()}"
            )
    else:
        lines.extend(['', 'No maintenance execution packages have been prepared yet.'])
    if not status.get('github_write_configured'):
        lines.extend([
            '',
            'GitHub publishing is safely unavailable until GITHUB_MAINTENANCE_TOKEN is configured.',
            'Preparing and reviewing patch packages still works without that token.',
        ])
    return base.base_payload(
        'maintenance_execution',
        '\n'.join(lines),
        used_tools=['maintenance_execution'],
        success=True,
    ) | {
        'maintenance_execution_status': status,
        'maintenance_executions': items,
    }


def prepare_execution_payload(identifier):
    result = EXECUTOR.prepare(identifier, persist=True)
    if not result.get('success'):
        error = result.get('error') or 'unable_to_prepare_execution'
        detail = result.get('detail')
        reply = f'I could not prepare a maintenance execution package for {identifier}. Reason: {error}.'
        if detail:
            reply += f' Safe detail: {detail}.'
        if error == 'outcome_verification_required_before_patch':
            reply += ' Verify the real downstream outcome first; Tyler will not prepare a blind retry patch.'
        return base.base_payload(
            'maintenance_execution',
            reply,
            used_tools=['maintenance_execution'],
            success=False,
        ) | {'maintenance_execution_result': result}
    package = result.get('package') or {}
    reply = _render_execution(package)
    return base.base_payload(
        'maintenance_execution',
        reply,
        used_tools=['maintenance_execution'],
        success=True,
    ) | {'maintenance_execution': package, 'maintenance_execution_saved': bool(result.get('saved'))}


def approve_execution_payload(execution_id, code):
    result = EXECUTOR.approve(execution_id, code)
    if not result.get('success'):
        return base.base_payload(
            'maintenance_execution',
            f"Maintenance execution {execution_id} was not approved. Reason: {result.get('error') or 'approval_failed'}.",
            used_tools=['maintenance_execution'],
            success=False,
        ) | {'maintenance_execution_result': result}
    package = result.get('package') or {}
    return base.base_payload(
        'maintenance_execution',
        _render_execution(package),
        used_tools=['maintenance_execution'],
        success=True,
    ) | {'maintenance_execution': package}


def execute_payload(execution_id):
    result = EXECUTOR.execute_approved(execution_id)
    if not result.get('success'):
        error = result.get('error') or 'execution_failed'
        reply = f'Maintenance execution {execution_id} was not published. Reason: {error}.'
        if error == 'github_write_not_configured':
            reply += ' No GitHub or production change occurred.'
        elif error in {'source_or_patch_drift', 'approval_expired', 'execution_not_approved'}:
            reply += ' No GitHub or production change occurred; prepare/review again rather than bypassing the gate.'
        return base.base_payload(
            'maintenance_execution',
            reply,
            used_tools=['maintenance_execution'],
            success=False,
        ) | {'maintenance_execution_result': result}
    package = result.get('package') or {}
    reply = _render_execution(package)
    if result.get('persistence_warning'):
        reply += '\n\nWarning: the review branch was created, but Tyler could not confirm the final state was persisted. Do not retry automatically.'
    return base.base_payload(
        'maintenance_execution',
        reply,
        used_tools=['maintenance_execution'],
        success=True,
    ) | {'maintenance_execution': package}


def show_execution_payload(execution_id):
    package = EXECUTOR.execution(execution_id)
    if not package:
        return base.base_payload(
            'maintenance_execution',
            f'Maintenance execution {execution_id} was not found.',
            used_tools=['maintenance_execution'],
            success=False,
        ) | {'maintenance_execution': None}
    return base.base_payload(
        'maintenance_execution',
        _render_execution(package),
        used_tools=['maintenance_execution'],
        success=True,
    ) | {'maintenance_execution': package}


def cancel_execution_payload(execution_id):
    result = EXECUTOR.cancel(execution_id)
    if not result.get('success'):
        return base.base_payload(
            'maintenance_execution',
            f"Maintenance execution {execution_id} was not cancelled. Reason: {result.get('error') or 'cancel_failed'}.",
            used_tools=['maintenance_execution'],
            success=False,
        ) | {'maintenance_execution_result': result}
    package = result.get('package') or {}
    return base.base_payload(
        'maintenance_execution',
        f'Maintenance execution {execution_id} is CANCELLED. No GitHub or production action will be taken from this package.',
        used_tools=['maintenance_execution'],
        success=True,
    ) | {'maintenance_execution': package}


_PREVIOUS_HANDLE_MESSAGE = v2131.handle_message_v2131


def handle_message_v214(message):
    approval_id, approval_code = _approval_parts(message)
    identifier = _extract_identifier(message)

    if execution_status_request(message):
        return execution_status_payload(), 200

    if approval_id and approval_code:
        payload = approve_execution_payload(approval_id, approval_code)
        return payload, 200 if payload.get('success') else 409

    if identifier and prepare_execution_request(message):
        if identifier.startswith('EXE-'):
            return base.base_payload(
                'maintenance_execution',
                'Prepare maintenance execution expects an MNT- maintenance plan or INC- incident identifier.',
                used_tools=['maintenance_execution'],
                success=False,
            ), 400
        payload = prepare_execution_payload(identifier)
        return payload, 200 if payload.get('success') else 409

    if identifier and execute_request(message):
        if not identifier.startswith('EXE-'):
            return base.base_payload(
                'maintenance_execution',
                'Execute approved maintenance expects an EXE- execution identifier.',
                used_tools=['maintenance_execution'],
                success=False,
            ), 400
        payload = execute_payload(identifier)
        return payload, 200 if payload.get('success') else 409

    if identifier and cancel_request(message):
        if not identifier.startswith('EXE-'):
            return base.base_payload(
                'maintenance_execution',
                'Cancel maintenance execution expects an EXE- execution identifier.',
                used_tools=['maintenance_execution'],
                success=False,
            ), 400
        payload = cancel_execution_payload(identifier)
        return payload, 200 if payload.get('success') else 409

    if identifier and show_execution_request(message):
        if not identifier.startswith('EXE-'):
            return base.base_payload(
                'maintenance_execution',
                'Show maintenance execution expects an EXE- execution identifier.',
                used_tools=['maintenance_execution'],
                success=False,
            ), 400
        payload = show_execution_payload(identifier)
        return payload, 200 if payload.get('success') else 404

    return _PREVIOUS_HANDLE_MESSAGE(message)


base.handle_message = handle_message_v214


_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v214():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' v2.14 adds approval-gated maintenance execution. Explicit preparation can turn a '
          'source-grounded maintenance plan into a validated exact-match patch package. The package '
          'must be durably approved using its execution ID and one-time approval code, followed by a '
          'separate execute command. Execution may publish only an atomic proposal commit to a new '
          'GitHub review branch when a dedicated GitHub maintenance token is configured. It never '
          'writes directly to main, creates a pull request automatically, deploys production, changes '
          'configuration, or retries an uncertain side effect.'
    )


def project_reply_v214():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nApproval-gated maintenance execution:'
        + '\n- Explicitly prepares a validated exact-match source patch from a maintenance plan'
        + '\n- Rejects simulated plans, unverified source, source drift, syntax-invalid patches, and secret literals'
        + '\n- Unknown external outcomes must be verified before Tyler will prepare a patch'
        + '\n- Approval requires the exact EXE identifier plus a one-time code and expires'
        + '\n- A second explicit execute command is required after approval'
        + '\n- Approved execution can publish only to a new GitHub review branch, never directly to main'
        + '\n- No automatic PR, production deploy, configuration change, or side-effect retry'
    )


base.core_project_text = core_project_text_v214
base.project_reply = project_reply_v214


_PREVIOUS_STATUS_VIEW = base.app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = base.app.view_functions.get('health')


def status_v214():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'approval_gated_maintenance_execution',
        'validated_exact_match_patch_packages',
        'expiring_durable_maintenance_approvals',
        'atomic_github_review_branch_publishing',
        'source_drift_prevention',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    tools = data.setdefault('tools', [])
    if 'maintenance_execution' not in tools:
        tools.append('maintenance_execution')
    data['maintenance_execution'] = EXECUTOR.status()
    return base.jsonify(data)


def health_v214():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


base.app.view_functions['status'] = status_v214
base.app.view_functions['health'] = health_v214


if 'maintenance_execution_diagnostics_api' not in base.app.view_functions:
    @base.app.route('/diagnostics/maintenance/execution', methods=['GET'])
    def maintenance_execution_diagnostics_api():
        if not (base.authorized() or base.ui_logged_in()):
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return base.jsonify({
            'success': True,
            'version': base.VERSION,
            'version_short': base.VERSION_SHORT,
            'maintenance_execution': EXECUTOR.status(),
            'executions': EXECUTOR.recent(limit=50),
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
