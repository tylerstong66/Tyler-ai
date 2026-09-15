import os
import re
from pathlib import Path

import app_v2_12_1 as v2121
from maintenance_planner import MAINTENANCE_PLAN_CATEGORY, MaintenancePlanner


# v2.13 adds a deterministic, source-grounded autonomous maintenance planner.
# It may prepare and persist a complete maintenance plan, but never edits code,
# changes production configuration, deploys, rotates credentials, or retries an
# uncertain external side effect without explicit approval.
v2121.base.VERSION = '2.13.0-autonomous-maintenance-planner'
v2121.base.VERSION_SHORT = 'v2.13.0'

base = v2121.base
app = v2121.app
ENGINE = v2121.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
OPS = v2121.OPS
v212 = v2121.v212
v210 = v212.v210

MAINTENANCE_TIMEOUT_SECONDS = int(os.environ.get('MAINTENANCE_TIMEOUT_SECONDS', '8'))
base.SPECIAL_MEMORY_CATEGORIES.add(MAINTENANCE_PLAN_CATEGORY)

PLANNER = MaintenancePlanner(
    incident_loader=OPS.incident,
    safe_source_files_fn=v210.v297._safe_source_files,
    supabase_url_fn=lambda: base.SUPABASE_URL,
    headers_fn=base.supabase_headers,
    version_fn=lambda: base.VERSION_SHORT,
    source_root=Path(__file__).resolve().parent,
    timeout_seconds=MAINTENANCE_TIMEOUT_SECONDS,
)


# Include the planner in future verified Tyler Developer grounding.
_ORIGINAL_SAFE_SOURCE_FILES = v210.v297._safe_source_files


def _safe_source_files_v213():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    if 'maintenance_planner.py' not in names:
        names.append('maintenance_planner.py')
    return sorted(set(names))


v210.v297._safe_source_files = _safe_source_files_v213
PLANNER.safe_source_files_fn = _safe_source_files_v213


def _norm(message):
    return re.sub(r'\s+', ' ', str(message or '')).strip().lower()


def _extract_identifier(message):
    match = re.search(r'\b((?:INC|MNT)-[A-Fa-f0-9]{10})\b', str(message or ''))
    return match.group(1).upper() if match else None


def maintenance_status_request(message):
    text = _norm(message)
    return text in {
        'show maintenance planner',
        'show maintenance status',
        'show maintenance plans',
        'list maintenance plans',
        'maintenance planner',
        'maintenance plans',
    }


def prepare_plan_request(message):
    text = _norm(message)
    return bool(re.search(r'\b(?:prepare|build|create|generate)\s+(?:a\s+)?maintenance\s+plan\b', text))


def show_plan_request(message):
    text = _norm(message)
    return bool(re.search(r'\b(?:show|open|display|review)\s+(?:the\s+)?maintenance\s+plan\b', text))


def _render_plan(plan):
    plan = dict(plan or {})
    patch = dict(plan.get('proposed_patch') or {})
    affected = plan.get('affected_code') or []
    files = [item.get('file') for item in affected if item.get('file')]
    lines = [
        f"Maintenance plan {plan.get('maintenance_plan_id')}",
        f"Incident: {plan.get('incident_id')}",
        f"Service: {plan.get('service') or 'unknown'}",
        f"Severity: {str(plan.get('severity') or 'unknown').upper()}",
        f"Status: {str(plan.get('status') or 'prepared').upper()}",
        '',
        'Likely cause:',
        str(plan.get('likely_cause') or 'Not yet verified.'),
        '',
        'Verified affected source:',
        ', '.join(files) if files else 'No relevant deployed source file was verified.',
        '',
        'Proposed patch strategy:',
        str(patch.get('strategy') or 'No patch strategy available.'),
    ]
    changes = patch.get('changes') or []
    if changes:
        lines.extend(['', 'Proposed changes:'])
        lines.extend([f'- {item}' for item in changes])
    tests = plan.get('test_plan') or []
    if tests:
        lines.extend(['', 'Test plan:'])
        lines.extend([f'- {item}' for item in tests])
    rollback = plan.get('rollback_plan') or []
    if rollback:
        lines.extend(['', 'Rollback plan:'])
        lines.extend([f'- {item}' for item in rollback])
    deployment = plan.get('deployment_plan') or []
    if deployment:
        lines.extend(['', 'Deployment plan:'])
        lines.extend([f'- {item}' for item in deployment])
    lines.extend([
        '',
        'Execution status: PREPARED ONLY',
        'Code changed automatically: no',
        'Production deployed automatically: no',
        'Approval required before execution: yes',
    ])
    return '\n'.join(lines)


