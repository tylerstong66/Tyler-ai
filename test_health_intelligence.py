import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from health_intelligence import (
    HealthIntelligence,
    detect_service_alert,
    historical_signals,
)


class FakeHistory:
    def __init__(self, records=None):
        self.records = list(records or [])
        self.max_records = 1500
        self.loads = 0

    def load(self, hours=24, limit=500):
        self.loads += 1
        return list(self.records)


def record(service, state='healthy', latency=100, error=None, unknown=False):
    return {
        'schema': 'dependency_health_v1',
        'recorded_at': '2026-09-15T20:00:00+00:00',
        'services': {
            service: {
                'observed': True,
                'state': state,
                'last_latency_ms': latency,
                'last_error_category': error,
                'last_outcome_unknown': unknown,
            }
        },
    }


def operation_record(service, total, state='healthy', latency=100, error=None):
    item = record(service, state=state, latency=latency, error=error)
    item['process_started_at'] = '2026-09-15T19:00:00+00:00'
    item['services'][service]['total_operations'] = total
    return item


def snapshot(service='groq', state='healthy', latency=100, consecutive=0, error=None, unknown=False):
    services = {
        name: {
            'configured': True,
            'observed': False,
            'state': 'unknown',
            'last_latency_ms': None,
            'consecutive_failures': 0,
            'last_error_category': None,
            'last_outcome_unknown': False,
        }
        for name in ['groq', 'tavily', 'supabase', 'n8n']
    }
    services[service] = {
        'configured': True,
        'observed': True,
        'state': state,
        'last_latency_ms': latency,
        'consecutive_failures': consecutive,
        'last_error_category': error,
        'last_outcome_unknown': unknown,
    }
    return {'overall': state, 'services': services}


class HealthIntelligenceUnitTests(unittest.TestCase):
    def test_healthy_live_service_with_no_history_has_no_alert(self):
        alert = detect_service_alert('groq', snapshot()['services']['groq'], {})
        self.assertIsNone(alert)

    def test_unknown_n8n_side_effect_outcome_is_critical_and_not_auto_retried(self):
        item = snapshot(
            service='n8n',
            state='degraded',
            error='unknown_outcome',
            unknown=True,
        )['services']['n8n']
        alert = detect_service_alert('n8n', item, {})
        self.assertEqual(alert['severity'], 'critical')
        self.assertEqual(alert['kind'], 'unknown_external_outcome')
        self.assertIn('Verify', alert['message'])
        self.assertNotIn('automatic', alert['message'].lower())
        self.assertNotIn('retry automatically', alert['message'].lower())

    def test_repeated_failures_are_critical(self):
        item = snapshot(
            service='tavily',
            state='unhealthy',
            consecutive=2,
            error='timeout',
        )['services']['tavily']
        alert = detect_service_alert('tavily', item, {})
        self.assertEqual(alert['severity'], 'critical')
        self.assertEqual(alert['kind'], 'live_unhealthy')

    def test_historical_reliability_warning_requires_enough_samples(self):
        few = {'samples': 4, 'healthy_rate': 0.50, 'failure_samples': 2}
        item = snapshot(service='supabase')['services']['supabase']
        self.assertIsNone(detect_service_alert('supabase', item, few))

        enough = {'samples': 5, 'healthy_rate': 0.80, 'failure_samples': 1}
        alert = detect_service_alert('supabase', item, enough)
        self.assertEqual(alert['severity'], 'warning')
        self.assertEqual(alert['kind'], 'historical_reliability')

    def test_historical_reliability_can_be_critical(self):
        item = snapshot(service='groq')['services']['groq']
        history = {'samples': 10, 'healthy_rate': 0.60, 'failure_samples': 4}
        alert = detect_service_alert('groq', item, history)
        self.assertEqual(alert['severity'], 'critical')

    def test_latency_regression_requires_sample_count_and_absolute_increase(self):
        item = snapshot(service='groq')['services']['groq']
        noisy_small = {
            'samples': 8,
            'healthy_rate': 1.0,
            'older_latency_ms': 50,
            'newer_latency_ms': 100,
            'latency_change_pct': 100.0,
        }
        self.assertIsNone(detect_service_alert('groq', item, noisy_small))

        meaningful = {
            'samples': 8,
            'healthy_rate': 1.0,
            'older_latency_ms': 200,
            'newer_latency_ms': 500,
            'latency_change_pct': 150.0,
        }
        alert = detect_service_alert('groq', item, meaningful)
        self.assertEqual(alert['severity'], 'warning')
        self.assertEqual(alert['kind'], 'latency_regression')

    def test_large_latency_regression_can_be_critical(self):
        item = snapshot(service='tavily')['services']['tavily']
        history = {
            'samples': 8,
            'healthy_rate': 1.0,
            'older_latency_ms': 250,
            'newer_latency_ms': 900,
            'latency_change_pct': 260.0,
        }
        alert = detect_service_alert('tavily', item, history)
        self.assertEqual(alert['severity'], 'critical')

    def test_historical_signals_compare_older_and_newer_halves(self):
        records = [record('groq', latency=value) for value in [100, 110, 120, 200, 220, 240]]
        signals = historical_signals(records, 'groq')
        self.assertEqual(signals['samples'], 6)
        self.assertEqual(signals['older_latency_ms'], 110)
        self.assertEqual(signals['newer_latency_ms'], 220)
        self.assertEqual(signals['latency_change_pct'], 100.0)

    def test_historical_signals_ignore_repeated_last_known_state(self):
        records = [
            operation_record('groq', 1, state='unhealthy', error='quota'),
            operation_record('groq', 1, state='unhealthy', error='quota'),
            operation_record('groq', 1, state='unhealthy', error='quota'),
            operation_record('groq', 2, state='healthy'),
            operation_record('groq', 2, state='healthy'),
        ]
        signals = historical_signals(records, 'groq')
        self.assertEqual(signals['samples'], 2)
        self.assertEqual(signals['failure_samples'], 1)
        self.assertEqual(signals['healthy_rate'], 0.5)

    def test_raised_alert_is_deduplicated_and_resolution_is_emitted_once(self):
        now = [datetime(2026, 9, 15, 22, 0, tzinfo=timezone.utc)]
        current = [snapshot(service='groq', state='unhealthy', consecutive=2, error='timeout')]
        intelligence = HealthIntelligence(
            history=FakeHistory(),
            snapshot_fn=lambda: current[0],
            supabase_url_fn=lambda: '',
            headers_fn=lambda: {},
            version_fn=lambda: 'v2.11.0',
            now_fn=lambda: now[0],
            monotonic_fn=lambda: 100.0,
        )

        first = intelligence.sync_and_get_events()
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]['event'], 'raised')
        self.assertEqual(intelligence.sync_and_get_events(), [])

        current[0] = snapshot(service='groq', state='healthy')
        resolved = intelligence.sync_and_get_events()
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0]['event'], 'resolved')
        self.assertEqual(intelligence.sync_and_get_events(), [])

    def test_history_reads_are_cached_between_normal_evaluations(self):
        history = FakeHistory([record('groq', latency=100)] * 6)
        intelligence = HealthIntelligence(
            history=history,
            snapshot_fn=lambda: snapshot(),
            supabase_url_fn=lambda: '',
            headers_fn=lambda: {},
            version_fn=lambda: 'v2.11.0',
            monotonic_fn=lambda: 100.0,
        )
        intelligence.evaluate()
        intelligence.evaluate()
        self.assertEqual(history.loads, 1)


class HealthIntelligenceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app_v2_11 as app211
        cls.app211 = app211

    def test_alert_state_category_is_hidden_from_normal_memory(self):
        self.assertIn('dependency_health_alert', self.app211.base.SPECIAL_MEMORY_CATEGORIES)

    def test_developer_grounding_includes_health_intelligence_module(self):
        files = self.app211.v210.v297._safe_source_files()
        self.assertIn('health_intelligence.py', files)

    def test_explicit_health_alert_command_does_not_require_groq(self):
        with patch.object(self.app211.INTELLIGENCE, 'sync_and_get_events', return_value=[]), patch.object(
            self.app211.INTELLIGENCE,
            'active_alerts',
            return_value=[],
        ):
            payload, status = self.app211.handle_message_v211('Show health alerts')
        self.assertEqual(status, 200)
        self.assertEqual(payload['type'], 'dependency_health_alerts')
        self.assertEqual(payload['health_alerts'], [])
        self.assertIn('no active alerts', payload['reply'].lower())
        self.assertEqual(payload['used_tools'], ['dependency_health_intelligence'])

    def test_normal_response_gets_one_new_warning_appended(self):
        event = {
            'event': 'raised',
            'recorded_at': '2026-09-15T22:00:00+00:00',
            'alert': {
                'fingerprint': 'tavily:live_degraded',
                'service': 'tavily',
                'severity': 'warning',
                'kind': 'live_degraded',
                'title': 'Tavily is degraded',
                'message': 'Tavily has a recent failure.',
                'evidence': {},
            },
        }
        with patch.object(
            self.app211,
            '_PREVIOUS_HANDLE_MESSAGE',
            return_value=({'reply': 'Original answer', 'used_tools': ['reason']}, 200),
        ), patch.object(
            self.app211.INTELLIGENCE,
            'sync_and_get_events',
            return_value=[event],
        ):
            payload, status = self.app211.handle_message_v211('Normal user request')
        self.assertEqual(status, 200)
        self.assertIn('Original answer', payload['reply'])
        self.assertIn('Health warning', payload['reply'])
        self.assertIn('Tavily is degraded', payload['reply'])
        self.assertIn('dependency_health_intelligence', payload['used_tools'])

    def test_intelligence_failure_never_breaks_original_response(self):
        with patch.object(
            self.app211,
            '_PREVIOUS_HANDLE_MESSAGE',
            return_value=({'reply': 'Still works', 'used_tools': []}, 200),
        ), patch.object(
            self.app211.INTELLIGENCE,
            'sync_and_get_events',
            side_effect=RuntimeError('diagnostics failed'),
        ):
            payload, status = self.app211.handle_message_v211('Normal user request')
        self.assertEqual(status, 200)
        self.assertEqual(payload['reply'], 'Still works')

    def test_detailed_alert_route_requires_authentication(self):
        client = self.app211.app.test_client()
        response = client.get('/diagnostics/dependencies/alerts')
        self.assertEqual(response.status_code, 401)

    def test_status_exposes_health_intelligence_capability_without_history_probe(self):
        client = self.app211.app.test_client()
        with patch.object(self.app211.HISTORY, 'load') as load:
            response = client.get('/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['version_short'], 'v2.11.0')
        self.assertIn('dependency_health_intelligence', data['capabilities'])
        load.assert_not_called()


if __name__ == '__main__':
    unittest.main()
