import os
import re

import app_v2_11 as v211
from proactive_operations import (
    INCIDENT_CATEGORY,
    OPS_PREFERENCE_CATEGORY,
    ProactiveOperations,
)


# v2.12 turns health intelligence into controlled proactive operations:
# automatic diagnostics + incident recording + prepared recommendations, with
# optional explicitly opted-in critical email notifications. It never performs
# automatic production remediation or retries uncertain side effects.
v211.base.VERSION = '2.12.0-proactive-operations'
v211.base.VERSION_SHORT = 'v2.12.0'

base = v211.base
app = v211.app
ENGINE = v211.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
v2102 = v211.v2102
v210 = v211.v210
DEPENDENCIES = v211.DEPENDENCIES
HISTORY = v211.HISTORY
INTELLIGENCE = v211.INTELLIGENCE

PROACTIVE_OPS_TIMEOUT_SECONDS = int(os.environ.get('PROACTIVE_OPS_TIMEOUT_SECONDS', '8'))

# Operational records/preferences are not normal conversational memory.
base.SPECIAL_MEMORY_CATEGORIES.add(INCIDENT_CATEGORY)
base.SPECIAL_MEMORY_CATEGORIES.add(OPS_PREFERENCE_CATEGORY)


OPS = ProactiveOperations(
    intelligence=INTELLIGENCE,
    history=HISTORY,
    snapshot_fn=lambda: v210.dependency_snapshot(include_errors=False),
    supabase_url_fn=lambda: base.SUPABASE_URL,
    headers_fn=base.supabase_headers,
    version_fn=lambda: base.VERSION_SHORT,
    # Adapt the incident engine's explicit recipient-first callback to Tyler's
    # existing send_email_via_n8n(subject, body, to=None) contract.
    email_fn=lambda recipient, subject, body: base.send_email_via_n8n(subject, body, to=recipient),
    default_email_fn=lambda: base.TYLER_DEFAULT_EMAIL,
    timeout_seconds=PROACTIVE_OPS_TIMEOUT_SECONDS,
)


# Include proactive operations in verified self-source grounding.
_ORIGINAL_SAFE_SOURCE_FILES = v210.v297._safe_source_files


def _safe_source_files_v212():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    if 'proactive_operations.py' not in names:
        names.append('proactive_operations.py')
    return sorted(set(names))


v210.v297._safe_source_files = _safe_source_files_v212


def _norm(message):
    return re.sub(r'\s+', ' ', str(message or '')).strip().lower()


def proactive_status_request(message):
    text = _norm(message)
    return bool(
        re.search(r'\b(?:show|check|list|display)\s+(?:proactive\s+)?(?:operations|incidents?)\b', text)
        or text in {'proactive operations', 'operational incidents', 'incidents'}
    )


def proactive_email_preference(message):
    text = _norm(message)
    if re.search(r'\b(?:enable|turn on)\s+proactive\s+(?:health\s+|alert\s+)?emails?\b', text):
        return True
    if re.search(r'\b(?:disable|turn off)\s+proactive\s+(?:health\s+|alert\s+)?emails?\b', text):
        return False
    return None


def incident_id_request(message):
    match = re.search(r'\b(INC-[A-Fa-f0-9]{10})\b', str(message or ''))
    return match.group(1).upper() if match else None


