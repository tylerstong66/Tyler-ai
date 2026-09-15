import os
import re

import app_v2_10_2 as v2102
from health_intelligence import (
    ALERT_STATE_CATEGORY,
    HealthIntelligence,
    SERVICE_LABELS,
)


# v2.11 turns passive dependency telemetry + persistent history into
# conservative, explainable health intelligence. It surfaces meaningful alerts
# during normal use without active dependency probes or automatic remediation.
v2102.base.VERSION = '2.11.0-health-intelligence-alerts'
v2102.base.VERSION_SHORT = 'v2.11.0'

base = v2102.base
app = v2102.app
ENGINE = v2102.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
v210 = v2102.v210
DEPENDENCIES = v2102.DEPENDENCIES
HISTORY = v2102.HISTORY

HEALTH_ALERT_HISTORY_HOURS = int(os.environ.get('HEALTH_ALERT_HISTORY_HOURS', '24'))
HEALTH_ALERT_REFRESH_SECONDS = int(os.environ.get('HEALTH_ALERT_REFRESH_SECONDS', '300'))
HEALTH_ALERT_REMINDER_SECONDS = int(os.environ.get('HEALTH_ALERT_REMINDER_SECONDS', '21600'))
HEALTH_ALERT_TIMEOUT_SECONDS = int(os.environ.get('HEALTH_ALERT_TIMEOUT_SECONDS', '8'))


# Alert state is operational telemetry, never ordinary conversational memory.
base.SPECIAL_MEMORY_CATEGORIES.add(ALERT_STATE_CATEGORY)


INTELLIGENCE = HealthIntelligence(
    history=HISTORY,
    snapshot_fn=lambda: v210.dependency_snapshot(include_errors=False),
    supabase_url_fn=lambda: base.SUPABASE_URL,
    headers_fn=base.supabase_headers,
    version_fn=lambda: base.VERSION_SHORT,
    history_hours=HEALTH_ALERT_HISTORY_HOURS,
    history_refresh_seconds=HEALTH_ALERT_REFRESH_SECONDS,
    reminder_seconds=HEALTH_ALERT_REMINDER_SECONDS,
    timeout_seconds=HEALTH_ALERT_TIMEOUT_SECONDS,
)


# Include the intelligence implementation in future verified source grounding.
_ORIGINAL_SAFE_SOURCE_FILES = v210.v297._safe_source_files


def _safe_source_files_v211():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    if 'health_intelligence.py' not in names:
        names.append('health_intelligence.py')
    return sorted(set(names))


v210.v297._safe_source_files = _safe_source_files_v211


def health_alert_request(message):
    text = re.sub(r'\s+', ' ', str(message or '')).strip().lower()
    return bool(
        re.search(r'\b(?:show|check|list|display)\s+(?:system\s+|dependency\s+|service\s+)?(?:health\s+)?alerts?\b', text)
        or re.search(r'\b(?:health|dependency|service)\s+(?:alert|alerts|warnings?)\b', text)
        or text in {'health alerts', 'system alerts', 'dependency alerts'}
    )


def _render_active_alerts(alerts):
    if not alerts:
        return [
            'Health intelligence: no active alerts',
            'No dependency currently meets Tyler AI’s alert thresholds.',
            'Passive telemetry and persisted history remain enabled; no probe requests were sent.',
        ]
    lines = [
        f"Health intelligence: {len(alerts)} active alert{'s' if len(alerts) != 1 else ''}",
        'Based on passive live telemetry plus persisted health history — no probe requests were sent.',
        '',
    ]
    for alert in alerts:
        severity = str(alert.get('severity') or 'warning').upper()
        lines.append(f"{severity} · {alert.get('title')}")
        lines.append(str(alert.get('message') or ''))
    return lines


def health_alert_payload():
    # Synchronize persisted raised/resolved state, then show all currently
    # active issues even if a duplicate conversational notification is muted.
    INTELLIGENCE.sync_and_get_events(force_history_refresh=True)
    alerts = INTELLIGENCE.active_alerts(force_history_refresh=False)
    payload = base.base_payload(
        'dependency_health_alerts',
        '\n'.join(_render_active_alerts(alerts)),
        used_tools=['dependency_health_intelligence'],
        success=True,
    )
    payload['health_alerts'] = alerts
    payload['health_intelligence'] = INTELLIGENCE.status()
    return payload


