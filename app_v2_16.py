import os
import re

import app_v2_15 as v215
from maintenance_promotion import (
    MAINTENANCE_PROMOTION_CATEGORY,
    MaintenancePromotionCoordinator,
)


# v2.16 adds a human-gated promotion layer after v2.15's READY review gate.
# A fresh READY review is required to prepare a promotion, a separate one-time
# approval is required, and a separate execute command is required before a PR
# can be created. v2.16 never merges, writes directly to main, or deploys.
v215.base.VERSION = '2.16.0-human-gated-pull-request-promotion'
v215.base.VERSION_SHORT = 'v2.16.0'

base = v215.base
app = v215.app
ENGINE = v215.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v215.EXECUTOR
DRILL_EXECUTOR = v215.DRILL_EXECUTOR
PLANNER = v215.PLANNER
OPS = v215.OPS
REVIEW_GATE = v215.REVIEW_GATE
v210 = v215.v210
base.SPECIAL_MEMORY_CATEGORIES.add(MAINTENANCE_PROMOTION_CATEGORY)


PROMOTION = MaintenancePromotionCoordinator(
    review_gate=REVIEW_GATE,
    supabase_url_fn=lambda: base.SUPABASE_URL,
    headers_fn=base.supabase_headers,
    version_fn=lambda: base.VERSION_SHORT,
    github_token_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_TOKEN', ''),
    github_repository_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_REPOSITORY', 'tylerstong66/Tyler-ai'),
    github_base_branch_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_BASE_BRANCH', 'main'),
    timeout_seconds=int(os.environ.get('MAINTENANCE_PROMOTION_TIMEOUT_SECONDS', '10')),
    approval_ttl_minutes=int(os.environ.get('MAINTENANCE_PROMOTION_APPROVAL_TTL_MINUTES', '30')),
)


_ORIGINAL_SAFE_SOURCE_FILES = v210.v297._safe_source_files


def _safe_source_files_v216():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    for name in ['maintenance_promotion.py', 'app_v2_16.py']:
        if name not in names:
            names.append(name)
    return sorted(set(names))


v210.v297._safe_source_files = _safe_source_files_v216
EXECUTOR.safe_source_files_fn = _safe_source_files_v216


def _norm(message):
    return re.sub(r'\s+', ' ', str(message or '')).strip().lower()


def _execution_id(message):
    match = re.search(r'\b(EXE-[A-Fa-f0-9]{10})\b', str(message or ''), flags=re.I)
    return match.group(1).upper() if match else None


def _promotion_id(message):
    match = re.search(r'\b(PRO-[A-Fa-f0-9]{10})\b', str(message or ''), flags=re.I)
    return match.group(1).upper() if match else None


def _approval_code(message):
    match = re.search(r'\bcode\s+([A-Fa-f0-9]{6})\b', str(message or ''), flags=re.I)
    return match.group(1).upper() if match else None


def promotion_status_request(message):
    return _norm(message) in {
        'show maintenance promotion gate',
        'show promotion gate',
        'maintenance promotion gate',
        'maintenance promotion status',
        'show maintenance promotion status',
    }


def prepare_promotion_request(message):
    text = _norm(message)
    return bool(
        re.search(r'\bprepare\s+(?:the\s+)?maintenance\s+promotion\b', text)
        or re.search(r'\bprepare\s+(?:the\s+)?pull\s+request\s+promotion\b', text)
    )


def approve_promotion_request(message):
    return bool(re.search(r'\bapprove\s+(?:the\s+)?maintenance\s+promotion\b', _norm(message)))


def execute_promotion_request(message):
    text = _norm(message)
    return bool(
        re.search(r'\bexecute\s+(?:the\s+)?(?:approved\s+)?maintenance\s+promotion\b', text)
        or re.search(r'\bcreate\s+(?:the\s+)?approved\s+maintenance\s+pull\s+request\b', text)
    )


def cancel_promotion_request(message):
    return bool(re.search(r'\bcancel\s+(?:the\s+)?maintenance\s+promotion\b', _norm(message)))