def _append_ops_results(payload, results):
    if not isinstance(payload, dict) or not results:
        return payload
    output = dict(payload)
    lines = []
    compact = []
    for result in results:
        incident = dict(result.get('incident') or {})
        if not incident:
            continue
        item = {
            'incident_id': incident.get('incident_id'),
            'status': incident.get('status'),
            'event': incident.get('event'),
            'service': incident.get('service'),
            'severity': incident.get('severity'),
            'title': incident.get('title'),
            'saved': bool(result.get('saved')),
            'notification': result.get('notification') or {},
            'recommended_response': incident.get('recommended_response') or {},
        }
        compact.append(item)
        if incident.get('event') == 'resolved':
            lines.append(
                f"Operational incident {incident.get('incident_id')} marked resolved. "
                'No automatic production changes were made.'
            )
        else:
            recommendation = incident.get('recommended_response') or {}
            lines.append(
                f"Operational incident {incident.get('incident_id')} opened/updated. "
                f"Tyler captured diagnostics and prepared: {recommendation.get('summary') or 'a recommended response.'}"
            )
        notification = result.get('notification') or {}
        if notification.get('sent'):
            lines.append('A proactive alert email was sent with a confirmed Gmail receipt.')
    if lines:
        reply = str(output.get('reply') or '').rstrip()
        notice = '\n'.join(lines)
        output['reply'] = f'{reply}\n\n{notice}' if reply else notice
    output['proactive_operations'] = compact
    used_tools = list(output.get('used_tools') or [])
    if compact and 'proactive_operations' not in used_tools:
        used_tools.append('proactive_operations')
    output['used_tools'] = used_tools
    return output


def _render_incident(item):
    item = dict(item or {})
    recommendation = item.get('recommended_response') or {}
    return '\n'.join([
        f"{item.get('incident_id')} · {str(item.get('status') or 'unknown').upper()} · {str(item.get('severity') or 'warning').upper()}",
        f"Service: {item.get('service') or 'unknown'}",
        f"Issue: {item.get('title') or 'Operational issue'}",
        f"Recommendation: {recommendation.get('summary') or 'No recommendation available.'}",
        'Automatic remediation performed: no',
    ])


def proactive_status_payload():
    incidents = OPS.recent_incidents(limit=10)
    open_incidents = [item for item in incidents if item.get('status') == 'open']
    status = OPS.status()
    lines = [
        'Proactive operations status',
        f"Open incidents: {len(open_incidents)}",
        f"Proactive alert emails: {'enabled' if status.get('email_notifications_enabled') else 'disabled'}",
        'Automatic production remediation: disabled',
        'Active dependency probes: disabled',
    ]
    if incidents:
        lines.extend(['', 'Recent incidents:'])
        for item in incidents[:5]:
            lines.append(
                f"- {item.get('incident_id')} · {str(item.get('status') or '').upper()} · "
                f"{str(item.get('severity') or '').upper()} · {item.get('title') or 'Operational issue'}"
            )
    else:
        lines.extend(['', 'No operational incidents have been recorded yet.'])
    return base.base_payload(
        'proactive_operations',
        '\n'.join(lines),
        used_tools=['proactive_operations'],
        success=True,
    ) | {
        'proactive_operations_status': status,
        'incidents': incidents,
    }


def incident_payload(incident_id):
    incident = OPS.incident(incident_id)
    if not incident:
        return base.base_payload(
            'operational_incident',
            f'Incident {incident_id} was not found.',
            used_tools=['proactive_operations'],
            success=False,
        ) | {'incident': None}
    return base.base_payload(
        'operational_incident',
        _render_incident(incident),
        used_tools=['proactive_operations'],
        success=True,
    ) | {'incident': incident}


def proactive_email_preference_payload(enabled):
    result = OPS.set_email_notifications(enabled)
    if not result.get('saved'):
        return base.base_payload(
            'proactive_operations_preference',
            'I could not persist the proactive email preference. No notification setting was changed.',
            used_tools=['proactive_operations'],
            success=False,
        ) | {'preference_result': result}
    if enabled:
        reply = (
            'Proactive alert emails are enabled. Tyler may email you for newly raised critical incidents '
            'when n8n is healthy. n8n incidents/unknown outcomes will never trigger an automatic n8n email, '
            'and Tyler will not perform automatic remediation.'
        )
    else:
        reply = 'Proactive alert emails are disabled. In-app incident detection and diagnostics remain enabled.'
    return base.base_payload(
        'proactive_operations_preference',
        reply,
        used_tools=['proactive_operations'],
        success=True,
    ) | {'preference_result': result}


