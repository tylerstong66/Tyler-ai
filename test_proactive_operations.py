import unittest
from unittest.mock import MagicMock, patch

from proactive_operations import (
    INCIDENT_CATEGORY,
    OPS_PREFERENCE_CATEGORY,
    ProactiveOperations,
    incident_id_for,
    recommended_response,
    safe_diagnostic_bundle,
)


class FakeHistory:
    max_records = 100

    def summarize(self, hours=24, limit=100):
        return {
            'hours': hours,
            'samples': 6,
            'services': {
                'groq': {
                    'samples': 6,
                    'latest_state': 'unhealthy',
                    'healthy_sample_rate': 0.5,
                    'average_latency_ms': 900,
                    'p95_latency_ms': 1400,
                    'latency_trend': 'slower',
                    'failure_samples': 3,
                    'unknown_outcome_samples': 0,
                },
                'n8n': {
                    'samples': 6,
                    'latest_state': 'healthy',
                    'healthy_sample_rate': 1.0,
                    'average_latency_ms': 500,
                    'p95_latency_ms': 650,
                    'latency_trend': 'stable',
                    'failure_samples': 0,
                    'unknown_outcome_samples': 0,
                },
            },
        }


def snapshot(n8n_state='healthy'):
    return {
        'overall': 'degraded',
        'services': {
            'groq': {
                'state': 'unhealthy',
                'configured': True,
                'observed': True,
                'last_latency_ms': 1200,
                'p50_latency_ms': 800,
                'p95_latency_ms': 1500,
                'window_success_rate': 0.5,
                'consecutive_failures': 2,
                'last_error_category': 'http_500',
                'last_outcome_unknown': False,
                'total_operations': 8,
            },
            'n8n': {
                'state': n8n_state,
                'configured': True,
                'observed': True,
                'last_latency_ms': 500,
                'p50_latency_ms': 500,
                'p95_latency_ms': 600,
                'window_success_rate': 1.0,
                'consecutive_failures': 0,
                'last_error_category': None,
                'last_outcome_unknown': False,
                'total_operations': 3,
            },
        },
    }


def critical_event(service='groq', kind='live_unhealthy', event_type='raised'):
    return {
        'event': event_type,
        'alert': {
            'fingerprint': f'{service}:{kind}',
            'service': service,
            'severity': 'critical',
            'kind': kind,
            'title': f'{service} incident',
            'message': f'{service} has a serious problem.',
            'evidence': {'consecutive_failures': 2},
        },
    }


class ProactiveOperationsUnitTests(unittest.TestCase):
    def test_incident_id_is_stable(self):
        self.assertEqual(incident_id_for('groq:live_unhealthy'), incident_id_for('groq:live_unhealthy'))
        self.assertTrue(incident_id_for('groq:live_unhealthy').startswith('INC-'))

    def test_unknown_outcome_plan_never_allows_automatic_retry(self):
        plan = recommended_response({
            'service': 'n8n',
            'kind': 'unknown_external_outcome',
        })
        self.assertIn('Verify', plan['summary'])
        self.assertTrue(any('retry' in item.lower() for item in plan['approval_required_for']))
        self.assertTrue(any('retry uncertain side effect' in item.lower() for item in plan['never_automatic']))
        self.assertNotIn('retry uncertain side effect', plan['automatic_actions_allowed'])

    def test_diagnostic_bundle_contains_no_raw_error_text_or_secret(self):
        live = snapshot()
        live['services']['groq']['last_error_category'] = 'authorization=Bearer SUPERSECRET'
        bundle = safe_diagnostic_bundle(
            critical_event()['alert'],
            live,
            FakeHistory().summarize(),
        )
        text = str(bundle)
        self.assertNotIn('SUPERSECRET', text)
        self.assertIn('redacted_sensitive_error', text)

    def make_ops(self, email_fn=None, n8n_state='healthy'):
        return ProactiveOperations(
            intelligence=MagicMock(),
            history=FakeHistory(),
            snapshot_fn=lambda: snapshot(n8n_state=n8n_state),
            supabase_url_fn=lambda: 'https://example.supabase.co',
            headers_fn=lambda: {'apikey': 'test', 'Authorization': 'Bearer test'},
            version_fn=lambda: 'v2.12.0',
            email_fn=email_fn,
            default_email_fn=lambda: 'owner@example.com',
        )

    def test_raised_event_creates_incident_but_email_is_disabled_by_default(self):
        ops = self.make_ops(email_fn=MagicMock())
        with patch.object(ops, '_post_memory', return_value=True):
            result = ops.process_events([critical_event()])
        self.assertEqual(len(result), 1)
        incident = result[0]['incident']
        self.assertEqual(incident['status'], 'open')
        self.assertFalse(incident['automatic_remediation_performed'])
        self.assertFalse(result[0]['notification']['attempted'])
        self.assertEqual(result[0]['notification']['reason'], 'disabled')

    def test_explicit_opt_in_persists_and_allows_confirmed_critical_email(self):
        email = MagicMock(return_value={'success': True, 'sent': True, 'message_id': 'msg-1'})
        ops = self.make_ops(email_fn=email)
        with patch.object(ops, '_post_memory', return_value=True):
            preference = ops.set_email_notifications(True)
            result = ops.process_events([critical_event()])
        self.assertTrue(preference['saved'])
        self.assertTrue(preference['enabled'])
        email.assert_called_once()
        self.assertTrue(result[0]['notification']['sent'])

    def test_n8n_incident_never_emails_through_n8n_even_when_opted_in(self):
        email = MagicMock(return_value={'success': True, 'sent': True, 'message_id': 'msg-1'})
        ops = self.make_ops(email_fn=email)
        with patch.object(ops, '_post_memory', return_value=True):
            ops.set_email_notifications(True)
            result = ops.process_events([
                critical_event(service='n8n', kind='unknown_external_outcome')
            ])
        email.assert_not_called()
        self.assertEqual(result[0]['notification']['reason'], 'n8n_not_safe')

    def test_unhealthy_n8n_blocks_alert_email_for_other_service(self):
        email = MagicMock(return_value={'success': True, 'sent': True, 'message_id': 'msg-1'})
        ops = self.make_ops(email_fn=email, n8n_state='unhealthy')
        with patch.object(ops, '_post_memory', return_value=True):
            ops.set_email_notifications(True)
            result = ops.process_events([critical_event(service='groq')])
        email.assert_not_called()
        self.assertEqual(result[0]['notification']['reason'], 'n8n_not_safe')

    def test_unconfirmed_email_receipt_is_not_reported_as_sent(self):
        email = MagicMock(return_value={'success': True, 'sent': True})
        ops = self.make_ops(email_fn=email)
        with patch.object(ops, '_post_memory', return_value=True):
            ops.set_email_notifications(True)
            result = ops.process_events([critical_event()])
        self.assertFalse(result[0]['notification']['sent'])
        self.assertEqual(result[0]['notification']['reason'], 'unconfirmed_receipt')

    def test_resolved_event_closes_incident_without_automatic_remediation(self):
        ops = self.make_ops()
        with patch.object(ops, '_post_memory', return_value=True):
            result = ops.process_events([
                critical_event(event_type='resolved')
            ])
        incident = result[0]['incident']
        self.assertEqual(incident['status'], 'resolved')
        self.assertFalse(incident['automatic_remediation_performed'])

    def test_incident_and_preference_categories_are_distinct(self):
        self.assertNotEqual(INCIDENT_CATEGORY, OPS_PREFERENCE_CATEGORY)