def maintenance_status_payload():
    plans = PLANNER.recent_plans(limit=10)
    status = PLANNER.status()
    lines = [
        'Autonomous maintenance planner status',
        f"Prepared plans stored: {len(plans)}",
        'Automatic code changes: disabled',
        'Automatic deployments: disabled',
        'Automatic configuration changes: disabled',
        'Approval required before execution: yes',
    ]
    if plans:
        lines.extend(['', 'Recent maintenance plans:'])
        for item in plans[:5]:
            lines.append(
                f"- {item.get('maintenance_plan_id')} · {item.get('incident_id')} · "
                f"{str(item.get('service') or '').upper()} · {str(item.get('status') or '').upper()}"
            )
    else:
        lines.extend(['', 'No maintenance plans have been prepared yet.'])
    return base.base_payload(
        'maintenance_planner',
        '\n'.join(lines),
        used_tools=['maintenance_planner'],
        success=True,
    ) | {
        'maintenance_planner_status': status,
        'maintenance_plans': plans,
    }


def prepare_plan_payload(incident_id):
    result = PLANNER.prepare_for_incident(incident_id, persist=True)
    if not result.get('success'):
        error = result.get('error') or 'unable_to_prepare_plan'
        return base.base_payload(
            'maintenance_plan',
            f'I could not prepare a maintenance plan for {incident_id}. Reason: {error}.',
            used_tools=['maintenance_planner'],
            success=False,
        ) | {'maintenance_plan_result': result}
    plan = result.get('plan') or {}
    reply = _render_plan(plan)
    if not result.get('saved'):
        reply += '\n\nPersistence warning: the plan was prepared in memory but could not be confirmed saved to Supabase.'
    return base.base_payload(
        'maintenance_plan',
        reply,
        used_tools=['maintenance_planner'],
        success=True,
    ) | {'maintenance_plan': plan, 'maintenance_plan_saved': bool(result.get('saved'))}


def show_plan_payload(identifier):
    plan = PLANNER.plan(identifier)
    if not plan:
        return base.base_payload(
            'maintenance_plan',
            f'Maintenance plan for {identifier} was not found.',
            used_tools=['maintenance_planner'],
            success=False,
        ) | {'maintenance_plan': None}
    return base.base_payload(
        'maintenance_plan',
        _render_plan(plan),
        used_tools=['maintenance_planner'],
        success=True,
    ) | {'maintenance_plan': plan}