def _render_events(events):
    lines = []
    for event in events or []:
        alert = event.get('alert') or {}
        event_type = event.get('event')
        if event_type == 'resolved':
            lines.append(f"✓ Health recovery: {alert.get('title')} has cleared.")
            continue
        prefix = '⚠ CRITICAL' if alert.get('severity') == 'critical' else '⚠ Health warning'
        if event_type == 'reminder':
            prefix += ' (still active)'
        lines.append(f"{prefix}: {alert.get('title')}")
        lines.append(str(alert.get('message') or ''))
    return lines


def _append_health_events(payload, events):
    if not isinstance(payload, dict) or not events:
        return payload
    output = dict(payload)
    event_lines = _render_events(events)
    if event_lines:
        reply = str(output.get('reply') or '').rstrip()
        notice = '\n'.join(event_lines)
        output['reply'] = f'{reply}\n\n{notice}' if reply else notice
    output['health_alert_events'] = events
    used_tools = list(output.get('used_tools') or [])
    if 'dependency_health_intelligence' not in used_tools:
        used_tools.append('dependency_health_intelligence')
    output['used_tools'] = used_tools
    return output


_PREVIOUS_HANDLE_MESSAGE = base.handle_message


def handle_message_v211(message):
    if health_alert_request(message):
        return health_alert_payload(), 200

    payload, status = _PREVIOUS_HANDLE_MESSAGE(message)

    # Alert evaluation is diagnostics-only. Any intelligence failure must leave
    # the original user response untouched.
    try:
        events = INTELLIGENCE.sync_and_get_events(force_history_refresh=False)
        payload = _append_health_events(payload, events)
    except Exception:
        pass
    return payload, status


base.handle_message = handle_message_v211


# ---------------------------------------------------------------------------
# Project self-description and diagnostics endpoints.
# ---------------------------------------------------------------------------
_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v211():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' Health intelligence analyzes passive live dependency telemetry and '
          'persisted cross-restart history to detect repeated failures, unhealthy '
          'dependencies, uncertain external side-effect outcomes, reliability '
          'degradation, and meaningful latency regressions. Alerts are explainable, '
          'deduplicated across restarts, and surfaced during normal use. Tyler does '
          'not probe dependencies or automatically retry/remediate side effects in '
          'response to an alert.'
    )


def project_reply_v211():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nHealth intelligence and alerts:'
        + '\n- Detects live degraded/unhealthy dependencies'
        + '\n- Treats unknown side-effect outcomes as critical and never auto-retries them'
        + '\n- Detects cross-restart reliability degradation'
        + '\n- Detects meaningful latency regressions with noise-resistant thresholds'
        + '\n- Deduplicates alerts across Render restarts'
        + '\n- Surfaces one-time recovery notices when issues clear'
        + '\n- No active dependency probes or automatic remediation'
    )


base.core_project_text = core_project_text_v211
base.project_reply = project_reply_v211


_PREVIOUS_STATUS_VIEW = base.app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = base.app.view_functions.get('health')


def status_v211():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'dependency_health_intelligence',
        'deduplicated_health_alerts',
        'health_recovery_notifications',
        'historical_reliability_alerting',
        'latency_regression_alerting',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    tools = data.setdefault('tools', [])
    if 'dependency_health_intelligence' not in tools:
        tools.append('dependency_health_intelligence')
    # Status is intentionally passive: do not trigger a history read here.
    data['health_intelligence'] = INTELLIGENCE.status()
    return base.jsonify(data)


def health_v211():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


base.app.view_functions['status'] = status_v211
base.app.view_functions['health'] = health_v211


if 'dependency_alert_diagnostics_api' not in base.app.view_functions:
    @base.app.route('/diagnostics/dependencies/alerts', methods=['GET'])
    def dependency_alert_diagnostics_api():
        if not (base.authorized() or base.ui_logged_in()):
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        try:
            INTELLIGENCE.sync_and_get_events(force_history_refresh=True)
            alerts = INTELLIGENCE.active_alerts(force_history_refresh=False)
            return base.jsonify({
                'success': True,
                'version': base.VERSION,
                'version_short': base.VERSION_SHORT,
                'health_alerts': alerts,
                'health_intelligence': INTELLIGENCE.status(),
            })
        except Exception:
            return base.jsonify({
                'success': False,
                'error': 'Health intelligence is temporarily unavailable.',
            }), 503


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