class V212IntegrationTests(unittest.TestCase):
    def test_v212_import_and_safety_flags(self):
        import app_v2_12 as app212
        self.assertEqual(app212.VERSION_SHORT, 'v2.12.0')
        self.assertIn(INCIDENT_CATEGORY, app212.base.SPECIAL_MEMORY_CATEGORIES)
        self.assertIn(OPS_PREFERENCE_CATEGORY, app212.base.SPECIAL_MEMORY_CATEGORIES)
        status = app212.OPS.status()
        self.assertFalse(status['automatic_remediation_enabled'])
        self.assertFalse(status['active_probes'])

    def test_proactive_status_command_is_side_effect_free(self):
        import app_v2_12 as app212
        with patch.object(app212.OPS, 'recent_incidents', return_value=[]), patch.object(
            app212.OPS,
            'status',
            return_value={
                'email_notifications_enabled': False,
                'automatic_remediation_enabled': False,
                'active_probes': False,
            },
        ):
            payload, status = app212.handle_message_v212('Show proactive operations')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        self.assertIn('Automatic production remediation: disabled', payload['reply'])

    def test_enable_email_command_requires_explicit_phrase_and_persists(self):
        import app_v2_12 as app212
        with patch.object(
            app212.OPS,
            'set_email_notifications',
            return_value={'saved': True, 'enabled': True},
        ) as setter:
            payload, status = app212.handle_message_v212('Enable proactive alert emails')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        setter.assert_called_once_with(True)
        self.assertIn('enabled', payload['reply'].lower())

    def test_normal_health_event_creates_incident_and_preserves_original_reply(self):
        import app_v2_12 as app212
        event = critical_event()
        fake_incident = {
            'incident': {
                'incident_id': 'INC-1234567890',
                'status': 'open',
                'event': 'raised',
                'service': 'groq',
                'severity': 'critical',
                'title': 'Groq incident',
                'recommended_response': {'summary': 'Inspect Groq safely.'},
            },
            'saved': True,
            'notification': {'attempted': False, 'reason': 'disabled'},
        }
        with patch.object(
            app212,
            '_PRE_HEALTH_HANDLE_MESSAGE',
            return_value=({'success': True, 'reply': 'Original answer', 'used_tools': []}, 200),
        ), patch.object(
            app212.INTELLIGENCE,
            'sync_and_get_events',
            return_value=[event],
        ), patch.object(
            app212.OPS,
            'process_events',
            return_value=[fake_incident],
        ):
            payload, status = app212.handle_message_v212('normal request')
        self.assertEqual(status, 200)
        self.assertIn('Original answer', payload['reply'])
        self.assertIn('INC-1234567890', payload['reply'])
        self.assertIn('proactive_operations', payload['used_tools'])

    def test_incident_diagnostics_route_requires_authentication(self):
        import app_v2_12 as app212
        with app212.app.test_client() as client:
            response = client.get('/diagnostics/incidents')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