def _append_auto_plans(payload):
    if not isinstance(payload, dict):
        return payload
    ops_items = list(payload.get('proactive_operations') or [])
    if not ops_items:
        return payload

    output = dict(payload)
    prepared = []
    notices = []
    for item in ops_items:
        if item.get('status') != 'open' or item.get('event') not in {'raised', 'updated'}:
            continue
        incident_id = str(item.get('incident_id') or '').upper()
        if not incident_id:
            continue
        try:
            existing = PLANNER.plan(incident_id)
            if existing:
                plan = existing
                saved = True
            else:
                result = PLANNER.prepare_for_incident(incident_id, persist=True)
                if not result.get('success'):
                    continue
                plan = result.get('plan') or {}
                saved = bool(result.get('saved'))
        except Exception:
            continue
        prepared.append({
            'maintenance_plan_id': plan.get('maintenance_plan_id'),
            'incident_id': plan.get('incident_id'),
            'service': plan.get('service'),
            'saved': saved,
            'approval_required_before_execution': True,
        })
        notices.append(
            f"Maintenance plan {plan.get('maintenance_plan_id')} prepared for {incident_id}. "
            'No code, configuration, deployment, or side-effect retry was executed.'
        )

    if prepared:
        reply = str(output.get('reply') or '').rstrip()
        notice = '\n'.join(notices)
        output['reply'] = f'{reply}\n\n{notice}' if reply else notice
        output['maintenance_plans_prepared'] = prepared
        used_tools = list(output.get('used_tools') or [])
        if 'maintenance_planner' not in used_tools:
            used_tools.append('maintenance_planner')
        output['used_tools'] = used_tools
    return output


_PREVIOUS_HANDLE_MESSAGE = v2121.handle_message_v2121


def handle_message_v213(message):
    identifier = _extract_identifier(message)

    if maintenance_status_request(message):
        return maintenance_status_payload(), 200

    if identifier and prepare_plan_request(message):
        if not identifier.startswith('INC-'):
            return base.base_payload(
                'maintenance_plan',
                'Prepare maintenance plan expects an INC- incident identifier.',
                used_tools=['maintenance_planner'],
                success=False,
            ), 400
        payload = prepare_plan_payload(identifier)
        return payload, 200 if payload.get('success') else 404

    if identifier and show_plan_request(message):
        payload = show_plan_payload(identifier)
        return payload, 200 if payload.get('success') else 404

    payload, status = _PREVIOUS_HANDLE_MESSAGE(message)
    try:
        payload = _append_auto_plans(payload)
    except Exception:
        pass
    return payload, status


base.handle_message = handle_message_v213


# Keep Tyler's project identity/source grounding current.
_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v213():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' The autonomous maintenance planner converts real open operational incidents '
          'into deterministic source-grounded maintenance plans containing a likely-cause '
          'analysis, verified affected code, proposed patch strategy, regression tests, '
          'rollback steps, and deployment steps. Plans are preparation only: Tyler does '
          'not automatically edit code, change production configuration, deploy, rotate '
          'credentials, or retry uncertain side effects.'
    )


def project_reply_v213():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nAutonomous maintenance planner:'
        + '\n- Automatically prepares plans for real open operational incidents'
        + '\n- Uses verified deployed source files to identify affected code'
        + '\n- Includes likely cause, proposed patch strategy, tests, rollback, and deployment steps'
        + '\n- Works deterministically even if Groq is the failing dependency'
        + '\n- Never edits/deploys production or retries uncertain side effects automatically'
        + '\n- Explicit approval is required before execution'
    )


base.core_project_text = core_project_text_v213
base.project_reply = project_reply_v213


_PREVIOUS_STATUS_VIEW = base.app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = base.app.view_functions.get('health')


def status_v213():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'autonomous_maintenance_planning',
        'source_grounded_incident_plans',
        'maintenance_test_plans',
        'maintenance_rollback_plans',
        'approval_gated_maintenance_execution',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    tools = data.setdefault('tools', [])
    if 'maintenance_planner' not in tools:
        tools.append('maintenance_planner')
    data['maintenance_planner'] = PLANNER.status()
    return base.jsonify(data)


def health_v213():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


base.app.view_functions['status'] = status_v213
base.app.view_functions['health'] = health_v213


if 'maintenance_diagnostics_api' not in base.app.view_functions:
    @base.app.route('/diagnostics/maintenance', methods=['GET'])
    def maintenance_diagnostics_api():
        if not (base.authorized() or base.ui_logged_in()):
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return base.jsonify({
            'success': True,
            'version': base.VERSION,
            'version_short': base.VERSION_SHORT,
            'maintenance_planner': PLANNER.status(),
            'plans': PLANNER.recent_plans(limit=50),
        })


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
