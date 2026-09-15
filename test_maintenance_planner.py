import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from maintenance_planner import (
    MAINTENANCE_PLAN_CATEGORY,
    MaintenancePlanner,
    maintenance_plan_id_for,
    verified_affected_code,
)


def incident(service='groq', kind='live_unhealthy', simulation=False):
    return {
        'incident_id': 'INC-1234567890',
        'status': 'open',
        'service': service,
        'severity': 'critical',
        'kind': kind,
        'title': f'{service} incident',
        'simulation': simulation,
        'diagnostics': {
            'live': {
                'state': 'unhealthy',
                'last_error_category': 'http_500',
                'p95_latency_ms': 1500,
            },
            'history': {
                'failure_samples': 4,
                'p95_latency_ms': 700,
            },
        },
    }


class MaintenancePlannerUnitTests(unittest.TestCase):
    def make_planner(self, item=None, source_root=None):
        return MaintenancePlanner(
            incident_loader=lambda _incident_id: item if item is not None else incident(),
            safe_source_files_fn=lambda: ['app.py', 'app_v2_10.py', 'maintenance_planner.py'],
            supabase_url_fn=lambda: 'https://example.supabase.co',
            headers_fn=lambda: {'apikey': 'test', 'Authorization': 'Bearer test'},
            version_fn=lambda: 'v2.13.0',
            source_root=source_root or Path(__file__).resolve().parent,
        )

    def test_plan_id_is_stable(self):
        self.assertEqual(
            maintenance_plan_id_for('INC-1234567890'),
            maintenance_plan_id_for('inc-1234567890'),
        )
        self.assertTrue(maintenance_plan_id_for('INC-1234567890').startswith('MNT-'))

    def test_plan_is_prepared_only_and_approval_gated(self):
        planner = self.make_planner()
        plan = planner.build_plan(incident())
        self.assertTrue(plan['approval_required_before_execution'])
        self.assertFalse(plan['automatic_changes_performed'])
        self.assertFalse(plan['automatic_deployment_performed'])
        self.assertFalse(plan['automatic_configuration_changes_performed'])
        self.assertFalse(plan['unsafe_retry_performed'])
        self.assertEqual(plan['status'], 'prepared')

    def test_unknown_n8n_outcome_requires_verification_before_retry(self):
        planner = self.make_planner(item=incident(service='n8n', kind='unknown_external_outcome'))
        plan = planner.build_plan(incident(service='n8n', kind='unknown_external_outcome'))
        text = str(plan).lower()
        self.assertIn('verify', text)
        self.assertIn('before any retry', text)
        self.assertTrue(plan['approval_required_before_execution'])
        self.assertFalse(plan['unsafe_retry_performed'])

    def test_simulated_incident_is_not_planned(self):
        planner = self.make_planner(item=incident(simulation=True))
        with patch.object(planner, '_post_memory') as writer:
            result = planner.prepare_for_incident('INC-1234567890')
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'simulation_incident_not_planned')
        writer.assert_not_called()

    def test_persistence_failure_does_not_turn_plan_into_execution(self):
        planner = self.make_planner()
        with patch.object(planner, '_post_memory', return_value=False):
            result = planner.prepare_for_incident('INC-1234567890')
        self.assertTrue(result['success'])
        self.assertFalse(result['saved'])
        self.assertFalse(result['plan']['automatic_changes_performed'])
        self.assertTrue(result['plan']['approval_required_before_execution'])

    def test_verified_affected_code_only_uses_present_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'app.py').write_text(
                'def groq(messages):\n    return messages\n\n'
                'def send_email_via_n8n(subject, body):\n    return True\n',
                encoding='utf-8',
            )
            found = verified_affected_code('groq', ['app.py', 'missing.py'], source_root=root)
        self.assertEqual([item['file'] for item in found], ['app.py'])
        self.assertIn('groq', found[0]['functions'])

    def test_category_is_dedicated(self):
        self.assertEqual(MAINTENANCE_PLAN_CATEGORY, 'maintenance_plan')