def _yesno(value):
    return 'yes' if bool(value) else 'no'


def _render_promotion(promotion, heading='Maintenance promotion'):
    promotion = dict(promotion or {})
    lines = [
        f"{heading}: {str(promotion.get('status') or 'unknown').upper()}",
        f"Promotion: {promotion.get('promotion_id') or 'unknown'}",
        f"Execution: {promotion.get('execution_id') or 'unknown'}",
        f"Review: {promotion.get('review_id') or 'unknown'}",
        f"Review branch: {promotion.get('review_branch') or 'unknown'}",
        f"Exact reviewed commit: {promotion.get('proposal_commit_sha') or 'unknown'}",
        f"Base branch: {promotion.get('base_branch') or 'unknown'}",
        '',
        'Fresh READY review required: yes',
        'Fresh human approval required: yes',
        f"Pull request created: {_yesno(promotion.get('pull_request_created'))}",
        f"Automatic merge performed: {_yesno(promotion.get('automatic_merge_performed'))}",
        f"Direct write to main performed: {_yesno(promotion.get('direct_main_write_performed'))}",
        f"Production deployment performed: {_yesno(promotion.get('production_deployment_performed'))}",
    ]
    if promotion.get('pull_request_number'):
        lines.append(f"Pull request: #{promotion.get('pull_request_number')}")
    if promotion.get('pull_request_url'):
        lines.append(f"Pull request URL: {promotion.get('pull_request_url')}")
    return '\n'.join(lines)


def promotion_status_payload():
    items = PROMOTION.recent(limit=10)
    status = PROMOTION.status()
    lines = [
        'Human-gated maintenance promotion status',
        f"Stored promotion records: {len(items)}",
        f"GitHub maintenance token present: {'yes' if status.get('github_token_present') else 'no'}",
        'Fresh READY review required before preparation: yes',
        'Fresh READY review revalidation before approval: yes',
        'Fresh READY review revalidation before PR creation: yes',
        'One-time human approval required: yes',
        'Separate execute command required after approval: yes',
        'Pull Requests permission verified only when PR creation is attempted: yes',
        'Automatic pull request creation: disabled',
        'Automatic merge: disabled',
        'Direct writes to main: disabled',
        'Automatic production deployment: disabled',
        'Blind retry after unknown PR outcome: disabled',
    ]
    if items:
        lines.extend(['', 'Recent promotion records:'])
        for item in items[:5]:
            lines.append(
                f"- {item.get('promotion_id')} · {item.get('execution_id')} · "
                f"{str(item.get('status') or '').upper()}"
            )
    else:
        lines.extend(['', 'No maintenance promotion records have been stored yet.'])
    return base.base_payload(
        'maintenance_promotion',
        '\n'.join(lines),
        used_tools=['maintenance_promotion'],
        success=True,
    ) | {'maintenance_promotion_status': status, 'maintenance_promotions': items}


def prepare_promotion_payload(execution_id):
    result = PROMOTION.prepare(execution_id, persist=True)
    if not result.get('success'):
        error = str(result.get('error') or 'promotion_prepare_failed')
        reply = f'Maintenance promotion could not be prepared for {execution_id}. Reason: {error}.'
        if error.startswith('review_'):
            reply += ' The v2.15 review gate must return READY immediately before promotion preparation.'
        return base.base_payload(
            'maintenance_promotion', reply,
            used_tools=['maintenance_promotion', 'maintenance_review_gate'], success=False,
        ) | {'maintenance_promotion_result': result}

    promotion = result.get('promotion') or {}
    lines = [_render_promotion(promotion, 'Maintenance promotion prepared'), '', 'No GitHub write occurred during preparation.']
    if str(promotion.get('status') or '') == 'awaiting_approval':
        lines.extend([
            f"Approval code: {promotion.get('approval_code')}", '',
            'To approve this exact reviewed commit, send:',
            f"Approve maintenance promotion {promotion.get('promotion_id')} code {promotion.get('approval_code')}",
        ])
    return base.base_payload(
        'maintenance_promotion', '\n'.join(lines),
        used_tools=['maintenance_promotion', 'maintenance_review_gate'], success=True,
    ) | {'maintenance_promotion': promotion}


