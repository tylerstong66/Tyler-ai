import hashlib
import json
import re
import threading
from datetime import datetime, timezone

import requests


INCIDENT_CATEGORY = 'operational_incident'
OPS_PREFERENCE_CATEGORY = 'operational_preference'
INCIDENT_SCHEMA = 'tyler_operational_incident_v1'
PREFERENCE_SCHEMA = 'tyler_operational_preference_v1'
DEFAULT_TIMEOUT_SECONDS = 8
SERVICE_LABELS = {
    'groq': 'Groq',
    'tavily': 'Tavily',
    'supabase': 'Supabase',
    'n8n': 'n8n',
}


def _utcnow():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.isoformat() if value else None


def _safe_text(value, limit=700):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    # Broad defensive redaction for accidental credential-like material.
    text = re.sub(
        r'(?i)\b(api[_-]?key|token|password|secret|authorization)\s*[:=]\s*[^,;|]+',
        r'\1=<redacted>',
        text,
    )
    text = re.sub(r'(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+', 'Bearer <redacted>', text)
    return text[:limit]


def _safe_error_category(value):
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    if not text:
        return None
    # Error categories should be categorical, never credential-bearing text.
    if re.search(r'(?i)\b(api[_-]?key|token|password|secret|authorization|bearer)\b', text):
        return 'redacted_sensitive_error'
    return _safe_text(text, 80) or None


def incident_id_for(fingerprint):
    digest = hashlib.sha256(str(fingerprint or '').encode('utf-8')).hexdigest()[:10].upper()
    return f'INC-{digest}'


def safe_diagnostic_bundle(alert, live_snapshot, history_summary, recorded_at=None):
    alert = dict(alert or {})
    live_snapshot = dict(live_snapshot or {})
    history_summary = dict(history_summary or {})
    service = str(alert.get('service') or '')
    live = dict((live_snapshot.get('services') or {}).get(service) or {})
    historical = dict((history_summary.get('services') or {}).get(service) or {})
    return {
        'recorded_at': _iso(recorded_at or _utcnow()),
        'service': service,
        'alert_kind': _safe_text(alert.get('kind'), 80),
        'severity': _safe_text(alert.get('severity'), 20),
        'live': {
            'state': live.get('state'),
            'configured': bool(live.get('configured')),
            'observed': bool(live.get('observed')),
            'last_latency_ms': live.get('last_latency_ms'),
            'p50_latency_ms': live.get('p50_latency_ms'),
            'p95_latency_ms': live.get('p95_latency_ms'),
            'window_success_rate': live.get('window_success_rate'),
            'consecutive_failures': int(live.get('consecutive_failures') or 0),
            'last_error_category': _safe_error_category(live.get('last_error_category')),
            'last_outcome_unknown': bool(live.get('last_outcome_unknown')),
            'total_operations': int(live.get('total_operations') or 0),
        },
        'history': {
            'samples': int(historical.get('samples') or 0),
            'latest_state': historical.get('latest_state'),
            'healthy_sample_rate': historical.get('healthy_sample_rate'),
            'average_latency_ms': historical.get('average_latency_ms'),
            'p95_latency_ms': historical.get('p95_latency_ms'),
            'latency_trend': historical.get('latency_trend'),
            'failure_samples': int(historical.get('failure_samples') or 0),
            'unknown_outcome_samples': int(historical.get('unknown_outcome_samples') or 0),
        },
        'evidence': dict(alert.get('evidence') or {}),
    }


