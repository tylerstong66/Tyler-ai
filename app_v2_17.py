import os
import re

import app_v2_16 as v216
from maintenance_merge import MAINTENANCE_MERGE_CATEGORY, MaintenanceMergeCoordinator


# v2.17 adds a human-gated GitHub merge after v2.16 pull-request creation.
# Merge is fail-closed unless Render auto-deploy has been explicitly confirmed
# disabled, so merging and production deployment remain separate operations.
v216.base.VERSION = '2.17.0-human-gated-merge-and-deploy-isolation'
v216.base.VERSION_SHORT = 'v2.17.0'

base = v216.base
app = v216.app
ENGINE = v216.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v216.EXECUTOR
DRILL_EXECUTOR = v216.DRILL_EXECUTOR
PLANNER = v216.PLANNER
OPS = v216.OPS
REVIEW_GATE = v216.REVIEW_GATE
PROMOTION = v216.PROMOTION
v210 = v216.v210
base.SPECIAL_MEMORY_CATEGORIES.add(MAINTENANCE_MERGE_CATEGORY)

MERGE_GATE = MaintenanceMergeCoordinator(
    promotion_loader=PROMOTION.promotion,
    review_gate=REVIEW_GATE,
    supabase_url_fn=lambda: base.SUPABASE_URL,
    headers_fn=base.supabase_headers,
    version_fn=lambda: base.VERSION_SHORT,
    github_token_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_TOKEN', ''),
    github_repository_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_REPOSITORY', 'tylerstong66/Tyler-ai'),
    github_base_branch_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_BASE_BRANCH', 'main'),
    render_auto_deploy_disabled_fn=lambda: str(
        os.environ.get('RENDER_AUTO_DEPLOY_DISABLED_CONFIRMED', '')
    ).strip().lower() in {'1', 'true', 'yes', 'on'},
    timeout_seconds=int(os.environ.get('MAINTENANCE_MERGE_TIMEOUT_SECONDS', '10')),
    approval_ttl_minutes=int(os.environ.get('MAINTENANCE_MERGE_APPROVAL_TTL_MINUTES', '30')),
)

_ORIGINAL_SAFE_SOURCE_FILES = v216._safe_source_files_v216


def _safe_source_files_v217():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    for name in ['maintenance_merge.py', 'app_v2_17.py']:
        if name not in names:
            names.append(name)
    return sorted(set(names))


v210.v297._safe_source_files = _safe_source_files_v217
EXECUTOR.safe_source_files_fn = _safe_source_files_v217


def _norm(message):
    return re.sub(r'\s+', ' ', str(message or '')).strip().lower()


def _promotion_id(message):
    match = re.search(r'\b(PRO-[A-Fa-f0-9]{10})\b', str(message or ''), flags=re.I)
    return match.group(1).upper() if match else None


def _merge_id(message):
    match = re.search(r'\b(MRG-[A-Fa-f0-9]{10})\b', str(message or ''), flags=re.I)
    return match.group(1).upper() if match else None


def _approval_code(message):
    match = re.search(r'\bcode\s+([A-Fa-f0-9]{6})\b', str(message or ''), flags=re.I)
    return match.group(1).upper() if match else None


def merge_status_request(message):
    return _norm(message) in {
        'show maintenance merge gate',
        'show merge gate',
        'maintenance merge gate',
        'maintenance merge status',
        'show maintenance merge status',
    }


def prepare_merge_request(message):
    return bool(re.search(r'\bprepare\s+(?:the\s+)?maintenance\s+merge\b', _norm(message)))


def approve_merge_request(message):
    return bool(re.search(r'\bapprove\s+(?:the\s+)?maintenance\s+merge\b', _norm(message)))


def execute_merge_request(message):
    text = _norm(message)
    return bool(
        re.search(r'\bexecute\s+(?:the\s+)?(?:approved\s+)?maintenance\s+merge\b', text)
        or re.search(r'\bmerge\s+(?:the\s+)?approved\s+maintenance\s+pull\s+request\b', text)
    )