def approve_promotion_payload(promotion_id, approval_code):
    result = PROMOTION.approve(promotion_id, approval_code)
    if not result.get('success'):
        error = str(result.get('error') or 'promotion_approval_failed')
        return base.base_payload(
            'maintenance_promotion',
            f'Maintenance promotion {promotion_id} was not approved. Reason: {error}.',
            used_tools=['maintenance_promotion', 'maintenance_review_gate'], success=False,
        ) | {'maintenance_promotion_result': result}

    promotion = result.get('promotion') or {}
    lines = [
        _render_promotion(promotion, 'Maintenance promotion approval'), '',
        f"Approval expires: {promotion.get('approval_expires_at') or 'unknown'}",
        'No GitHub write occurred during approval.', '',
        'To create the pull request, send:',
        f"Execute approved maintenance promotion {promotion.get('promotion_id')}",
    ]
    return base.base_payload(
        'maintenance_promotion', '\n'.join(lines),
        used_tools=['maintenance_promotion', 'maintenance_review_gate'], success=True,
    ) | {'maintenance_promotion': promotion}


def execute_promotion_payload(promotion_id):
    result = PROMOTION.execute(promotion_id)
    if not result.get('success'):
        error = str(result.get('error') or 'promotion_execution_failed')
        reply = f'Maintenance promotion {promotion_id} did not create a pull request. Reason: {error}.'
        if error == 'github_pull_request_permission_denied':
            reply += (
                ' The Render GITHUB_MAINTENANCE_TOKEN needs GitHub Pull Requests: Read and write permission. '
                'Do not broaden any other permission.'
            )
        if error == 'github_pr_outcome_unknown':
            reply += ' Tyler blocked any blind retry because the external side-effect outcome is uncertain.'
        return base.base_payload(
            'maintenance_promotion', reply,
            used_tools=['maintenance_promotion', 'maintenance_review_gate', 'github'], success=False,
        ) | {'maintenance_promotion_result': result}

    promotion = result.get('promotion') or {}
    lines = [
        _render_promotion(promotion, 'Maintenance promotion'), '',
        'The pull request is bound in Tyler’s promotion record to the exact reviewed proposal commit.',
        'The pull request has NOT been merged.',
        'Production has NOT been deployed by this promotion.',
        'Any future merge step must revalidate the pull-request head SHA, base branch, CI, and current main again.',
    ]
    if result.get('existing'):
        lines.append('No duplicate PR was created; Tyler reused the already-recorded promotion result.')
    return base.base_payload(
        'maintenance_promotion', '\n'.join(lines),
        used_tools=['maintenance_promotion', 'maintenance_review_gate', 'github'], success=True,
    ) | {'maintenance_promotion': promotion, 'pull_request': result.get('pull_request')}


def cancel_promotion_payload(promotion_id):
    result = PROMOTION.cancel(promotion_id)
    if not result.get('success'):
        return base.base_payload(
            'maintenance_promotion',
            f"Maintenance promotion {promotion_id} was not cancelled. Reason: {result.get('error') or 'cancel_failed'}.",
            used_tools=['maintenance_promotion'], success=False,
        ) | {'maintenance_promotion_result': result}
    promotion = result.get('promotion') or {}
    return base.base_payload(
        'maintenance_promotion', _render_promotion(promotion, 'Maintenance promotion cancelled'),
        used_tools=['maintenance_promotion'], success=True,
    ) | {'maintenance_promotion': promotion}


_PREVIOUS_HANDLE_MESSAGE = v215.handle_message_v215