def recommended_response(alert, diagnostics=None):
    """Return a conservative plan. This function never executes the plan."""
    alert = dict(alert or {})
    diagnostics = dict(diagnostics or {})
    service = str(alert.get('service') or '')
    kind = str(alert.get('kind') or '')
    label = SERVICE_LABELS.get(service, service or 'dependency')

    if kind == 'unknown_external_outcome':
        return {
            'summary': f'Verify the real downstream {label} outcome before any retry.',
            'steps': [
                'Inspect the downstream execution/receipt using existing logs or provider history.',
                'Determine whether the side effect actually completed.',
                'If it completed, record the receipt and do not repeat the action.',
                'If it definitely did not complete, prepare a new retry for explicit approval.',
            ],
            'approval_required_for': [
                'retrying the side-effect action',
                'changing credentials or configuration',
                'deploying code changes',
            ],
            'automatic_actions_allowed': ['collect diagnostics', 'record incident', 'prepare recommendation'],
            'never_automatic': ['retry uncertain side effect', 'change production configuration', 'deploy code'],
        }

    if kind in {'live_unhealthy', 'live_degraded'}:
        steps = [
            f'Review the latest safe {label} telemetry and error category.',
            'Compare the failure timing with recent deployments or configuration changes.',
            'Inspect provider/workflow logs without changing production state.',
            'Prepare the smallest reversible fix that addresses the verified root cause.',
            'Run targeted tests before requesting approval for any production change.',
        ]
        if service == 'n8n':
            steps.insert(2, 'Check the latest n8n workflow execution and authentication configuration before considering any resend.')
        return {
            'summary': f'Diagnose the verified cause of the {label} health degradation, then prepare a minimal reversible fix.',
            'steps': steps,
            'approval_required_for': ['production configuration changes', 'deploying code', 'side-effect retries'],
            'automatic_actions_allowed': ['collect diagnostics', 'record incident', 'prepare recommendation'],
            'never_automatic': ['unsafe retry', 'credential rotation', 'production deploy'],
        }

    if kind == 'historical_reliability':
        return {
            'summary': f'Investigate recurring {label} reliability failures across the persisted history window.',
            'steps': [
                'Correlate failed samples with timestamps and known deployments.',
                'Separate provider outages from local authentication, rate-limit, or application failures.',
                'Identify the dominant repeatable failure mode.',
                'Prepare a targeted reliability change and regression test plan.',
            ],
            'approval_required_for': ['production changes', 'provider/configuration changes'],
            'automatic_actions_allowed': ['analyze history', 'record incident', 'prepare recommendation'],
            'never_automatic': ['deploy code', 'change credentials'],
        }

    if kind == 'latency_regression':
        return {
            'summary': f'Confirm the {label} latency regression and identify whether it is provider-side or local before changing anything.',
            'steps': [
                'Compare recent and older persisted latency samples.',
                'Check whether failures, model changes, payload growth, or provider conditions coincide with the slowdown.',
                'Prepare a benchmark that reproduces the slower path without generating side effects.',
                'Propose the smallest performance change only after the bottleneck is verified.',
            ],
            'approval_required_for': ['model/provider changes', 'production configuration changes', 'deployment'],
            'automatic_actions_allowed': ['analyze latency history', 'record incident', 'prepare recommendation'],
            'never_automatic': ['switch providers', 'deploy code'],
        }

    return {
        'summary': f'Collect evidence for the {label} alert and prepare a reversible fix only after the cause is verified.',
        'steps': [
            'Collect passive diagnostics and persisted history.',
            'Verify the failure mode.',
            'Prepare a minimal reversible fix and tests.',
        ],
        'approval_required_for': ['production changes', 'side-effect actions'],
        'automatic_actions_allowed': ['collect diagnostics', 'record incident', 'prepare recommendation'],
        'never_automatic': ['production mutation'],
    }