def cancel_merge_request(message):
    return bool(re.search(r'\bcancel\s+(?:the\s+)?maintenance\s+merge\b', _norm(message)))


def _yesno(value):
    return 'yes' if bool(value) else 'no'


def _render_merge(record, heading='Maintenance merge'):
    record = dict(record or {})
    lines = [
        f"{heading}: {str(record.get('status') or 'unknown').upper()}",
        f"Merge: {record.get('merge_id') or 'unknown'}",
        f"Promotion: {record.get('promotion_id') or 'unknown'}",
        f"Execution: {record.get('execution_id') or 'unknown'}",
        f"Review: {record.get('review_id') or 'unknown'}",
        f"Pull request: #{record.get('pull_request_number') or 'unknown'}",
        f"Exact reviewed commit: {record.get('proposal_commit_sha') or 'unknown'}",
        f"Base branch: {record.get('base_branch') or 'unknown'}",
        '',
        'Fresh READY review required: yes',
        'Exact PR head/base revalidation required: yes',
        'Render Auto Deploy must be disabled before merge: yes',
        'Fresh human merge approval required: yes',
        f"Human-gated merge performed: {_yesno(record.get('human_gated_merge_performed'))}",
        f"Automatic merge performed: {_yesno(record.get('automatic_merge_performed'))}",
        f"Production deployment performed: {_yesno(record.get('production_deployment_performed'))}",
    ]
    if record.get('merge_commit_sha'):
        lines.append(f"Merge commit: {record.get('merge_commit_sha')}")
    return '\n'.join(lines)


def merge_status_payload():
    items = MERGE_GATE.recent(limit=10)
    status = MERGE_GATE.status()
    lines = [
        'Human-gated maintenance merge status',
        f"Stored merge records: {len(items)}",
        f"GitHub maintenance token present: {'yes' if status.get('github_token_present') else 'no'}",
        'Fresh READY review required before preparation: yes',
        'Exact pull-request identity revalidated before approval: yes',
        'Exact pull-request identity revalidated before merge: yes',
        'Current main must still match the approved base: yes',
        'One-time human merge approval required: yes',
        'Separate execute command required after approval: yes',
        f"Render Auto Deploy confirmed disabled: {'yes' if status.get('render_auto_deploy_confirmed_disabled') else 'no'}",
        'Merge is blocked unless Render Auto Deploy is confirmed disabled: yes',
        'Automatic merge: disabled',
        'Automatic production deployment: disabled',
        'Blind retry after unknown merge outcome: disabled',
    ]
    if items:
        lines.extend(['', 'Recent merge records:'])
        for item in items[:5]:
            lines.append(
                f"- {item.get('merge_id')} · {item.get('promotion_id')} · "
                f"{str(item.get('status') or '').upper()}"
            )
    else:
        lines.extend(['', 'No maintenance merge records have been stored yet.'])
    return base.base_payload(
        'maintenance_merge', '\n'.join(lines), used_tools=['maintenance_merge'], success=True,
    ) | {'maintenance_merge_status': status, 'maintenance_merges': items}


def prepare_merge_payload(promotion_id):
    result = MERGE_GATE.prepare(promotion_id, persist=True)
    if not result.get('success'):
        error = str(result.get('error') or 'merge_prepare_failed')
        reply = f'Maintenance merge could not be prepared for {promotion_id}. Reason: {error}.'
        if error == 'render_auto_deploy_not_confirmed_disabled':
            reply += (
                ' Merge is intentionally blocked until Render Auto Deploy is disabled and '
                'RENDER_AUTO_DEPLOY_DISABLED_CONFIRMED=true is set.'
            )
        return base.base_payload(
            'maintenance_merge', reply,
            used_tools=['maintenance_merge', 'maintenance_review_gate', 'github'], success=False,
        ) | {'maintenance_merge_result': result}

    record = result.get('merge') or {}
    lines = [_render_merge(record, 'Maintenance merge prepared'), '', 'No GitHub merge occurred during preparation.']
    if str(record.get('status') or '') == 'awaiting_approval':
        lines.extend([
            f"Approval code: {record.get('approval_code')}", '',
            'To approve this exact pull request and reviewed commit, send:',
            f"Approve maintenance merge {record.get('merge_id')} code {record.get('approval_code')}",
        ])
    return base.base_payload(
        'maintenance_merge', '\n'.join(lines),
        used_tools=['maintenance_merge', 'maintenance_review_gate', 'github'], success=True,
    ) | {'maintenance_merge': record}


