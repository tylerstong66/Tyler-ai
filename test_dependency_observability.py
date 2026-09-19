import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from dependency_observability import DependencyObservability, classify_error
import app_v2_10 as app210


class Clock:
    def __init__(self):
        self.value = datetime(2026, 9, 15, 21, 30, tzinfo=timezone.utc)

    def now(self):
        return self.value

    def advance(self, seconds):
        self.value += timedelta(seconds=seconds)


class DependencyObservabilityUnitTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.telemetry = DependencyObservability(history_size=20, now_fn=self.clock.now)

    def test_unknown_until_real_operation_is_observed(self):
        snapshot = self.telemetry.snapshot({'groq': True})
        self.assertEqual(snapshot['overall'], 'warming_up')
        self.assertEqual(snapshot['services']['groq']['state'], 'unknown')
        self.assertFalse(snapshot['active_probes'])

    def test_quota_errors_are_classified_as_rate_limits(self):
        self.assertEqual(classify_error('daily token quota exhausted'), 'rate_limit')
        self.assertEqual(classify_error('RESOURCE_EXHAUSTED'), 'rate_limit')

    def test_success_records_latency_and_health(self):
        self.telemetry.record_success('groq', 'completion', 123)
        snapshot = self.telemetry.snapshot({'groq': True})
        service = snapshot['services']['groq']
        self.assertEqual(service['state'], 'healthy')
        self.assertEqual(service['last_latency_ms'], 123)
        self.assertEqual(service['window_success_rate'], 1.0)
        self.assertEqual(service['p50_latency_ms'], 123)

    def test_one_failure_is_degraded_two_consecutive_failures_are_unhealthy(self):
        self.telemetry.record_success('tavily', 'search', 50)
        self.telemetry.record_failure('tavily', 'search', 60, RuntimeError('timeout'))
        degraded = self.telemetry.snapshot({'tavily': True})
        self.assertEqual(degraded['services']['tavily']['state'], 'degraded')

        self.telemetry.record_failure('tavily', 'search', 70, RuntimeError('timeout'))
        unhealthy = self.telemetry.snapshot({'tavily': True})
        self.assertEqual(unhealthy['services']['tavily']['state'], 'unhealthy')
        self.assertEqual(unhealthy['overall'], 'unhealthy')

    def test_stale_is_not_reported_as_live_healthy(self):
        self.telemetry.record_success('supabase', 'read', 20)
        self.clock.advance(1900)
        snapshot = self.telemetry.snapshot({'supabase': True}, stale_after_seconds=1800)
        self.assertEqual(snapshot['services']['supabase']['state'], 'stale')
        self.assertEqual(snapshot['overall'], 'stale')

    def test_detailed_errors_are_sanitized(self):
        self.telemetry.record_failure(
            'groq',
            'completion',
            10,
            RuntimeError('Bearer abcdef123 secret=supersecret https://example.com/private'),
        )
        public = self.telemetry.snapshot({'groq': True}, include_errors=False)
        self.assertNotIn('last_error_summary', public['services']['groq'])

        private = self.telemetry.snapshot({'groq': True}, include_errors=True)
        error = private['services']['groq']['last_error_summary']
        self.assertNotIn('abcdef123', error)
        self.assertNotIn('supersecret', error)
        self.assertNotIn('example.com', error)
        self.assertIn('<redacted', error)

    def test_unknown_outcome_is_explicit(self):
        self.telemetry.record_failure(
            'n8n',
            'email_dispatch',
            300,
            RuntimeError('Email outcome is unknown.'),
            side_effect=True,
            outcome_unknown=True,
        )
        snapshot = self.telemetry.snapshot({'n8n': True})
        service = snapshot['services']['n8n']
        self.assertTrue(service['last_outcome_unknown'])
        self.assertEqual(service['last_error_category'], 'unknown_outcome')