class ProactiveOperations:
    """Incident + recommendation layer for Tyler AI health events.

    Safe automatic work: gather already-observed diagnostics, store incident state,
    prepare a recommended response, and optionally send an explicitly opted-in
    alert email. It never changes production configuration/code and never retries
    an uncertain side effect.
    """

    def __init__(
        self,
        intelligence,
        history,
        snapshot_fn,
        supabase_url_fn,
        headers_fn,
        version_fn,
        email_fn=None,
        default_email_fn=None,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        now_fn=None,
    ):
        self.intelligence = intelligence
        self.history = history
        self.snapshot_fn = snapshot_fn
        self.supabase_url_fn = supabase_url_fn
        self.headers_fn = headers_fn
        self.version_fn = version_fn
        self.email_fn = email_fn
        self.default_email_fn = default_email_fn
        self.timeout_seconds = max(2, min(int(timeout_seconds), 30))
        self.now_fn = now_fn or _utcnow
        self._lock = threading.RLock()
        self._preference_loaded = False
        self._email_notifications_enabled = False
        self._last_error_category = None
        self._processed_events = 0
        self._incidents_written = 0
        self._emails_sent = 0

    def configured(self):
        try:
            return bool(self.supabase_url_fn() and self.headers_fn())
        except Exception:
            return False

    def status(self):
        self._load_preference_once()
        with self._lock:
            return {
                'configured': self.configured(),
                'email_notifications_enabled': bool(self._email_notifications_enabled),
                'processed_events_this_process': int(self._processed_events),
                'incidents_written_this_process': int(self._incidents_written),
                'emails_sent_this_process': int(self._emails_sent),
                'last_error_category': self._last_error_category,
                'automatic_remediation_enabled': False,
                'active_probes': False,
            }

    def _post_memory(self, category, payload, importance=5):
        if not self.configured():
            return False
        try:
            response = requests.post(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers={**self.headers_fn(), 'Prefer': 'return=minimal'},
                json={
                    'memories': json.dumps(payload, separators=(',', ':'), sort_keys=True),
                    'category': category,
                    'importance': max(1, min(int(importance), 10)),
                },
                timeout=self.timeout_seconds,
            )
            if response.ok:
                return True
            self._last_error_category = f'http_{response.status_code}'
        except requests.Timeout:
            self._last_error_category = 'timeout'
        except Exception:
            self._last_error_category = 'write_error'
        return False

    def _load_rows(self, category, limit=50):
        if not self.configured():
            return []
        try:
            response = requests.get(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers=self.headers_fn(),
                params={
                    'select': 'id,created_at,memories',
                    'category': f'eq.{category}',
                    'order': 'created_at.desc',
                    'limit': max(1, min(int(limit), 250)),
                },
                timeout=self.timeout_seconds,
            )
            if not response.ok:
                return []
            output = []
            for row in response.json() or []:
                try:
                    item = json.loads(str(row.get('memories') or ''))
                except Exception:
                    continue
                if not isinstance(item, dict):
                    continue
                item['row_id'] = row.get('id')
                item['stored_at'] = row.get('created_at')
                output.append(item)
            return output
        except Exception:
            return []

    def _load_preference_once(self):
        with self._lock:
            if self._preference_loaded:
                return
            self._preference_loaded = True
        rows = self._load_rows(OPS_PREFERENCE_CATEGORY, limit=20)
        for item in rows:
            if item.get('schema') != PREFERENCE_SCHEMA:
                continue
            if item.get('name') == 'proactive_alert_emails':
                with self._lock:
                    self._email_notifications_enabled = bool(item.get('enabled'))
                return

    def set_email_notifications(self, enabled):
        enabled = bool(enabled)
        record = {
            'schema': PREFERENCE_SCHEMA,
            'name': 'proactive_alert_emails',
            'enabled': enabled,
            'recorded_at': _iso(self.now_fn()),
            'version': str(self.version_fn() or ''),
        }
        saved = self._post_memory(OPS_PREFERENCE_CATEGORY, record, importance=6)
        if saved:
            with self._lock:
                self._preference_loaded = True
                self._email_notifications_enabled = enabled
                self._last_error_category = None
        return {'saved': saved, 'enabled': enabled if saved else self.status().get('email_notifications_enabled')}

    def _history_summary(self):
        try:
            return self.history.summarize(hours=24, limit=self.history.max_records) or {}
        except Exception:
            return {}

    def _snapshot(self):
        try:
            return self.snapshot_fn() or {}
        except Exception:
            return {}

    def build_incident(self, event):
        event = dict(event or {})
        alert = dict(event.get('alert') or {})
        fingerprint = str(alert.get('fingerprint') or '')
        incident_id = incident_id_for(fingerprint)
        event_type = str(event.get('event') or 'raised')
        status = 'resolved' if event_type == 'resolved' else 'open'
        diagnostics = safe_diagnostic_bundle(
            alert,
            self._snapshot(),
            self._history_summary(),
            recorded_at=self.now_fn(),
        )
        return {
            'schema': INCIDENT_SCHEMA,
            'incident_id': incident_id,
            'fingerprint': fingerprint,
            'status': status,
            'event': event_type,
            'service': str(alert.get('service') or ''),
            'severity': str(alert.get('severity') or 'warning'),
            'kind': str(alert.get('kind') or ''),
            'title': _safe_text(alert.get('title'), 160),
            'message': _safe_text(alert.get('message'), 700),
            'recorded_at': _iso(self.now_fn()),
            'version': str(self.version_fn() or ''),
            'diagnostics': diagnostics,
            'recommended_response': recommended_response(alert, diagnostics),
            'automatic_remediation_performed': False,
        }

    def _n8n_safe_for_notification(self, alert):
        if str((alert or {}).get('service') or '') == 'n8n':
            return False
        try:
            snapshot = self._snapshot()
            n8n = dict((snapshot.get('services') or {}).get('n8n') or {})
            return n8n.get('state') == 'healthy' and not n8n.get('last_outcome_unknown')
        except Exception:
            return False

    def _maybe_email(self, event, incident):
        self._load_preference_once()
        with self._lock:
            enabled = bool(self._email_notifications_enabled)
        alert = dict((event or {}).get('alert') or {})
        event_type = str((event or {}).get('event') or '')
        if not enabled or not self.email_fn or not self.default_email_fn:
            return {'attempted': False, 'reason': 'disabled'}
        if event_type == 'reminder':
            return {'attempted': False, 'reason': 'reminder_suppressed'}
        if event_type not in {'raised', 'resolved'}:
            return {'attempted': False, 'reason': 'not_notifiable'}
        if event_type == 'raised' and alert.get('severity') != 'critical':
            return {'attempted': False, 'reason': 'critical_only'}
        if not self._n8n_safe_for_notification(alert):
            return {'attempted': False, 'reason': 'n8n_not_safe'}

        recipient = str(self.default_email_fn() or '').strip()
        if not recipient:
            return {'attempted': False, 'reason': 'no_recipient'}

        if event_type == 'resolved':
            subject = f"Tyler AI recovery: {incident.get('title')}"
            body = (
                f"Incident {incident.get('incident_id')} is now resolved.\n\n"
                f"Service: {incident.get('service')}\n"
                f"Previous issue: {incident.get('title')}\n\n"
                'No automatic production changes were made.'
            )
        else:
            recommendation = incident.get('recommended_response') or {}
            subject = f"Tyler AI {str(incident.get('severity') or '').upper()} incident: {incident.get('title')}"
            body = (
                f"Tyler AI opened incident {incident.get('incident_id')}.\n\n"
                f"Service: {incident.get('service')}\n"
                f"Issue: {incident.get('message')}\n\n"
                f"Recommended response: {recommendation.get('summary')}\n\n"
                'Tyler gathered diagnostics and prepared a recommendation only. '
                'No production configuration, code, or uncertain side-effect action was changed automatically.'
            )
        try:
            result = self.email_fn(recipient, subject, body)
            sent = bool(isinstance(result, dict) and result.get('success') and result.get('sent') and result.get('message_id'))
            if sent:
                with self._lock:
                    self._emails_sent += 1
                return {'attempted': True, 'sent': True, 'message_id': result.get('message_id')}
            return {'attempted': True, 'sent': False, 'reason': 'unconfirmed_receipt'}
        except Exception:
            return {'attempted': True, 'sent': False, 'reason': 'notification_failed'}

    def process_events(self, events):
        output = []
        for event in events or []:
            with self._lock:
                self._processed_events += 1
            try:
                incident = self.build_incident(event)
                importance = 8 if incident.get('severity') == 'critical' else 6
                if incident.get('status') == 'resolved':
                    importance = 5
                saved = self._post_memory(INCIDENT_CATEGORY, incident, importance=importance)
                if saved:
                    with self._lock:
                        self._incidents_written += 1
                        self._last_error_category = None
                notification = self._maybe_email(event, incident)
                output.append({
                    'incident': incident,
                    'saved': bool(saved),
                    'notification': notification,
                })
            except Exception:
                output.append({'saved': False, 'error': 'incident_processing_error'})
        return output

    def recent_incidents(self, limit=20, status=None):
        rows = self._load_rows(INCIDENT_CATEGORY, limit=max(20, int(limit) * 4))
        latest = {}
        for item in rows:
            if item.get('schema') != INCIDENT_SCHEMA:
                continue
            incident_id = str(item.get('incident_id') or '')
            if not incident_id or incident_id in latest:
                continue
            latest[incident_id] = item
        incidents = list(latest.values())
        if status:
            incidents = [item for item in incidents if item.get('status') == status]
        return incidents[:max(1, min(int(limit), 50))]

    def incident(self, incident_id):
        target = str(incident_id or '').strip().upper()
        for item in self.recent_incidents(limit=50):
            if str(item.get('incident_id') or '').upper() == target:
                return item
        return None