# Bypass v2.11's outer handle wrapper so v2.12 can process the exact same health
# events into incidents before they are appended to the conversational response.
_PRE_HEALTH_HANDLE_MESSAGE = v211._PREVIOUS_HANDLE_MESSAGE


def handle_message_v212(message):
    preference = proactive_email_preference(message)
    if preference is not None:
        return proactive_email_preference_payload(preference), 200

    requested_incident = incident_id_request(message)
    if requested_incident and any(term in _norm(message) for term in ['show', 'open', 'incident', 'details', 'diagnose']):
        payload = incident_payload(requested_incident)
        return payload, 200 if payload.get('success') else 404

    if proactive_status_request(message):
        return proactive_status_payload(), 200

    if v211.health_alert_request(message):
        events = INTELLIGENCE.sync_and_get_events(force_history_refresh=True)
        ops_results = OPS.process_events(events)
        payload = v211.health_alert_payload()
        return _append_ops_results(payload, ops_results), 200

    payload, status = _PRE_HEALTH_HANDLE_MESSAGE(message)

    # Health intelligence + incident creation are diagnostics-only. Any failure
    # leaves the original user response intact.
    try:
        events = INTELLIGENCE.sync_and_get_events(force_history_refresh=False)
        ops_results = OPS.process_events(events)
        payload = v211._append_health_events(payload, events)
        payload = _append_ops_results(payload, ops_results)
    except Exception:
        pass
    return payload, status


base.handle_message = handle_message_v212


# ---------------------------------------------------------------------------
# Project self-description and diagnostics endpoints.
# ---------------------------------------------------------------------------
_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v212():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' Proactive operations converts newly raised/resolved dependency-health events '
          'into persistent operational incidents with safe diagnostic bundles and '
          'deterministic recommended responses. Tyler may send critical incident emails '
          'only after explicit opt-in and only when n8n is healthy; n8n/unknown-outcome '
          'incidents never trigger automatic n8n notification. Production remediation, '
          'deployments, credential changes, and uncertain side-effect retries remain '
          'approval-controlled and are never executed automatically.'
    )


def project_reply_v212():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nProactive operations:'
        + '\n- Automatically creates incident records from meaningful health events'
        + '\n- Captures safe live + historical diagnostics'
        + '\n- Prepares deterministic recommended fixes without depending on the failing service'
        + '\n- Keeps all production remediation and uncertain side-effect retries approval-gated'
        + '\n- Optional critical email alerts require explicit opt-in'
        + '\n- Never emails through n8n when n8n itself is unsafe/unknown'
        + '\n- No active dependency probes'
    )


base.core_project_text = core_project_text_v212
base.project_reply = project_reply_v212


_PREVIOUS_STATUS_VIEW = base.app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = base.app.view_functions.get('health')


def status_v212():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'proactive_operational_incidents',
        'automatic_safe_diagnostic_collection',
        'prepared_incident_recommendations',
        'opt_in_critical_email_alerts',
        'approval_gated_remediation',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    tools = data.setdefault('tools', [])
    if 'proactive_operations' not in tools:
        tools.append('proactive_operations')
    data['proactive_operations'] = OPS.status()
    return base.jsonify(data)


def health_v212():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


base.app.view_functions['status'] = status_v212
base.app.view_functions['health'] = health_v212


if 'operational_incident_diagnostics_api' not in base.app.view_functions:
    @base.app.route('/diagnostics/incidents', methods=['GET'])
    def operational_incident_diagnostics_api():
        if not (base.authorized() or base.ui_logged_in()):
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        status_filter = str(base.request.args.get('status', '') or '').strip().lower() or None
        if status_filter not in {None, 'open', 'resolved'}:
            status_filter = None
        incidents = OPS.recent_incidents(limit=50, status=status_filter)
        return base.jsonify({
            'success': True,
            'version': base.VERSION,
            'version_short': base.VERSION_SHORT,
            'proactive_operations': OPS.status(),
            'incidents': incidents,
        })


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