class DependencyObservabilityIntegrationTests(unittest.TestCase):
    def setUp(self):
        app210.DEPENDENCIES.reset()
        self.client = app210.app.test_client()

    def test_health_route_is_passive_and_always_liveness_200(self):
        before = app210.dependency_snapshot(include_errors=False)
        before_total = sum(
            item.get('total_operations', 0)
            for item in before.get('services', {}).values()
        )
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['process'], 'alive')
        self.assertFalse(data['active_probes'])
        after = app210.dependency_snapshot(include_errors=False)
        after_total = sum(
            item.get('total_operations', 0)
            for item in after.get('services', {}).values()
        )
        self.assertEqual(before_total, after_total)

    def test_public_status_does_not_expose_error_text(self):
        app210.DEPENDENCIES.record_failure(
            'groq',
            'completion',
            10,
            RuntimeError('Bearer secret-value https://private.example/path'),
        )
        response = self.client.get('/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['version_short'], app210.base.VERSION_SHORT)
        service = data['dependency_observability']['services']['groq']
        self.assertNotIn('last_error_summary', service)
        self.assertIn('dependency_observability', data['capabilities'])

    def test_detailed_dependency_route_requires_authentication(self):
        response = self.client.get('/diagnostics/dependencies')
        self.assertEqual(response.status_code, 401)

    def test_health_chat_command_is_passive(self):
        with patch.object(app210.base, 'GROQ_API_KEY', 'configured'), patch.object(
            app210.base, 'TAVILY_API_KEY', 'configured'
        ), patch.object(app210.base, 'SUPABASE_URL', 'https://supabase.invalid'), patch.object(
            app210.base, 'SUPABASE_KEY', 'configured'
        ), patch.object(app210.base, 'N8N_WEBHOOK_URL', 'https://n8n.invalid'), patch.object(
            app210.base, 'N8N_WEBHOOK_KEY', 'configured'
        ):
            payload, status = app210.base.handle_message('Show system health')
        self.assertEqual(status, 200)
        self.assertEqual(payload['type'], 'dependency_health')
        self.assertIn('Passive telemetry only', payload['reply'])
        self.assertEqual(payload['used_tools'], ['dependency_telemetry'])
        total = sum(
            item.get('total_operations', 0)
            for item in payload['dependency_health']['services'].values()
        )
        self.assertEqual(total, 0)

    def test_groq_wrapper_records_real_success(self):
        with patch.object(app210.base, 'GROQ_API_KEY', 'configured'), patch.object(
            app210, '_ORIGINAL_GROQ', return_value='answer'
        ):
            result = app210.groq_observed([{'role': 'user', 'content': 'hello'}])
            snapshot = app210.dependency_snapshot(include_errors=False)
        self.assertEqual(result, 'answer')
        groq = snapshot['services']['groq']
        self.assertEqual(groq['total_operations'], 1)
        self.assertEqual(groq['state'], 'healthy')

    def test_n8n_dispatch_failure_marks_unknown_outcome(self):
        with patch.object(
            app210,
            '_ORIGINAL_SEND_EMAIL',
            side_effect=RuntimeError('Email outcome is unknown. Check n8n execution history before sending again.'),
        ):
            with self.assertRaises(RuntimeError):
                app210.send_email_via_n8n_observed('subject', 'body')
        snapshot = app210.dependency_snapshot(include_errors=False)
        n8n = snapshot['services']['n8n']
        self.assertTrue(n8n['last_outcome_unknown'])
        self.assertEqual(n8n['last_error_category'], 'unknown_outcome')

    def test_n8n_preflight_configuration_failure_is_not_unknown_outcome(self):
        error = RuntimeError('N8N_WEBHOOK_KEY is not configured')
        self.assertFalse(app210._n8n_outcome_unknown(error))

    def test_developer_grounding_includes_observability_module(self):
        files = app210.v297._safe_source_files()
        self.assertIn('dependency_observability.py', files)


if __name__ == '__main__':
    unittest.main()
