import json
import math
import time
from datetime import datetime, timedelta, timezone

import requests


HEALTH_HISTORY_CATEGORY = 'dependency_health'
DEFAULT_INTERVAL_SECONDS = 600
DEFAULT_MAX_RECORDS = 1500
DEFAULT_TIMEOUT_SECONDS = 8
SERVICE_NAMES = ('groq', 'gemini', 'tavily', 'supabase', 'n8n')


def _utcnow():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.isoformat() if value else None


def _percentile(values, percentile):
    values = sorted(float(v) for v in values if v is not None)
    if not values:
        return None
    if len(values) == 1:
        return int(round(values[0]))
    position = (len(values) - 1) * float(percentile)
    lower = int(math.floor(position))
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower
    return int(round(values[lower] + ((values[upper] - values[lower]) * fraction)))


def _trend(values):
    values = [float(v) for v in values if v is not None]
    if len(values) < 4:
        return 'insufficient_data'
    midpoint = len(values) // 2
    older = values[:midpoint]
    newer = values[midpoint:]
    if not older or not newer:
        return 'insufficient_data'
    older_avg = sum(older) / len(older)
    newer_avg = sum(newer) / len(newer)
    if older_avg <= 0:
        return 'stable'
    change = (newer_avg - older_avg) / older_avg
    if change >= 0.20:
        return 'slower'
    if change <= -0.20:
        return 'faster'
    return 'stable'


def _compact_service(item):
    item = dict(item or {})
    return {
        'state': item.get('state'),
        'configured': bool(item.get('configured')),
        'observed': bool(item.get('observed')),
        'last_latency_ms': item.get('last_latency_ms'),
        'p50_latency_ms': item.get('p50_latency_ms'),
        'p95_latency_ms': item.get('p95_latency_ms'),
        'window_success_rate': item.get('window_success_rate'),
        'consecutive_failures': int(item.get('consecutive_failures') or 0),
        'last_error_category': item.get('last_error_category'),
        'last_outcome_unknown': bool(item.get('last_outcome_unknown')),
        'total_operations': int(item.get('total_operations') or 0),
        'last_observed_at': item.get('last_observed_at'),
    }


def operation_checkpoints(records, service):
    """Return service samples only when its operation counter advances.

    Health-history rows are global snapshots. A forced history request or an
    unrelated dependency call can therefore persist Groq's unchanged
    last-known state again. Treating every row as a new Groq sample inflates
    both failures and successes. The process start timestamp plus the
    monotonic per-process operation counter lets us discard those duplicates.

    Legacy/test records without both fields remain distinct for backward
    compatibility; real v1 history rows contain them.
    """
    output = []
    last_total_by_process = {}
    for record in records or []:
        item = (record.get('services') or {}).get(service)
        if not isinstance(item, dict) or not item.get('observed'):
            continue

        process_started_at = record.get('process_started_at')
        total_operations = item.get('total_operations')
        has_counter = (
            process_started_at not in {None, ''}
            and isinstance(total_operations, (int, float))
            and int(total_operations) > 0
        )
        if has_counter:
            process_key = str(process_started_at)
            total = int(total_operations)
            previous = last_total_by_process.get(process_key)
            if previous is not None and total <= previous:
                continue
            last_total_by_process[process_key] = total

        sample = dict(item)
        sample['recorded_at'] = record.get('recorded_at') or record.get('stored_at')
        sample['process_started_at'] = process_started_at
        output.append(sample)
    return output


def compact_snapshot(snapshot, version, recorded_at=None):
    snapshot = dict(snapshot or {})
    recorded_at = recorded_at or _utcnow()
    services = {}
    for name in SERVICE_NAMES:
        item = (snapshot.get('services') or {}).get(name)
        if item is not None:
            services[name] = _compact_service(item)
    return {
        'schema': 'dependency_health_v1',
        'recorded_at': _iso(recorded_at),
        'version': str(version or ''),
        'process_started_at': snapshot.get('started_at'),
        'overall': snapshot.get('overall'),
        'services': services,
    }


def state_signature(snapshot):
    snapshot = dict(snapshot or {})
    parts = [str(snapshot.get('overall') or '')]
    services = snapshot.get('services') or {}
    for name in SERVICE_NAMES:
        item = services.get(name) or {}
        parts.extend([
            name,
            str(item.get('state') or ''),
            str(item.get('last_error_category') or ''),
            '1' if item.get('last_outcome_unknown') else '0',
        ])
    return '|'.join(parts)


