import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from persistent_health_history import (
    HEALTH_HISTORY_CATEGORY,
    PersistentHealthHistory,
    compact_snapshot,
    operation_checkpoints,
    state_signature,
)
import app_v2_10_2 as app2102


class Clock:
    def __init__(self):
        self.value = datetime(2026, 9, 15, 22, 0, tzinfo=timezone.utc)
        self.mono = 1000.0

    def now(self):
        return self.value

    def monotonic(self):
        return self.mono

    def advance(self, seconds):
        self.value += timedelta(seconds=seconds)
        self.mono += seconds


class FakeResponse:
    def __init__(self, ok=True, status_code=200, data=None):
        self.ok = ok
        self.status_code = status_code
        self._data = data if data is not None else []
        self.text = ''

    def json(self):
        return self._data


class PersistentHistoryUnitTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.snapshot = {
            'overall': 'warming_up',
            'started_at': '2026-09-15T21:55:00+00:00',
            'services': {
                'groq': {
                    'state': 'healthy', 'configured': True, 'observed': True,
                    'last_latency_ms': 600, 'p50_latency_ms': 600,
                    'p95_latency_ms': 600, 'window_success_rate': 1.0,
                    'consecutive_failures': 0, 'last_error_category': None,
                    'last_outcome_unknown': False, 'total_operations': 1,
                },
                'tavily': {
                    'state': 'unknown', 'configured': True, 'observed': False,
                    'last_latency_ms': None, 'p50_latency_ms': None,
                    'p95_latency_ms': None, 'window_success_rate': None,
                    'consecutive_failures': 0, 'last_error_category': None,
                    'last_outcome_unknown': False, 'total_operations': 0,
                },
            },
        }
        self.history = PersistentHealthHistory(
            supabase_url_fn=lambda: 'https://supabase.invalid',
            headers_fn=lambda: {'Authorization': 'Bearer test'},
            snapshot_fn=lambda: self.snapshot,
            version_fn=lambda: 'v2.10.2',
            interval_seconds=600,
            max_records=100,
            now_fn=self.clock.now,
            monotonic_fn=self.clock.monotonic,
        )

    def test_compact_snapshot_contains_no_raw_errors_or_secrets(self):
        record = compact_snapshot(self.snapshot, 'v2.10.2', self.clock.now())
        self.assertEqual(record['schema'], 'dependency_health_v1')
        self.assertEqual(record['services']['groq']['last_latency_ms'], 600)
        self.assertNotIn('last_error_summary', record['services']['groq'])

    def test_operation_checkpoints_exclude_repeated_unchanged_snapshots(self):
        records = []
        for index, total in enumerate([1, 1, 1, 2, 2]):
            record = compact_snapshot(
                self.snapshot,
                'v2.19.3.4',
                self.clock.now() + timedelta(minutes=index),
            )
            record['process_started_at'] = '2026-09-15T21:55:00+00:00'
            record['services']['groq']['total_operations'] = total
            record['services']['groq']['state'] = 'healthy' if total == 2 else 'unhealthy'
            records.append(record)
        samples = operation_checkpoints(records, 'groq')
        self.assertEqual(len(samples), 2)
        self.assertEqual([item['total_operations'] for item in samples], [1, 2])
        self.assertEqual(samples[-1]['state'], 'healthy')

    def test_state_signature_ignores_latency_changes(self):
        first = state_signature(self.snapshot)
        self.snapshot['services']['groq']['last_latency_ms'] = 9999
        second = state_signature(self.snapshot)
        self.assertEqual(first, second)

    @patch('persistent_health_history.requests.delete', return_value=FakeResponse())
    @patch('persistent_health_history.requests.get', return_value=FakeResponse(data=[]))
    @patch('persistent_health_history.requests.post', return_value=FakeResponse(status_code=201))
    def test_first_observation_persists_then_throttles_latency_only_changes(self, post, get, delete):
        first = self.history.maybe_persist()
        self.assertTrue(first['saved'])
        self.snapshot['services']['groq']['last_latency_ms'] = 700
        second = self.history.maybe_persist()
        self.assertFalse(second['saved'])
        self.assertEqual(second['reason'], 'not_due')
        self.assertEqual(post.call_count, 1)

    @patch('persistent_health_history.requests.delete', return_value=FakeResponse())
    @patch('persistent_health_history.requests.get', return_value=FakeResponse(data=[]))
    @patch('persistent_health_history.requests.post', return_value=FakeResponse(status_code=201))
    def test_meaningful_state_change_persists_immediately(self, post, get, delete):
        self.history.maybe_persist()
        self.snapshot['services']['tavily']['state'] = 'healthy'
        self.snapshot['services']['tavily']['observed'] = True
        self.snapshot['services']['tavily']['last_latency_ms'] = 2000
        result = self.history.maybe_persist()
        self.assertTrue(result['saved'])
        self.assertEqual(post.call_count, 2)

    @patch('persistent_health_history.requests.post', side_effect=RuntimeError('storage unavailable'))
    def test_persistence_failure_is_reported_not_raised(self, post):
        result = self.history.maybe_persist()
        self.assertFalse(result['saved'])
        self.assertEqual(result['reason'], 'write_error')

    @patch('persistent_health_history.requests.get')
    def test_summary_calculates_cross_restart_trends(self, get):
        rows = []
        for index, latency in enumerate([1000, 900, 600, 500]):
            recorded = self.clock.now() + timedelta(minutes=index * 10)
            record = compact_snapshot(self.snapshot, 'v2.10.2', recorded)
            record['services']['groq']['last_latency_ms'] = latency
            record['services']['groq']['state'] = 'healthy'
            record['services']['groq']['total_operations'] = index + 1
            rows.append({
                'id': index + 1,
                'created_at': recorded.isoformat(),
                'memories': json.dumps(record),
            })
        get.return_value = FakeResponse(data=rows)
        summary = self.history.summarize(hours=24)
        groq = summary['services']['groq']
        self.assertEqual(groq['samples'], 4)
        self.assertEqual(groq['healthy_sample_rate'], 1.0)
        self.assertEqual(groq['latency_trend'], 'faster')
        self.assertGreater(groq['p95_latency_ms'], 0)

    @patch('persistent_health_history.requests.get')
    def test_summary_reports_operation_checkpoints_not_forced_duplicates(self, get):
        rows = []
        for index, total in enumerate([1, 1, 1, 2, 2]):
            recorded = self.clock.now() + timedelta(minutes=index)
            record = compact_snapshot(self.snapshot, 'v2.19.3.4', recorded)
            record['process_started_at'] = '2026-09-15T21:55:00+00:00'
            record['services']['groq']['total_operations'] = total
            record['services']['groq']['state'] = 'unhealthy' if total == 1 else 'healthy'
            record['services']['groq']['last_error_category'] = 'quota' if total == 1 else None
            rows.append({
                'id': index + 1,
                'created_at': recorded.isoformat(),
                'memories': json.dumps(record),
            })
        get.return_value = FakeResponse(data=rows)
        groq = self.history.summarize(hours=24)['services']['groq']
        self.assertEqual(groq['samples'], 2)
        self.assertEqual(groq['raw_snapshots'], 5)
        self.assertEqual(groq['ignored_repeated_snapshots'], 3)
        self.assertEqual(groq['healthy_sample_rate'], 0.5)
        self.assertEqual(groq['failure_samples'], 1)
        self.assertEqual(groq['error_categories'], {'quota': 1})