def approve_merge_payload(merge_id, approval_code):
    result = MERGE_GATE.approve(merge_id, approval_code)
    if not result.get('success'):
        return base.base_payload(
            'maintenance_merge',
            f"Maintenance merge {merge_id} was not approved. Reason: {result.get('error') or 'merge_approval_failed'}.",
            used_tools=['maintenance_merge', 'maintenance_review_gate', 'github'], success=False,
        ) | {'maintenance_merge_result': result}
    record = result.get('merge') or {}
    lines = [
        _render_merge(record, 'Maintenance merge approval'), '',
        f"Approval expires: {record.get('approval_expires_at') or 'unknown'}",
        'No GitHub merge occurred during approval.', '',
        'To merge the exact approved pull request, send:',
        f"Execute approved maintenance merge {record.get('merge_id')}",
    ]
    return base.base_payload(
        'maintenance_merge', '\n'.join(lines),
        used_tools=['maintenance_merge', 'maintenance_review_gate', 'github'], success=True,
    ) | {'maintenance_merge': record}


def execute_merge_payload(merge_id):
    result = MERGE_GATE.execute(merge_id)
    if not result.get('success'):
        error = str(result.get('error') or 'merge_execution_failed')
        reply = f'Maintenance merge {merge_id} was not completed. Reason: {error}.'
        if error == 'render_auto_deploy_not_confirmed_disabled':
            reply += ' Tyler refused to merge because a GitHub merge could still trigger Render production automatically.'
        if error == 'github_merge_outcome_unknown':
            reply += ' Tyler blocked blind retry because the external side-effect outcome is uncertain.'
        return base.base_payload(
            'maintenance_merge', reply,
            used_tools=['maintenance_merge', 'maintenance_review_gate', 'github'], success=False,
        ) | {'maintenance_merge_result': result}

    record = result.get('merge') or {}
    lines = [
        _render_merge(record, 'Maintenance merge'), '',
        'The exact reviewed pull request is confirmed merged.',
        'Production deployment has NOT been performed by this merge action.',
        'The next production step must verify the merge commit is still current main, deploy deliberately, run health checks, and retain a rollback path.',
    ]
    if result.get('existing'):
        lines.append('No duplicate merge was attempted; Tyler reused the already-recorded merge result.')
    return base.base_payload(
        'maintenance_merge', '\n'.join(lines),
        used_tools=['maintenance_merge', 'maintenance_review_gate', 'github'], success=True,
    ) | {'maintenance_merge': record, 'pull_request': result.get('pull_request')}


def cancel_merge_payload(merge_id):
    result = MERGE_GATE.cancel(merge_id)
    if not result.get('success'):
        return base.base_payload(
            'maintenance_merge',
            f"Maintenance merge {merge_id} was not cancelled. Reason: {result.get('error') or 'cancel_failed'}.",
            used_tools=['maintenance_merge'], success=False,
        ) | {'maintenance_merge_result': result}
    record = result.get('merge') or {}
    return base.base_payload(
        'maintenance_merge', _render_merge(record, 'Maintenance merge cancelled'),
        used_tools=['maintenance_merge'], success=True,
    ) | {'maintenance_merge': record}


_PREVIOUS_HANDLE_MESSAGE = v216.handle_message_v216


