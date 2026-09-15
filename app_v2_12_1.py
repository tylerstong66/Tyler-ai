import re

import app_v2_12 as v212


# v2.12.1 adds an explicit, isolated proactive-operations drill. The drill never
# mutates real dependency health, never changes production configuration, and
# never retries an uncertain side effect.
v212.base.VERSION = '2.12.1-safe-incident-drill'
v212.base.VERSION_SHORT = 'v2.12.1'

base = v212.base
app = v212.app
ENGINE = v212.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
OPS = v212.OPS
INTELLIGENCE = v212.INTELLIGENCE
HISTORY = v212.HISTORY
DEPENDENCIES = v212.DEPENDENCIES
v210 = v212.v210

DRILL_FINGERPRINT = 'drill:safe_proactive_operations_v1'
DRILL_SERVICE = 'drill'
DRILL_TITLE = 'SIMULATED proactive operations incident'


def _norm(message):
    return re.sub(r'\s+', ' ', str(message or '')).strip().lower()


def safe_drill_request(message):
    text = _norm(message)
    return text in {
        'run proactive operations test',
        'run proactive operations drill',
        'run safe incident drill',
        'run the proactive operations test',
        'run the proactive operations drill',
    }


def _drill_event(event_type):
    return {
        'event': event_type,
        'alert': {
            'fingerprint': DRILL_FINGERPRINT,
            'service': DRILL_SERVICE,
            'severity': 'critical',
            'kind': 'safe_incident_drill',
            'title': DRILL_TITLE,
            'message': (
                'SIMULATION ONLY: Tyler AI is verifying proactive incident persistence, '
                'receipt-verified alert email delivery, and recovery closure. No real '
                'dependency failure occurred.'
            ),
            'evidence': {
                'simulation': True,
                'production_dependency_changed': False,
                'automatic_remediation_performed': False,
            },
        },
    }


def _persist_drill_event(event):
    incident = OPS.build_incident(event)
    incident['simulation'] = True
    incident['automatic_remediation_performed'] = False
    importance = 5 if incident.get('status') == 'resolved' else 6
    saved = OPS._post_memory(v212.INCIDENT_CATEGORY, incident, importance=importance)
    return incident, bool(saved)


def _drill_n8n_ready():
    try:
        snapshot = v210.dependency_snapshot(include_errors=False) or {}
    except Exception:
        snapshot = {}
    n8n = dict((snapshot.get('services') or {}).get('n8n') or {})
    configured = bool(n8n.get('configured'))
    state = str(n8n.get('state') or 'unknown').lower()
    unknown_outcome = bool(n8n.get('last_outcome_unknown'))
    if not configured:
        return False, 'n8n is not configured.'
    if unknown_outcome:
        return False, 'n8n has an unresolved unknown-outcome event. Verify that outcome before running the drill.'
    if state in {'degraded', 'unhealthy'}:
        return False, f'n8n is currently {state}. Resolve that condition before running the drill.'
    # healthy, unknown, or stale are acceptable here because this is an explicit
    # user-requested controlled email test with deterministic receipt handling.
    return True, ''


