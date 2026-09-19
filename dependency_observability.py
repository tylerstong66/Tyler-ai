import re
import threading
from collections import deque
from datetime import datetime, timezone


DEFAULT_HISTORY_SIZE = 50
DEFAULT_STALE_AFTER_SECONDS = 1800


def _now():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.isoformat() if value else None


def _percentile(values, percentile):
    values = sorted(int(v) for v in values if v is not None)
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * float(percentile)
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower
    return int(round(values[lower] + (values[upper] - values[lower]) * fraction))


def _safe_error_text(error):
    text = re.sub(r'\s+', ' ', str(error or '')).strip()
    if not text:
        return ''

    # Diagnostics should be useful without becoming a secret/endpoint dump.
    patterns = [
        (r'(?i)bearer\s+[A-Za-z0-9._~+\-/=]+', 'Bearer <redacted>'),
        (r'(?i)\bsk-[A-Za-z0-9_-]{8,}\b', '<redacted-key>'),
        (r'(?i)(api[_ -]?key|token|secret|password)\s*[:=]\s*[^\s,;]+', r'\1=<redacted>'),
        (r'https?://[^\s)\]}>,]+', '<redacted-url>'),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text[:240]


def classify_error(error):
    text = str(error or '').lower()
    if not text:
        return 'other'
    if 'unknown outcome' in text or 'unconfirmed' in text:
        return 'unknown_outcome'
    if 'timeout' in text or 'timed out' in text:
        return 'timeout'
    if (
        'rate limit' in text
        or '429' in text
        or 'too many requests' in text
        or 'quota' in text
        or 'resource_exhausted' in text
        or 'tokens per day' in text
    ):
        return 'rate_limit'
    if (
        'unauthorized' in text
        or 'authentication' in text
        or 'forbidden' in text
        or '401' in text
        or '403' in text
    ):
        return 'authentication'
    if 'does not exist' in text or 'do not have access' in text or 'model_decommissioned' in text:
        return 'model_access'
    if 'not configured' in text or 'required' in text:
        return 'configuration'
    if '500' in text or '502' in text or '503' in text or '504' in text or 'unavailable' in text:
        return 'unavailable'
    return 'other'


class DependencyObservability:
    """Bounded, process-local telemetry for Tyler AI dependencies.

    No active probes are performed here. Callers record real operations so
    observability adds near-zero external traffic and cannot trigger side effects.
    """

    def __init__(self, history_size=DEFAULT_HISTORY_SIZE, now_fn=None):
        self.history_size = max(10, min(int(history_size), 500))
        self.now_fn = now_fn or _now
        self.started_at = self.now_fn()
        self._lock = threading.RLock()
        self._services = {}

    def _service(self, name):
        if name not in self._services:
            self._services[name] = {
                'total_operations': 0,
                'successes': 0,
                'failures': 0,
                'consecutive_failures': 0,
                'last_success_at': None,
                'last_failure_at': None,
                'last_observed_at': None,
                'last_latency_ms': None,
                'last_error_category': None,
                'last_error_summary': '',
                'last_operation': None,
                'last_outcome_unknown': False,
                'events': deque(maxlen=self.history_size),
            }
        return self._services[name]

    def record_success(self, service, operation, latency_ms, side_effect=False):
        now = self.now_fn()
        with self._lock:
            state = self._service(service)
            state['total_operations'] += 1
            state['successes'] += 1
            state['consecutive_failures'] = 0
            state['last_success_at'] = now
            state['last_observed_at'] = now
            state['last_latency_ms'] = max(0, int(latency_ms or 0))
            state['last_error_category'] = None
            state['last_error_summary'] = ''
            state['last_operation'] = str(operation or 'operation')[:80]
            state['last_outcome_unknown'] = False
            state['events'].append({
                'at': now,
                'ok': True,
                'latency_ms': state['last_latency_ms'],
                'operation': state['last_operation'],
                'side_effect': bool(side_effect),
                'error_category': None,
                'outcome_unknown': False,
            })

    def record_failure(
        self,
        service,
        operation,
        latency_ms,
        error,
        side_effect=False,
        outcome_unknown=False,
    ):
        now = self.now_fn()
        category = classify_error(error)
        if outcome_unknown:
            category = 'unknown_outcome'
        with self._lock:
            state = self._service(service)
            state['total_operations'] += 1
            state['failures'] += 1
            state['consecutive_failures'] += 1
            state['last_failure_at'] = now
            state['last_observed_at'] = now
            state['last_latency_ms'] = max(0, int(latency_ms or 0))
            state['last_error_category'] = category
            state['last_error_summary'] = _safe_error_text(error)
            state['last_operation'] = str(operation or 'operation')[:80]
            state['last_outcome_unknown'] = bool(outcome_unknown)
            state['events'].append({
                'at': now,
                'ok': False,
                'latency_ms': state['last_latency_ms'],
                'operation': state['last_operation'],
                'side_effect': bool(side_effect),
                'error_category': category,
                'outcome_unknown': bool(outcome_unknown),
            })

    def reset(self):
        with self._lock:
            self._services = {}
            self.started_at = self.now_fn()

    def snapshot(self, configured=None, stale_after_seconds=DEFAULT_STALE_AFTER_SECONDS, include_errors=False):
        configured = dict(configured or {})
        stale_after_seconds = max(60, int(stale_after_seconds))
        now = self.now_fn()
        names = sorted(set(configured) | set(self._services))
        output = {}

        with self._lock:
            for name in names:
                state = self._services.get(name)
                is_configured = bool(configured.get(name, False))

                if not is_configured:
                    output[name] = {
                        'state': 'unconfigured',
                        'configured': False,
                        'observed': bool(state and state['last_observed_at']),
                        'stale': False,
                        'total_operations': int(state['total_operations']) if state else 0,
                        'window_success_rate': None,
                        'last_latency_ms': state['last_latency_ms'] if state else None,
                        'p50_latency_ms': None,
                        'p95_latency_ms': None,
                        'consecutive_failures': int(state['consecutive_failures']) if state else 0,
                        'last_success_at': _iso(state['last_success_at']) if state else None,
                        'last_failure_at': _iso(state['last_failure_at']) if state else None,
                        'last_observed_at': _iso(state['last_observed_at']) if state else None,
                        'last_operation': state['last_operation'] if state else None,
                        'last_error_category': state['last_error_category'] if state else None,
                        'last_outcome_unknown': bool(state['last_outcome_unknown']) if state else False,
                    }
                    continue

                if not state or not state['last_observed_at']:
                    output[name] = {
                        'state': 'unknown',
                        'configured': True,
                        'observed': False,
                        'stale': False,
                        'total_operations': 0,
                        'window_success_rate': None,
                        'last_latency_ms': None,
                        'p50_latency_ms': None,
                        'p95_latency_ms': None,
                        'consecutive_failures': 0,
                        'last_success_at': None,
                        'last_failure_at': None,
                        'last_observed_at': None,
                        'last_operation': None,
                        'last_error_category': None,
                        'last_outcome_unknown': False,
                    }
                    continue

                events = list(state['events'])
                successes = sum(1 for event in events if event.get('ok'))
                success_rate = round(successes / len(events), 3) if events else None
                latencies = [event.get('latency_ms') for event in events if event.get('latency_ms') is not None]
                age_seconds = max(0, int((now - state['last_observed_at']).total_seconds()))
                stale = age_seconds > stale_after_seconds

                if stale:
                    service_state = 'stale'
                elif state['consecutive_failures'] >= 2:
                    service_state = 'unhealthy'
                elif state['consecutive_failures'] == 1:
                    service_state = 'degraded'
                elif success_rate is not None and len(events) >= 5 and success_rate < 0.9:
                    service_state = 'degraded'
                else:
                    service_state = 'healthy'

                item = {
                    'state': service_state,
                    'configured': True,
                    'observed': True,
                    'stale': stale,
                    'age_seconds': age_seconds,
                    'total_operations': int(state['total_operations']),
                    'window_size': len(events),
                    'window_success_rate': success_rate,
                    'last_latency_ms': state['last_latency_ms'],
                    'p50_latency_ms': _percentile(latencies, 0.50),
                    'p95_latency_ms': _percentile(latencies, 0.95),
                    'consecutive_failures': int(state['consecutive_failures']),
                    'last_success_at': _iso(state['last_success_at']),
                    'last_failure_at': _iso(state['last_failure_at']),
                    'last_observed_at': _iso(state['last_observed_at']),
                    'last_operation': state['last_operation'],
                    'last_error_category': state['last_error_category'],
                    'last_outcome_unknown': bool(state['last_outcome_unknown']),
                }
                if include_errors:
                    item['last_error_summary'] = state['last_error_summary']
                output[name] = item

        configured_items = [item for item in output.values() if item.get('configured')]
        states = {item.get('state') for item in configured_items}
        if not configured_items:
            overall = 'unconfigured'
        elif 'unhealthy' in states:
            overall = 'unhealthy'
        elif 'degraded' in states:
            overall = 'degraded'
        elif 'unknown' in states:
            overall = 'warming_up'
        elif states == {'stale'} or ('stale' in states and states <= {'healthy', 'stale'}):
            overall = 'stale'
        else:
            overall = 'healthy'

        return {
            'overall': overall,
            'passive_only': True,
            'active_probes': False,
            'started_at': _iso(self.started_at),
            'stale_after_seconds': stale_after_seconds,
            'services': output,
        }