def handle_message_v217(message):
    promotion_id = _promotion_id(message)
    merge_id = _merge_id(message)
    approval_code = _approval_code(message)

    if merge_status_request(message):
        return merge_status_payload(), 200

    if prepare_merge_request(message):
        if not promotion_id:
            return base.base_payload(
                'maintenance_merge', 'Prepare maintenance merge requires a PRO- promotion identifier.',
                used_tools=['maintenance_merge'], success=False,
            ), 400
        payload = prepare_merge_payload(promotion_id)
        return payload, 200 if payload.get('success') else 409

    if approve_merge_request(message):
        if not merge_id or not approval_code:
            return base.base_payload(
                'maintenance_merge',
                'Approve maintenance merge requires an MRG- merge identifier and a six-character approval code.',
                used_tools=['maintenance_merge'], success=False,
            ), 400
        payload = approve_merge_payload(merge_id, approval_code)
        return payload, 200 if payload.get('success') else 409

    if execute_merge_request(message):
        if not merge_id:
            return base.base_payload(
                'maintenance_merge', 'Execute approved maintenance merge requires an MRG- merge identifier.',
                used_tools=['maintenance_merge'], success=False,
            ), 400
        payload = execute_merge_payload(merge_id)
        return payload, 200 if payload.get('success') else 409

    if cancel_merge_request(message):
        if not merge_id:
            return base.base_payload(
                'maintenance_merge', 'Cancel maintenance merge requires an MRG- merge identifier.',
                used_tools=['maintenance_merge'], success=False,
            ), 400
        payload = cancel_merge_payload(merge_id)
        return payload, 200 if payload.get('success') else 409

    return _PREVIOUS_HANDLE_MESSAGE(message)


base.handle_message = handle_message_v217

_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v217():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' v2.17 adds a human-gated merge layer after v2.16 pull-request promotion. '
          'Tyler requires the exact v2.16 promotion record, a fresh READY review, an open non-draft PR '
          'whose head SHA and branch still match the reviewed proposal, and current main still matching '
          'the approved base. Render Auto Deploy must be explicitly confirmed disabled before merge. '
          'A separate one-time merge approval and separate execute command are required. Unknown merge '
          'outcomes are verified read-only and never blindly retried. Merge never performs production deployment.'
    )


def project_reply_v217():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nHuman-gated maintenance merge:'
        + '\n- Requires a v2.16-created exact pull request'
        + '\n- Requires a fresh v2.15 READY review before merge preparation, approval, and execution'
        + '\n- Revalidates PR head branch, exact head SHA, base branch, and open/non-draft state'
        + '\n- Requires Render Auto Deploy to be explicitly confirmed disabled before any merge'
        + '\n- Requires a new one-time human merge approval and separate execute command'
        + '\n- Blocks blind retries after uncertain merge outcomes'
        + '\n- Keeps production deployment as a separate action with health verification and rollback planning'
    )


base.core_project_text = core_project_text_v217
base.project_reply = project_reply_v217

_PREVIOUS_STATUS_VIEW = app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = app.view_functions.get('health')


def status_v217():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'human_gated_maintenance_merge',
        'fresh_ready_review_before_merge',
        'exact_pr_identity_before_merge',
        'render_auto_deploy_merge_guard',
        'unknown_merge_outcome_retry_block',
        'separate_production_deployment_after_merge',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    tools = data.setdefault('tools', [])
    if 'maintenance_merge' not in tools:
        tools.append('maintenance_merge')
    data['maintenance_merge'] = MERGE_GATE.status()
    return base.jsonify(data)


def health_v217():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


if _PREVIOUS_STATUS_VIEW is not None:
    app.view_functions['status'] = status_v217
if _PREVIOUS_HEALTH_VIEW is not None:
    app.view_functions['health'] = health_v217


if 'maintenance_merge_diagnostics_api' not in app.view_functions:
    @app.route('/diagnostics/maintenance/merge', methods=['GET'])
    def maintenance_merge_diagnostics_api():
        if not (base.authorized() or base.ui_logged_in()):
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return base.jsonify({
            'success': True,
            'version': base.VERSION,
            'version_short': base.VERSION_SHORT,
            'maintenance_merge': MERGE_GATE.status(),
            'merges': MERGE_GATE.recent(limit=50),
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