def handle_message_v216(message):
    execution_id = _execution_id(message)
    promotion_id = _promotion_id(message)
    approval_code = _approval_code(message)

    if promotion_status_request(message):
        return promotion_status_payload(), 200

    if prepare_promotion_request(message):
        if not execution_id:
            return base.base_payload(
                'maintenance_promotion', 'Prepare maintenance promotion requires an EXE- execution identifier.',
                used_tools=['maintenance_promotion'], success=False,
            ), 400
        payload = prepare_promotion_payload(execution_id)
        return payload, 200 if payload.get('success') else 409

    if approve_promotion_request(message):
        if not promotion_id or not approval_code:
            return base.base_payload(
                'maintenance_promotion',
                'Approve maintenance promotion requires a PRO- promotion identifier and a six-character approval code.',
                used_tools=['maintenance_promotion'], success=False,
            ), 400
        payload = approve_promotion_payload(promotion_id, approval_code)
        return payload, 200 if payload.get('success') else 409

    if execute_promotion_request(message):
        if not promotion_id:
            return base.base_payload(
                'maintenance_promotion', 'Execute approved maintenance promotion requires a PRO- promotion identifier.',
                used_tools=['maintenance_promotion'], success=False,
            ), 400
        payload = execute_promotion_payload(promotion_id)
        return payload, 200 if payload.get('success') else 409

    if cancel_promotion_request(message):
        if not promotion_id:
            return base.base_payload(
                'maintenance_promotion', 'Cancel maintenance promotion requires a PRO- promotion identifier.',
                used_tools=['maintenance_promotion'], success=False,
            ), 400
        payload = cancel_promotion_payload(promotion_id)
        return payload, 200 if payload.get('success') else 409

    return _PREVIOUS_HANDLE_MESSAGE(message)


base.handle_message = handle_message_v216


_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v216():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' v2.16 adds human-gated pull-request promotion after the v2.15 automated review gate. '
          'Tyler requires a fresh READY review to prepare a promotion, a separate one-time human '
          'approval code, and a separate execute command. Before PR creation Tyler reruns the READY '
          'review and requires the exact same review id, execution id, repository, base branch, review '
          'branch, approved base commit, and proposal commit. PR creation is idempotent: Tyler checks '
          'for an existing exact PR first. If a PR creation request has an unknown network outcome, '
          'Tyler performs a read-only verification and blocks blind retry if the result remains unknown. '
          'v2.16 never merges, writes directly to main, or deploys production.'
    )


def project_reply_v216():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nHuman-gated pull-request promotion:'
        + '\n- Requires a fresh v2.15 READY review before promotion preparation'
        + '\n- Requires a new one-time human approval after READY'
        + '\n- Requires a separate execute command after approval'
        + '\n- Revalidates the exact reviewed commit and current main immediately before PR creation'
        + '\n- Checks for an existing exact PR before creating one'
        + '\n- Blocks blind retries after uncertain PR-creation outcomes'
        + '\n- Never merges, writes directly to main, or deploys production'
    )


base.core_project_text = core_project_text_v216
base.project_reply = project_reply_v216


_PREVIOUS_STATUS_VIEW = app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = app.view_functions.get('health')


def status_v216():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'human_gated_maintenance_promotion',
        'fresh_ready_review_before_pr',
        'one_time_promotion_approval',
        'idempotent_pull_request_creation',
        'unknown_pr_outcome_retry_block',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    tools = data.setdefault('tools', [])
    if 'maintenance_promotion' not in tools:
        tools.append('maintenance_promotion')
    data['maintenance_promotion'] = PROMOTION.status()
    return base.jsonify(data)


def health_v216():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


if _PREVIOUS_STATUS_VIEW is not None:
    app.view_functions['status'] = status_v216
if _PREVIOUS_HEALTH_VIEW is not None:
    app.view_functions['health'] = health_v216


if 'maintenance_promotion_diagnostics_api' not in app.view_functions:
    @app.route('/diagnostics/maintenance/promotion', methods=['GET'])
    def maintenance_promotion_diagnostics_api():
        if not (base.authorized() or base.ui_logged_in()):
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return base.jsonify({
            'success': True,
            'version': base.VERSION,
            'version_short': base.VERSION_SHORT,
            'maintenance_promotion': PROMOTION.status(),
            'promotions': PROMOTION.recent(limit=50),
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
