import json
import math
import threading
import time
from datetime import datetime, timedelta, timezone

import requests

from persistent_health_history import operation_checkpoints


ALERT_STATE_CATEGORY = 'dependency_health_alert'
ALERT_SCHEMA = 'dependency_health_alert_v1'
SERVICE_ORDER = ['groq', 'gemini', 'tavily', 'supabase', 'n8n']
SERVICE_LABELS = {
    'groq': 'Groq',
    'gemini': 'Gemini',
    'tavily': 'Tavily',
    'supabase': 'Supabase',
    'n8n': 'n8n',
}
SEVERITY_RANK = {'info': 0, 'warning': 1, 'critical': 2}


def _utcnow():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.isoformat() if value else None


def _parse_time(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def _mean(values):
    values = [float(value) for value in values if value is not None]
    return (sum(values) / len(values)) if values else None


def _round_ms(value):
    return int(round(float(value))) if value is not None else None


def _clean_alert(alert):
    """Return a safe alert object with no raw exception text or credentials."""
    alert = dict(alert or {})
    return {
        'fingerprint': str(alert.get('fingerprint') or '')[:120],
        'service': str(alert.get('service') or '')[:40],
        'severity': str(alert.get('severity') or 'warning')[:20],
        'kind': str(alert.get('kind') or '')[:60],
        'title': str(alert.get('title') or '')[:160],
        'message': str(alert.get('message') or '')[:700],
        'evidence': dict(alert.get('evidence') or {}),
    }


def _alert(service, kind, severity, title, message, evidence=None):
    return _clean_alert({
        'fingerprint': f'{service}:{kind}',
        'service': service,
        'kind': kind,
        'severity': severity,
        'title': title,
        'message': message,
        'evidence': evidence or {},
    })


def _historical_service_series(records, service):
    output = []
    for item in operation_checkpoints(records, service):
        output.append({
            'state': item.get('state'),
            'last_latency_ms': item.get('last_latency_ms'),
            'last_error_category': item.get('last_error_category'),
            'last_outcome_unknown': bool(item.get('last_outcome_unknown')),
            'recorded_at': item.get('recorded_at'),
        })
    return output


def historical_signals(records, service):
    """Calculate conservative historical reliability and latency signals."""
    samples = _historical_service_series(records, service)
    result = {
        'samples': len(samples),
        'healthy_rate': None,
        'failure_samples': 0,
        'unknown_outcome_samples': 0,
        'older_latency_ms': None,
        'newer_latency_ms': None,
        'latency_change_pct': None,
    }
    if not samples:
        return result

    healthy = sum(1 for item in samples if item.get('state') == 'healthy')
    failures = sum(
        1 for item in samples
        if item.get('state') in {'degraded', 'unhealthy'} or item.get('last_error_category')
    )
    unknown = sum(1 for item in samples if item.get('last_outcome_unknown'))
    result['healthy_rate'] = round(healthy / len(samples), 3)
    result['failure_samples'] = failures
    result['unknown_outcome_samples'] = unknown

    latencies = [
        float(item.get('last_latency_ms'))
        for item in samples
        if item.get('last_latency_ms') is not None
        and float(item.get('last_latency_ms')) >= 0
    ]
    if len(latencies) >= 6:
        midpoint = len(latencies) // 2
        older = latencies[:midpoint]
        newer = latencies[midpoint:]
        older_avg = _mean(older)
        newer_avg = _mean(newer)
        result['older_latency_ms'] = _round_ms(older_avg)
        result['newer_latency_ms'] = _round_ms(newer_avg)
        if older_avg and older_avg > 0:
            result['latency_change_pct'] = round(((newer_avg - older_avg) / older_avg) * 100.0, 1)
    return result


def detect_service_alert(service, live_item, historical=None):
    """Choose at most one highest-value active alert per dependency."""
    live_item = dict(live_item or {})
    historical = dict(historical or {})
    label = SERVICE_LABELS.get(service, service)

    # Unknown side-effect outcome is the most important condition. Never advise
    # an automatic retry because the real-world action may already have happened.
    if live_item.get('last_outcome_unknown'):
        return _alert(
            service,
            'unknown_external_outcome',
            'critical',
            f'{label} action outcome is unknown',
            f'{label} reported an uncertain external outcome. Verify the downstream execution/receipt before retrying any side-effect action.',
            {'last_error_category': live_item.get('last_error_category') or 'unknown_outcome'},
        )

    state = str(live_item.get('state') or '')
    consecutive = int(live_item.get('consecutive_failures') or 0)
    if state == 'unhealthy' or consecutive >= 2:
        return _alert(
            service,
            'live_unhealthy',
            'critical',
            f'{label} is unhealthy',
            f'{label} has repeated recent failures and is currently unhealthy. Review the dependency before relying on it for critical work.',
            {
                'state': state or 'unhealthy',
                'consecutive_failures': consecutive,
                'last_error_category': live_item.get('last_error_category'),
            },
        )
    if state == 'degraded':
        return _alert(
            service,
            'live_degraded',
            'warning',
            f'{label} is degraded',
            f'{label} has a recent failure and is currently degraded. Tyler will continue operating where safe, but this dependency deserves attention.',
            {
                'state': state,
                'consecutive_failures': consecutive,
                'last_error_category': live_item.get('last_error_category'),
            },
        )

    samples = int(historical.get('samples') or 0)
    healthy_rate = historical.get('healthy_rate')
    if samples >= 5 and healthy_rate is not None:
        if healthy_rate < 0.80:
            return _alert(
                service,
                'historical_reliability',
                'critical',
                f'{label} reliability is poor',
                f'{label} was healthy in only {round(healthy_rate * 100)}% of observed operation checkpoints in the analysis window.',
                {
                    'samples': samples,
                    'healthy_rate': healthy_rate,
                    'failure_samples': int(historical.get('failure_samples') or 0),
                },
            )
        if healthy_rate < 0.95:
            return _alert(
                service,
                'historical_reliability',
                'warning',
                f'{label} reliability has degraded',
                f'{label} was healthy in {round(healthy_rate * 100)}% of observed operation checkpoints in the analysis window.',
                {
                    'samples': samples,
                    'healthy_rate': healthy_rate,
                    'failure_samples': int(historical.get('failure_samples') or 0),
                },
            )

    change = historical.get('latency_change_pct')
    older = historical.get('older_latency_ms')
    newer = historical.get('newer_latency_ms')
    if samples >= 6 and change is not None and older is not None and newer is not None:
        absolute_increase = newer - older
        # Avoid noisy alerts: require both a relative and absolute regression.
        if change >= 100 and absolute_increase >= 500:
            return _alert(
                service,
                'latency_regression',
                'critical',
                f'{label} latency has sharply increased',
                f'{label} recent latency is about {round(change)}% slower than earlier persisted samples ({older} ms → {newer} ms average).',
                {
                    'samples': samples,
                    'latency_change_pct': change,
                    'older_latency_ms': older,
                    'newer_latency_ms': newer,
                },
            )
        if change >= 35 and absolute_increase >= 150:
            return _alert(
                service,
                'latency_regression',
                'warning',
                f'{label} latency is trending slower',
                f'{label} recent latency is about {round(change)}% slower than earlier persisted samples ({older} ms → {newer} ms average).',
                {
                    'samples': samples,
                    'latency_change_pct': change,
                    'older_latency_ms': older,
                    'newer_latency_ms': newer,
                },
            )
    return None


class HealthIntelligence:
    """Passive alert engine built from observed health and persisted history.

    It never probes Groq, Gemini, Tavily, n8n, or Supabase for service health. Supabase
    is used only to read existing health history and persist alert state. Alert
    state persistence is best effort and cannot break the user request.
    """

    def __init__(
        self,
        history,
        snapshot_fn,
        supabase_url_fn,
        headers_fn,
        version_fn,
        history_hours=24,
        history_refresh_seconds=300,
        reminder_seconds=21600,
        state_limit=250,
        timeout_seconds=8,
        now_fn=None,
        monotonic_fn=None,
    ):
        self.history = history
        self.snapshot_fn = snapshot_fn
        self.supabase_url_fn = supabase_url_fn
        self.headers_fn = headers_fn
        self.version_fn = version_fn
        self.history_hours = max(1, min(int(history_hours), 24 * 30))
        self.history_refresh_seconds = max(60, int(history_refresh_seconds))
        self.reminder_seconds = max(900, int(reminder_seconds))
        self.state_limit = max(50, min(int(state_limit), 1000))
        self.timeout_seconds = max(2, min(int(timeout_seconds), 30))
        self.now_fn = now_fn or _utcnow
        self.monotonic_fn = monotonic_fn or time.monotonic
        self._lock = threading.RLock()
        self._state_loaded = False
        self._active = {}
        self._last_emitted = {}
        self._history_records = []
        self._history_loaded_mono = None
        self._last_history_error = None

    def configured(self):
        try:
            return bool(self.supabase_url_fn() and self.headers_fn())
        except Exception:
            return False

    def status(self):
        with self._lock:
            return {
                'configured': self.configured(),
                'state_loaded': bool(self._state_loaded),
                'active_alerts': len(self._active),
                'history_hours': self.history_hours,
                'history_refresh_seconds': self.history_refresh_seconds,
                'reminder_seconds': self.reminder_seconds,
                'last_history_error': self._last_history_error,
            }

    def _load_state_once(self):
        with self._lock:
            if self._state_loaded:
                return
            self._state_loaded = True
        if not self.configured():
            return
        try:
            response = requests.get(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers=self.headers_fn(),
                params={
                    'select': 'id,created_at,memories',
                    'category': f'eq.{ALERT_STATE_CATEGORY}',
                    'order': 'created_at.desc',
                    'limit': self.state_limit,
                },
                timeout=self.timeout_seconds,
            )
            if not response.ok:
                return
            latest = {}
            for row in response.json() or []:
                try:
                    event = json.loads(str(row.get('memories') or ''))
                except Exception:
                    continue
                if not isinstance(event, dict) or event.get('schema') != ALERT_SCHEMA:
                    continue
                fingerprint = str(event.get('fingerprint') or '')
                if not fingerprint or fingerprint in latest:
                    continue
                latest[fingerprint] = event
            with self._lock:
                for fingerprint, event in latest.items():
                    emitted_at = _parse_time(event.get('recorded_at'))
                    if emitted_at:
                        self._last_emitted[fingerprint] = emitted_at
                    if event.get('event') in {'raised', 'reminder'}:
                        self._active[fingerprint] = _clean_alert(event.get('alert') or {})
        except Exception:
            return

    def _persist_event(self, event_type, alert):
        if not self.configured():
            return False
        alert = _clean_alert(alert)
        record = {
            'schema': ALERT_SCHEMA,
            'event': str(event_type or '')[:20],
            'fingerprint': alert.get('fingerprint'),
            'recorded_at': _iso(self.now_fn()),
            'version': str(self.version_fn() or ''),
            'alert': alert,
        }
        try:
            response = requests.post(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers={**self.headers_fn(), 'Prefer': 'return=minimal'},
                json={
                    'memories': json.dumps(record, separators=(',', ':'), sort_keys=True),
                    'category': ALERT_STATE_CATEGORY,
                    'importance': 4 if alert.get('severity') == 'critical' else 3,
                },
                timeout=self.timeout_seconds,
            )
            return bool(response.ok)
        except Exception:
            return False

    def _refresh_history(self, force=False):
        now_mono = self.monotonic_fn()
        with self._lock:
            due = (
                force
                or self._history_loaded_mono is None
                or (now_mono - self._history_loaded_mono) >= self.history_refresh_seconds
            )
            if not due:
                return list(self._history_records)
        try:
            records = self.history.load(
                hours=self.history_hours,
                limit=self.history.max_records,
            )
            with self._lock:
                self._history_records = list(records or [])
                self._history_loaded_mono = now_mono
                self._last_history_error = None
                return list(self._history_records)
        except Exception:
            with self._lock:
                self._history_loaded_mono = now_mono
                self._last_history_error = 'history_read_error'
                return list(self._history_records)

    def evaluate(self, force_history_refresh=False):
        self._load_state_once()
        try:
            snapshot = self.snapshot_fn() or {}
        except Exception:
            snapshot = {}
        records = self._refresh_history(force=force_history_refresh)
        alerts = []
        services = snapshot.get('services') or {}
        for service in SERVICE_ORDER:
            live = services.get(service) or {}
            historical = historical_signals(records, service)
            alert = detect_service_alert(service, live, historical)
            if alert:
                alerts.append(alert)
        alerts.sort(
            key=lambda item: (
                -SEVERITY_RANK.get(item.get('severity'), 0),
                SERVICE_ORDER.index(item.get('service')) if item.get('service') in SERVICE_ORDER else 99,
            )
        )
        return alerts

    def sync_and_get_events(self, force_history_refresh=False):
        """Return only newly raised/reminded/resolved events to suppress spam."""
        alerts = self.evaluate(force_history_refresh=force_history_refresh)
        now = self.now_fn()
        current = {item['fingerprint']: item for item in alerts if item.get('fingerprint')}
        events = []

        with self._lock:
            previous = dict(self._active)
            last_emitted = dict(self._last_emitted)

        for fingerprint, alert in current.items():
            previous_alert = previous.get(fingerprint)
            last = last_emitted.get(fingerprint)
            if previous_alert is None:
                event_type = 'raised'
            elif last is None or (now - last).total_seconds() >= self.reminder_seconds:
                event_type = 'reminder'
            else:
                continue
            event = {'event': event_type, 'alert': alert, 'recorded_at': _iso(now)}
            events.append(event)
            with self._lock:
                self._active[fingerprint] = alert
                self._last_emitted[fingerprint] = now
            self._persist_event(event_type, alert)

        for fingerprint, old_alert in previous.items():
            if fingerprint in current:
                continue
            event = {
                'event': 'resolved',
                'alert': old_alert,
                'recorded_at': _iso(now),
            }
            events.append(event)
            with self._lock:
                self._active.pop(fingerprint, None)
                self._last_emitted[fingerprint] = now
            self._persist_event('resolved', old_alert)

        events.sort(
            key=lambda item: (
                1 if item.get('event') == 'resolved' else 0,
                -SEVERITY_RANK.get((item.get('alert') or {}).get('severity'), 0),
            )
        )
        return events

    def active_alerts(self, force_history_refresh=False):
        # Explicit inspection returns current evidence even if it was already
        # notified and therefore suppressed from normal conversational alerts.
        return self.evaluate(force_history_refresh=force_history_refresh)