class PersistentHistoryIntegrationTests(unittest.TestCase):
    def setUp(self):
        app2102.DEPENDENCIES.reset()
        self.client = app2102.app.test_client()

    def test_health_history_category_is_hidden_from_normal_memory(self):
        self.assertIn(HEALTH_HISTORY_CATEGORY, app2102.base.SPECIAL_MEMORY_CATEGORIES)

    def test_history_failure_never_breaks_observed_operation(self):
        with patch.object(app2102.HISTORY, 'maybe_persist', side_effect=RuntimeError('boom')):
            result = app2102.record_success_persistent('groq', 'completion', 123)
        self.assertIsNone(result)
        snapshot = app2102.v210.dependency_snapshot(include_errors=False)
        self.assertEqual(snapshot['services']['groq']['state'], 'unconfigured')
        self.assertEqual(snapshot['services']['groq']['total_operations'], 1)

    def test_history_chat_command_returns_persisted_summary_without_probes(self):
        fake_summary = {
            'hours': 24,
            'samples': 4,
            'services': {
                'groq': {
                    'samples': 4,
                    'latest_state': 'healthy',
                    'healthy_sample_rate': 1.0,
                    'average_latency_ms': 700,
                    'p95_latency_ms': 900,
                    'latency_trend': 'stable',
                    'failure_samples': 0,
                    'unknown_outcome_samples': 0,
                }
            },
            'persistence': {'last_error_category': None},
        }
        with patch.object(app2102.HISTORY, 'maybe_persist', return_value={'saved': True}), patch.object(
            app2102.HISTORY, 'summarize', return_value=fake_summary
        ):
            payload, status = app2102.base.handle_message('Show health history')
        self.assertEqual(status, 200)
        self.assertEqual(payload['type'], 'dependency_health_history')
        self.assertIn(
            'no Groq, Gemini, Tavily, or n8n probe requests were sent',
            payload['reply'],
        )
        self.assertIn('Groq: healthy', payload['reply'])

    def test_detailed_history_route_requires_authentication(self):
        response = self.client.get('/diagnostics/dependencies/history')
        self.assertEqual(response.status_code, 401)

    def test_status_exposes_safe_persistence_state(self):
        response = self.client.get('/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['version_short'], app2102.base.VERSION_SHORT)
        self.assertIn('persistent_dependency_health_history', data['capabilities'])
        self.assertIn('health_history_persistence', data)

    def test_developer_grounding_includes_persistent_history_module(self):
        files = app2102.v210.v297._safe_source_files()
        self.assertIn('persistent_health_history.py', files)


if __name__ == '__main__':
    unittest.main()