def run_safe_incident_drill():
    status = OPS.status()
    if not status.get('email_notifications_enabled'):
        return base.base_payload(
            'proactive_operations_drill',
            'Safe incident drill not started. Proactive alert emails must be enabled first.',
            used_tools=['proactive_operations'],
            success=False,
        ) | {
            'drill': {
                'started': False,
                'reason': 'proactive_alert_emails_disabled',
            }
        }

    ready, reason = _drill_n8n_ready()
    if not ready:
        return base.base_payload(
            'proactive_operations_drill',
            f'Safe incident drill not started. {reason}',
            used_tools=['proactive_operations'],
            success=False,
        ) | {
            'drill': {
                'started': False,
                'reason': reason,
            }
        }

    raised_event = _drill_event('raised')
    raised_incident, raised_saved = _persist_drill_event(raised_event)
    incident_id = raised_incident.get('incident_id')

    subject = 'Tyler AI TEST: Proactive Operations Safe Incident Drill'
    body = (
        'SIMULATION ONLY — this is not a real outage.\n\n'
        f'Tyler AI opened simulated incident {incident_id}.\n'
        'Purpose: verify proactive incident persistence, alert delivery, and recovery closure.\n\n'
        'No dependency was intentionally failed. No production configuration, code, '
        'credentials, or external workflow settings were changed. No automatic '
        'remediation was performed.'
    )

    email_result = None
    email_error = None
    try:
        email_result = base.send_email_via_n8n(subject, body)
    except Exception as exc:
        # Never retry: the normal n8n wrapper already distinguishes preflight vs
        # unknown downstream outcome, and the drill must preserve that guarantee.
        email_error = str(exc)

    resolved_event = _drill_event('resolved')
    resolved_incident, resolved_saved = _persist_drill_event(resolved_event)

    receipt_confirmed = bool(
        isinstance(email_result, dict)
        and email_result.get('success') is True
        and email_result.get('sent') is True
        and isinstance(email_result.get('message_id'), str)
        and email_result.get('message_id', '').strip()
    )

    passed = bool(raised_saved and resolved_saved and receipt_confirmed)
    lines = [
        'Safe proactive operations drill complete.',
        f'Incident: {incident_id}',
        f'Raised incident persisted: {"yes" if raised_saved else "no"}',
        f'Alert email receipt confirmed: {"yes" if receipt_confirmed else "no"}',
        f'Recovery persisted and incident closed: {"yes" if resolved_saved else "no"}',
        'Real dependency health changed: no',
        'Automatic remediation performed: no',
        'Production configuration changed: no',
    ]
    if email_error:
        lines.extend([
            '',
            'Email test did not produce a confirmed receipt.',
            'Tyler did not retry the email. Verify the real n8n/Gmail outcome before any resend.',
        ])
    elif passed:
        lines.extend([
            '',
            'Result: PASS — incident persistence, proactive email delivery, and recovery closure were verified end-to-end.',
        ])
    else:
        lines.extend([
            '',
            'Result: INCOMPLETE — one or more persistence/receipt checks did not verify successfully.',
        ])

    used_tools = ['proactive_operations']
    if receipt_confirmed:
        used_tools.append('send_email')

    return base.base_payload(
        'proactive_operations_drill',
        '\n'.join(lines),
        used_tools=used_tools,
        success=passed,
        email_result={
            'sent': receipt_confirmed,
            'message_id': email_result.get('message_id') if receipt_confirmed else None,
        } if email_result is not None else {'sent': False},
    ) | {
        'drill': {
            'started': True,
            'passed': passed,
            'simulation': True,
            'incident_id': incident_id,
            'raised_saved': raised_saved,
            'receipt_confirmed': receipt_confirmed,
            'resolved_saved': resolved_saved,
            'email_error_category': 'unconfirmed_or_failed' if email_error else None,
            'real_dependency_health_changed': False,
            'automatic_remediation_performed': False,
            'production_configuration_changed': False,
        },
        'incident': resolved_incident,
    }


_PREVIOUS_HANDLE_MESSAGE = v212.handle_message_v212


def handle_message_v2121(message):
    if safe_drill_request(message):
        payload = run_safe_incident_drill()
        return payload, 200 if payload.get('success') else 503
    return _PREVIOUS_HANDLE_MESSAGE(message)


base.handle_message = handle_message_v2121


# Keep Tyler's verified self-description current.
_ORIGINAL_CORE_PROJECT_TEXT = base.core_project_text
_ORIGINAL_PROJECT_REPLY = base.project_reply


def core_project_text_v2121():
    return (
        _ORIGINAL_CORE_PROJECT_TEXT()
        + ' v2.12.1 includes an explicit safe proactive-operations drill that can '
          'verify simulated incident persistence, one receipt-verified alert email, '
          'and simulated recovery closure without changing real dependency health or '
          'production configuration. The drill never retries an uncertain email outcome.'
    )


def project_reply_v2121():
    return (
        _ORIGINAL_PROJECT_REPLY()
        + '\n\nSafe incident drill:'
        + '\n- Explicit command only; never runs automatically'
        + '\n- Creates a clearly labeled simulated incident and recovery'
        + '\n- Sends one receipt-verified proactive test email'
        + '\n- Never mutates real dependency health or production configuration'
        + '\n- Never retries an uncertain email outcome'
    )


base.core_project_text = core_project_text_v2121
base.project_reply = project_reply_v2121


_PREVIOUS_STATUS_VIEW = base.app.view_functions.get('status')
_PREVIOUS_HEALTH_VIEW = base.app.view_functions.get('health')


def status_v2121():
    response = _PREVIOUS_STATUS_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    capabilities = data.setdefault('capabilities', [])
    if 'safe_proactive_operations_drill' not in capabilities:
        capabilities.append('safe_proactive_operations_drill')
    return base.jsonify(data)


def health_v2121():
    response = _PREVIOUS_HEALTH_VIEW()
    data = response.get_json() if hasattr(response, 'get_json') else {}
    data = dict(data or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    return base.jsonify(data)


base.app.view_functions['status'] = status_v2121
base.app.view_functions['health'] = health_v2121


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(base.os.environ.get('PORT', 10000)),
    )
