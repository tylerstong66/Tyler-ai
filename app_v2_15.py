import os
import re

import app_v2_14_1 as v2141
from maintenance_review_gate import (
    MAINTENANCE_REVIEW_CATEGORY,
    MaintenanceReviewGate,
)


# v2.15 adds a read-only automated review and test gate after v2.14's
# approval-gated review-branch publisher. It verifies exact provenance, diff
# scope, source safety, current-base freshness, and dedicated CI. It never
# merges, creates a PR, mutates a branch, or deploys production.
v2141.base.VERSION = '2.15.0-automated-review-and-test-gate'
v2141.base.VERSION_SHORT = 'v2.15.0'

base = v2141.base
app = v2141.app
ENGINE = v2141.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v2141.EXECUTOR
DRILL_EXECUTOR = v2141.DRILL_EXECUTOR
PLANNER = v2141.PLANNER
OPS = v2141.OPS
v210 = v2141.v210
base.SPECIAL_MEMORY_CATEGORIES.add(MAINTENANCE_REVIEW_CATEGORY)


def _execution_loader(execution_id):
    target = str(execution_id or '').upper()
    package = EXECUTOR.execution(target)
    if package:
        return package
    return DRILL_EXECUTOR.execution(target)


REVIEW_GATE = MaintenanceReviewGate(
    execution_loader=_execution_loader,
    supabase_url_fn=lambda: base.SUPABASE_URL,
    headers_fn=base.supabase_headers,
    version_fn=lambda: base.VERSION_SHORT,
    github_token_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_TOKEN', ''),
    github_repository_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_REPOSITORY', 'tylerstong66/Tyler-ai'),
    github_base_branch_fn=lambda: os.environ.get('GITHUB_MAINTENANCE_BASE_BRANCH', 'main'),
    timeout_seconds=int(os.environ.get('MAINTENANCE_REVIEW_TIMEOUT_SECONDS', '10')),
)


# Include the review implementation in future Tyler Developer source grounding.
_ORIGINAL_SAFE_SOURCE_FILES = v210.v297._safe_source_files


def _safe_source_files_v215():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    for name in ['maintenance_review_gate.py', 'app_v2_15.py']:
        if name not in names:
            names.append(name)
    return sorted(set(names))


v210.v297._safe_source_files = _safe_source_files_v215
EXECUTOR.safe_source_files_fn = _safe_source_files_v215


def _norm(message):
    return re.sub(r'\s+', ' ', str(message or '')).strip().lower()


def _execution_id(message):
    match = re.search(r'\b(EXE-[A-Fa-f0-9]{10})\b', str(message or ''), flags=re.I)
    return match.group(1).upper() if match else None


def review_status_request(message):
    return _norm(message) in {
        'show maintenance review gate',
        'show review gate',
        'maintenance review gate',
        'maintenance review status',
        'show maintenance review status',
    }


def review_execution_request(message):
    text = _norm(message)
    return bool(
        re.search(r'\b(?:review|check|evaluate)\s+(?:the\s+)?maintenance\s+(?:execution|review)\b', text)
        or re.search(r'\brun\s+(?:the\s+)?maintenance\s+review\s+gate\b', text)
    )


def _yesno(value):
    return 'yes' if bool(value) else 'no'


def _render_review(review):
    review = dict(review or {})
    checks = dict(review.get('checks') or {})
    ci = dict(review.get('ci') or {})
    reasons = list(review.get('reasons') or [])
    status = str(review.get('gate_status') or 'not_ready').upper()
    lines = [
        f"Maintenance review gate: {status}",
        f"Review: {review.get('review_id') or 'unknown'}",
        f"Execution: {review.get('execution_id') or 'unknown'}",
        f"Review branch: {review.get('review_branch') or 'unknown'}",
        f"Proposal commit: {review.get('proposal_commit_sha') or 'unknown'}",
        '',
        f"Branch points to approved proposal: {_yesno(checks.get('branch_points_to_proposal'))}",
        f"Proposal parent matches approved base: {_yesno(checks.get('proposal_parent_matches_base'))}",
        f"Main still matches approved base: {_yesno(checks.get('main_still_at_review_base'))}",
        f"Exactly one proposal commit: {_yesno(checks.get('single_commit_proposal'))}",
        f"Changed files exactly match approved package: {_yesno(checks.get('exact_diff_scope'))}",
        f"Only existing approved files modified: {_yesno(checks.get('only_existing_files_modified'))}",
        f"Source safety scan passed: {_yesno(checks.get('source_safety_scan_passed'))}",
        f"Dedicated review CI: {str(ci.get('state') or 'not_checked').upper()}",
    ]
    if ci.get('reason'):
        lines.append(f"CI detail: {ci.get('reason')}")
    changed = list(review.get('changed_files') or [])
    if changed:
        lines.append(f"Changed files: {', '.join(changed)}")
    if reasons:
        lines.extend(['', 'Gate blockers:'])
        for reason in reasons:
            lines.append(f'- {reason}')
    lines.extend([
        '',
        'Automatic merge performed: no',
        'Pull request created automatically: no',
        'Review branch mutated by review gate: no',
        'Production deployment performed: no',
    ])
    if status == 'READY':
        lines.extend([
            '',
            'READY means the approved review branch passed Tyler’s automated gate.',
            'No merge or deployment has occurred. Human approval is still required for any future promotion step.',
        ])
    elif status == 'PENDING':
        lines.extend([
            '',
            'PENDING means the structural checks passed but dedicated CI is not finished or not visible yet.',
            f"Run again with: Review maintenance execution {review.get('execution_id')}",
        ])
    else:
        lines.extend([
            '',
            'NOT READY — do not merge or deploy this review branch.',
        ])
    return '\n'.join(lines)