class PersistentHealthHistory:
    """Best-effort bounded persistence for passive dependency telemetry.

    This component never probes dependencies. It persists compact snapshots of
    telemetry that Tyler AI already observed from real operations. Persistence
    writes bypass the instrumented Supabase wrappers so they cannot recursively
    generate more health-history writes.
    """

    def __init__(
        self,
        supabase_url_fn,
        headers_fn,
        snapshot_fn,
        version_fn,
        interval_seconds=DEFAULT_INTERVAL_SECONDS,
        max_records=DEFAULT_MAX_RECORDS,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        now_fn=None,
        monotonic_fn=None,
    ):
        self.supabase_url_fn = supabase_url_fn
        self.headers_fn = headers_fn
        self.snapshot_fn = snapshot_fn
        self.version_fn = version_fn
        self.interval_seconds = max(60, int(interval_seconds))
        self.max_records = max(100, min(int(max_records), 5000))
        self.timeout_seconds = max(2, min(int(timeout_seconds), 30))
        self.now_fn = now_fn or _utcnow
        self.monotonic_fn = monotonic_fn or time.monotonic
        self.last_persist_monotonic = None
        self.last_attempt_monotonic = None
        self.last_signature = None
        self.last_success_at = None
        self.last_error_category = None
        self.persisted_this_process = 0

    def configured(self):
        try:
            return bool(self.supabase_url_fn() and self.headers_fn())
        except Exception:
            return False

    def status(self):
        return {
            'configured': self.configured(),
            'last_success_at': _iso(self.last_success_at),
            'last_error_category': self.last_error_category,
            'persisted_this_process': int(self.persisted_this_process),
            'interval_seconds': int(self.interval_seconds),
            'max_records': int(self.max_records),
        }

    def _should_persist(self, snapshot, force=False):
        if force:
            return True
        now_mono = self.monotonic_fn()
        signature = state_signature(snapshot)
        state_changed = self.last_signature is not None and signature != self.last_signature
        first_observation = self.last_signature is None and any(
            bool(item.get('observed'))
            for item in (snapshot.get('services') or {}).values()
        )
        due = (
            self.last_persist_monotonic is None
            or (now_mono - self.last_persist_monotonic) >= self.interval_seconds
        )
        return first_observation or state_changed or due

    def maybe_persist(self, force=False, reason='activity'):
        """Persist a compact snapshot if due. Never raises to the caller."""
        try:
            snapshot = self.snapshot_fn()
        except Exception:
            self.last_error_category = 'snapshot_error'
            return {'saved': False, 'reason': 'snapshot_error'}

        if not self._should_persist(snapshot, force=force):
            return {'saved': False, 'reason': 'not_due'}
        if not self.configured():
            self.last_error_category = 'unconfigured'
            return {'saved': False, 'reason': 'unconfigured'}

        now_mono = self.monotonic_fn()
        self.last_attempt_monotonic = now_mono
        record = compact_snapshot(snapshot, self.version_fn(), self.now_fn())
        record['reason'] = str(reason or 'activity')[:40]

        try:
            response = requests.post(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers={**self.headers_fn(), 'Prefer': 'return=minimal'},
                json={
                    'memories': json.dumps(record, separators=(',', ':'), sort_keys=True),
                    'category': HEALTH_HISTORY_CATEGORY,
                    'importance': 3,
                },
                timeout=self.timeout_seconds,
            )
            if not response.ok:
                self.last_error_category = f'http_{response.status_code}'
                return {'saved': False, 'reason': self.last_error_category}
        except requests.Timeout:
            self.last_error_category = 'timeout'
            return {'saved': False, 'reason': 'timeout'}
        except Exception:
            self.last_error_category = 'write_error'
            return {'saved': False, 'reason': 'write_error'}

        self.last_persist_monotonic = now_mono
        self.last_signature = state_signature(snapshot)
        self.last_success_at = self.now_fn()
        self.last_error_category = None
        self.persisted_this_process += 1

        # Keep storage bounded. Cleanup is deliberately infrequent and best effort.
        if self.persisted_this_process == 1 or self.persisted_this_process % 25 == 0:
            self.prune()
        return {'saved': True, 'reason': 'saved'}

    def prune(self):
        if not self.configured():
            return 0
        try:
            response = requests.get(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers=self.headers_fn(),
                params={
                    'select': 'id',
                    'category': f'eq.{HEALTH_HISTORY_CATEGORY}',
                    'order': 'created_at.desc',
                    'offset': self.max_records,
                    'limit': 250,
                },
                timeout=self.timeout_seconds,
            )
            if not response.ok:
                return 0
            rows = response.json() or []
            ids = [str(item.get('id')) for item in rows if item.get('id') is not None]
            if not ids:
                return 0
            delete = requests.delete(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers={**self.headers_fn(), 'Prefer': 'return=minimal'},
                params={'id': f"in.({','.join(ids)})"},
                timeout=self.timeout_seconds,
            )
            return len(ids) if delete.ok else 0
        except Exception:
            return 0

    def load(self, hours=24, limit=500):
        if not self.configured():
            return []
        hours = max(1, min(int(hours), 24 * 30))
        limit = max(1, min(int(limit), self.max_records))
        cutoff = self.now_fn() - timedelta(hours=hours)
        try:
            response = requests.get(
                f"{str(self.supabase_url_fn()).rstrip('/')}/rest/v1/memories",
                headers=self.headers_fn(),
                params={
                    'select': 'id,created_at,memories',
                    'category': f'eq.{HEALTH_HISTORY_CATEGORY}',
                    'created_at': f'gte.{_iso(cutoff)}',
                    'order': 'created_at.asc',
                    'limit': limit,
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
                if not isinstance(item, dict) or item.get('schema') != 'dependency_health_v1':
                    continue
                item['row_id'] = row.get('id')
                item['stored_at'] = row.get('created_at')
                output.append(item)
            return output
        except Exception:
            return []

    def summarize(self, hours=24, limit=500):
        records = self.load(hours=hours, limit=limit)
        summary = {
            'hours': max(1, min(int(hours), 24 * 30)),
            'samples': len(records),
            'services': {},
            'persistence': self.status(),
        }
        if not records:
            return summary

        for name in SERVICE_NAMES:
            raw_samples = []
            for record in records:
                item = (record.get('services') or {}).get(name)
                if isinstance(item, dict) and item.get('observed'):
                    raw_samples.append(item)
            samples = operation_checkpoints(records, name)
            if not samples:
                summary['services'][name] = {
                    'samples': 0,
                    'raw_snapshots': len(raw_samples),
                    'ignored_repeated_snapshots': len(raw_samples),
                    'latest_state': None,
                    'healthy_sample_rate': None,
                    'average_latency_ms': None,
                    'p95_latency_ms': None,
                    'latency_trend': 'insufficient_data',
                    'failure_samples': 0,
                    'unknown_outcome_samples': 0,
                }
                continue

            latencies = [item.get('last_latency_ms') for item in samples if item.get('last_latency_ms') is not None]
            healthy_count = sum(1 for item in samples if item.get('state') == 'healthy')
            failure_samples = sum(
                1 for item in samples
                if item.get('state') in {'degraded', 'unhealthy'} or item.get('last_error_category')
            )
            unknown_outcomes = sum(1 for item in samples if item.get('last_outcome_unknown'))
            error_categories = {}
            for item in samples:
                category = str(item.get('last_error_category') or '').strip()
                if category:
                    error_categories[category] = error_categories.get(category, 0) + 1
            summary['services'][name] = {
                'samples': len(samples),
                'raw_snapshots': len(raw_samples),
                'ignored_repeated_snapshots': max(0, len(raw_samples) - len(samples)),
                'latest_state': samples[-1].get('state'),
                'healthy_sample_rate': round(healthy_count / len(samples), 3),
                'average_latency_ms': int(round(sum(latencies) / len(latencies))) if latencies else None,
                'p95_latency_ms': _percentile(latencies, 0.95),
                'latency_trend': _trend(latencies),
                'failure_samples': failure_samples,
                'unknown_outcome_samples': unknown_outcomes,
                'error_categories': error_categories,
                'last_observed_at': samples[-1].get('last_observed_at'),
            }
        summary['first_recorded_at'] = records[0].get('recorded_at')
        summary['last_recorded_at'] = records[-1].get('recorded_at')
        return summary
