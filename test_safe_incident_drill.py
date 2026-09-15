import unittest
from unittest.mock import MagicMock, patch

import app_v2_12_1 as app2121


class SafeIncidentDrillTests(unittest.TestCase):
    def test_command_requires_explicit_drill_phrase(self):
        self.assertTrue(app2121.safe_drill_request('Run proactive operations test'))
        self.assertTrue(app2121.safe_drill_request('Run safe incident drill'))
        self.assertFalse(app2121.safe_drill_request('test proactive operations someday'))
        self.assertFalse(app2121.safe_drill_request('show proactive operations'))

    def test_disabled_proactive_email_prevents_drill(self):
        with patch.object(
            app2121.OPS,
            'status',
            return_value={'email_notifications_enabled': False},
        ), patch.object(app2121.base, 'send_email_via_n8n') as send:
            payload = app2121.run_safe_incident_drill()
        self.assertFalse(payload['success'])
        self.assertFalse(payload['drill']['started'])
        self.assertEqual(payload['drill']['reason'], 'proactive_alert_emails_disabled')
        send.assert_not_called()

    def test_unsafe_n8n_state_prevents_drill(self):
        with patch.object(
            app2121.OPS,
            'status',
            return_value={'email_notifications_enabled': True},
        ), patch.object(
            app2121,
            '_drill_n8n_ready',
            return_value=(False, 'n8n has an unresolved unknown-outcome event.'),
        ), patch.object(app2121.base, 'send_email_via_n8n') as send:
            payload = app2121.run_safe_incident_drill()
        self.assertFalse(payload['success'])
        self.assertFalse(payload['drill']['started'])
        send.assert_not_called()

    def test_successful_drill_sends_exactly_one_email_and_closes_incident(self):
        raised = {
            'incident_id': 'INC-DRILL00001',
            'status': 'open',
            'event': 'raised',
            'service': 'drill',
            'severity': 'critical',
            'title': app2121.DRILL_TITLE,
        }
        resolved = {
            'incident_id': 'INC-DRILL00001',
            'status': 'resolved',
            'event': 'resolved',
            'service': 'drill',
            'severity': 'critical',
            'title': app2121.DRILL_TITLE,
        }
        sender = MagicMock(return_value={
            'success': True,
            'sent': True,
            'message_id': 'gmail-test-1',
        })
        with patch.object(
            app2121.OPS,
            'status',
            return_value={'email_notifications_enabled': True},
        ), patch.object(
            app2121,
            '_drill_n8n_ready',
            return_value=(True, ''),
        ), patch.object(
            app2121,
            '_persist_drill_event',
            side_effect=[(raised, True), (resolved, True)],
        ) as persist, patch.object(
            app2121.base,
            'send_email_via_n8n',
            sender,
        ):
            payload = app2121.run_safe_incident_drill()

        self.assertTrue(payload['success'])
        self.assertTrue(payload['drill']['passed'])
        self.assertTrue(payload['drill']['simulation'])
        self.assertTrue(payload['drill']['receipt_confirmed'])
        self.assertTrue(payload['drill']['resolved_saved'])
        self.assertFalse(payload['drill']['real_dependency_health_changed'])
        self.assertFalse(payload['drill']['automatic_remediation_performed'])
        self.assertFalse(payload['drill']['production_configuration_changed'])
        self.assertEqual(payload['incident']['status'], 'resolved')
        self.assertEqual(sender.call_count, 1)
        self.assertEqual(persist.call_count, 2)
        self.assertIn('SIMULATION ONLY', sender.call_args.args[1])

    def test_email_failure_is_never_retried(self):
        raised = {
            'incident_id': 'INC-DRILL00001',
            'status': 'open',
            'event': 'raised',
        }
        resolved = {
            'incident_id': 'INC-DRILL00001',
            'status': 'resolved',
            'event': 'resolved',
        }
        sender = MagicMock(side_effect=RuntimeError(
            'Email outcome is unknown. Check n8n execution history before sending again.'
        ))
        with patch.object(
            app2121.OPS,
            'status',
            return_value={'email_notifications_enabled': True},
        ), patch.object(
            app2121,
            '_drill_n8n_ready',
            return_value=(True, ''),
        ), patch.object(
            app2121,
            '_persist_drill_event',
            side_effect=[(raised, True), (resolved, True)],
        ), patch.object(
            app2121.base,
            'send_email_via_n8n',
            sender,
        ):
            payload = app2121.run_safe_incident_drill()

        self.assertFalse(payload['success'])
        self.assertFalse(payload['drill']['receipt_confirmed'])
        self.assertEqual(payload['drill']['email_error_category'], 'unconfirmed_or_failed')
        self.assertEqual(sender.call_count, 1)
        self.assertIn('did not retry', payload['reply'].lower())

    def test_message_handler_runs_drill_without_calling_normal_reasoning(self):
        fake = app2121.base.base_payload(
            'proactive_operations_drill',
            'Safe proactive operations drill complete.',
            used_tools=['proactive_operations'],
            success=True,
        )
        with patch.object(app2121, 'run_safe_incident_drill', return_value=fake) as drill, patch.object(
            app2121,
            '_PREVIOUS_HANDLE_MESSAGE',
        ) as normal:
            payload, status = app2121.handle_message_v2121('Run proactive operations test')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        drill.assert_called_once_with()
        normal.assert_not_called()

    def test_v2121_version_and_health_route(self):
        self.assertEqual(app2121.VERSION_SHORT, 'v2.12.1')
        self.assertIs(app2121.base.handle_message, app2121.handle_message_v2121)
        with app2121.app.test_client() as client:
            health = client.get('/health')
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()['version_short'], 'v2.12.1')


if __name__ == '__main__':
    unittest.main()