class V213IntegrationTests(unittest.TestCase):
    def test_v213_import_and_safety_flags(self):
        import app_v2_13 as app213
        self.assertEqual(app213.VERSION_SHORT, 'v2.13.0')
        self.assertIn(MAINTENANCE_PLAN_CATEGORY, app213.base.SPECIAL_MEMORY_CATEGORIES)
        self.assertIn('maintenance_planner.py', app213.v210.v297._safe_source_files())
        status = app213.PLANNER.status()
        self.assertFalse(status['automatic_code_changes_enabled'])
        self.assertFalse(status['automatic_deployment_enabled'])
        self.assertTrue(status['approval_required_before_execution'])

    def test_maintenance_status_command_is_model_free(self):
        import app_v2_13 as app213
        with patch.object(app213.PLANNER, 'recent_plans', return_value=[]), patch.object(
            app213.PLANNER,
            'status',
            return_value={
                'automatic_code_changes_enabled': False,
                'automatic_deployment_enabled': False,
                'automatic_configuration_changes_enabled': False,
                'approval_required_before_execution': True,
            },
        ):
            payload, status = app213.handle_message_v213('Show maintenance planner')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        self.assertIn('Automatic code changes: disabled', payload['reply'])

    def test_explicit_prepare_command_returns_prepared_plan(self):
        import app_v2_13 as app213
        fake_plan = {
            'maintenance_plan_id': 'MNT-ABCDEF1234',
            'incident_id': 'INC-1234567890',
            'service': 'groq',
            'severity': 'critical',
            'status': 'prepared',
            'likely_cause': 'Verified test cause.',
            'affected_code': [{'file': 'app.py', 'functions': ['groq']}],
            'proposed_patch': {'strategy': 'Minimal reversible patch.', 'changes': ['Add regression test.']},
            'test_plan': ['Run tests.'],
            'rollback_plan': ['Rollback.'],
            'deployment_plan': ['Deploy after approval.'],
        }
        with patch.object(
            app213.PLANNER,
            'prepare_for_incident',
            return_value={'success': True, 'plan': fake_plan, 'saved': True},
        ) as prepare:
            payload, status = app213.handle_message_v213('Prepare maintenance plan for INC-1234567890')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        prepare.assert_called_once_with('INC-1234567890', persist=True)
        self.assertIn('Execution status: PREPARED ONLY', payload['reply'])

    def test_real_incident_response_gets_auto_plan_but_no_execution(self):
        import app_v2_13 as app213
        base_payload = {
            'success': True,
            'reply': 'Original answer',
            'used_tools': ['proactive_operations'],
            'proactive_operations': [{
                'incident_id': 'INC-1234567890',
                'status': 'open',
                'event': 'raised',
                'service': 'groq',
            }],
        }
        fake_plan = {
            'maintenance_plan_id': 'MNT-ABCDEF1234',
            'incident_id': 'INC-1234567890',
            'service': 'groq',
        }
        with patch.object(app213, '_PREVIOUS_HANDLE_MESSAGE', return_value=(base_payload, 200)), patch.object(
            app213.PLANNER, 'plan', return_value=None
        ), patch.object(
            app213.PLANNER,
            'prepare_for_incident',
            return_value={'success': True, 'plan': fake_plan, 'saved': True},
        ):
            payload, status = app213.handle_message_v213('normal request')
        self.assertEqual(status, 200)
        self.assertIn('MNT-ABCDEF1234', payload['reply'])
        self.assertIn('No code, configuration, deployment, or side-effect retry was executed.', payload['reply'])
        self.assertIn('maintenance_planner', payload['used_tools'])

    def test_diagnostics_route_requires_authentication(self):
        import app_v2_13 as app213
        with app213.app.test_client() as client:
            response = client.get('/diagnostics/maintenance')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