def review_status_payload():
    reports = REVIEW_GATE.recent(limit=10)
    status = REVIEW_GATE.status()
    lines = [
        'Automated maintenance review & test gate status',
        f"Stored terminal review reports: {len(reports)}",
        f"GitHub read path configured: {'yes' if status.get('github_read_configured') else 'no'}",
        'Exact diff-scope verification: enabled',
        'Current-main base verification: enabled',
        'Source secret-safety scan: enabled',
        'Dedicated review CI required: yes',
        'Automatic branch mutation: disabled',
        'Automatic pull request creation: disabled',
        'Automatic merge: disabled',
        'Automatic production deployment: disabled',
    ]
    if reports:
        lines.extend(['', 'Recent terminal review reports:'])
        for item in reports[:5]:
            lines.append(
                f"- {item.get('review_id')} · {item.get('execution_id')} · "
                f"{str(item.get('gate_status') or '').upper()}"
            )
    else:
        lines.extend(['', 'No terminal maintenance review reports have been stored yet.'])
    return base.base_payload(
        'maintenance_review_gate',
        '\n'.join(lines),
        used_tools=['maintenance_review_gate'],
        success=True,
    ) | {'maintenance_review_gate_status': status, 'maintenance_review_reports': reports}


def review_execution_payload(execution_id):
    result = REVIEW_GATE.review(execution_id, persist=True)
    if not result.get('success'):
        error = result.get('error') or 'review_failed'
        reply = f'Maintenance review gate could not review {execution_id}. Reason: {error}.'
        if error == 'execution_not_published_for_review':
            reply += ' The execution must first be published to its isolated review branch.'
        return base.base_payload(
            'maintenance_review_gate',
            reply,
            used_tools=['maintenance_review_gate'],
            success=False,
        ) | {'maintenance_review_result': result}
    review = result.get('review') or {}
    return base.base_payload(
        'maintenance_review_gate',
        _render_review(review),
        used_tools=['maintenance_review_gate'],
        success=True,
    ) | {'maintenance_review': review}


_PREVIOUS_HANDLE_MESSAGE = v2141.handle_message_v2141


def handle_message_v215(message):
    execution_id = _execution_id(message)
    if review_status_request(message):
        return review_status_payload(), 200
    if execution_id and review_execution_request(message):
        payload = review_execution_payload(execution_id)
        if not payload.get('success'):
            return payload, 409
        review = payload.get('maintenance_review') or {}
        return payload, 200 if review.get('gate_status') != 'not_ready' else 409
    if review_execution_request(message) and not execution_id:
        return base.base_payload(
            'maintenance_review_gate',
            'Review maintenance execution requires an EXE- execution identifier.',
            used_tools=['maintenance_review_gate'],
            success=False,
        ), 400
    return _PREVIOUS_HANDLE_MESSAGE(message)


base.handle_message = handle_message_v215


_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v215():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' v2.15 adds a read-only automated maintenance review and test gate. For a published '
          'maintenance review branch, Tyler verifies repository and branch provenance, the exact '
          'approved proposal commit and parent, that main has not advanced since preparation, exact '
          'changed-file scope, modification-only semantics, a source secret-safety scan, and a '
          'dedicated GitHub Actions review workflow. The gate returns READY, PENDING, or NOT READY. '
          'READY never means merged or deployed. The review gate cannot mutate branches, create pull '
          'requests automatically, merge, write to main, or deploy production.'
    )


def project_reply_v215():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nAutomated review & test gate:'
        + '\n- Verifies an approved proposal branch points to the exact approved commit'
        + '\n- Rejects stale review branches when main has advanced since preparation'
        + '\n- Requires the exact approved changed-file set and modification-only scope'
        + '\n- Re-scans changed source for secret-like literals before declaring readiness'
        + '\n- Requires the dedicated v2.15 GitHub Actions review workflow to succeed'
        + '\n- Returns READY, PENDING, or NOT READY without mutating the branch'
        + '\n- Never creates a PR automatically, merges, writes to main, or deploys production'
    )


base.core_project_text = core_project_text_v215
base.project_reply = project_reply_v215


_PREVIOUS_STATUS_VIEW = app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = app.view_functions.get('health')


def status_v215():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'automated_maintenance_review_gate',
        'exact_review_branch_provenance_check',
        'exact_diff_scope_check',
        'review_branch_source_safety_scan',
        'dedicated_review_branch_ci_gate',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    tools = data.setdefault('tools', [])
    if 'maintenance_review_gate' not in tools:
        tools.append('maintenance_review_gate')
    data['maintenance_review_gate'] = REVIEW_GATE.status()
    return base.jsonify(data)


def health_v215():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


if _PREVIOUS_STATUS_VIEW is not None:
    app.view_functions['status'] = status_v215
if _PREVIOUS_HEALTH_VIEW is not None:
    app.view_functions['health'] = health_v215


if 'maintenance_review_gate_diagnostics_api' not in app.view_functions:
    @app.route('/diagnostics/maintenance/review-gate', methods=['GET'])
    def maintenance_review_gate_diagnostics_api():
        if not (base.authorized() or base.ui_logged_in()):
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return base.jsonify({
            'success': True,
            'version': base.VERSION,
            'version_short': base.VERSION_SHORT,
            'maintenance_review_gate': REVIEW_GATE.status(),
            'reviews': REVIEW_GATE.recent(limit=50),
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
