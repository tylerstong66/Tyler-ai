import unittest

import app_v2_13_1 as appmod


class SafeMaintenancePlannerDrillTests(unittest.TestCase):
    def test_request_detection_is_explicit(self):
        self.assertTrue(appmod.maintenance_drill_request('Run maintenance planner test'))
        self.assertTrue(appmod.maintenance_drill_request('Run safe maintenance planner drill'))
        self.assertFalse(appmod.maintenance_drill_request('Show maintenance planner'))
        self.assertFalse(appmod.maintenance_drill_request('Fix n8n'))

    def test_drill_builds_safe_source_grounded_plan(self):
        payload = appmod.run_maintenance_planner_drill()
        self.assertTrue(payload['success'])
        drill = payload['maintenance_planner_drill']
        plan = payload['maintenance_plan']

        self.assertTrue(drill['simulation'])
        self.assertTrue(drill['passed'])
        self.assertFalse(drill['persisted'])
        self.assertFalse(drill['production_mutation_performed'])
        self.assertFalse(drill['external_side_effect_performed'])

        checks = drill['checks']
        self.assertTrue(all(checks.values()), checks)
        self.assertTrue(drill['verified_source_files'])
        self.assertTrue(plan['source_grounded'])
        self.assertTrue(plan['simulation'])
        self.assertEqual(plan['status'], 'test_only')
        self.assertEqual(plan['service'], 'n8n')
        self.assertEqual(plan['kind'], 'unknown_external_outcome')
        self.assertTrue(plan['approval_required_before_execution'])
        self.assertFalse(plan['automatic_changes_performed'])
        self.assertFalse(plan['automatic_deployment_performed'])
        self.assertFalse(plan['automatic_configuration_changes_performed'])
        self.assertFalse(plan['unsafe_retry_performed'])

    def test_unknown_outcome_plan_verifies_before_retry(self):
        payload = appmod.run_maintenance_planner_drill()
        plan = payload['maintenance_plan']
        patch = plan['proposed_patch']
        combined = ' '.join([patch.get('strategy', '')] + list(patch.get('changes') or [])).lower()
        tests = ' '.join(plan.get('test_plan') or []).lower()

        self.assertIn('verify', combined)
        self.assertIn('outcome', combined)
        self.assertTrue('do not patch or retry first' in combined or 'verify the downstream outcome' in combined)
        self.assertTrue('never auto-retry' in tests or 'unknown-outcome' in tests)

    def test_chat_command_returns_pass_without_persistence(self):
        payload, status = appmod.handle_message_v2131('Run maintenance planner test')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        self.assertIn('Result: PASS', payload['reply'])
        self.assertIn('Maintenance plan persisted to production history: no', payload['reply'])
        self.assertIn('External side effect executed: no', payload['reply'])

    def test_health_and_status_report_v2131(self):
        with appmod.app.test_client() as client:
            health = client.get('/health')
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.get_json()['version_short'], 'v2.13.1')

            status = client.get('/status')
            self.assertEqual(status.status_code, 200)
            data = status.get_json()
            self.assertEqual(data['version_short'], 'v2.13.1')
            self.assertIn('safe_maintenance_planner_drill', data.get('capabilities') or [])


if __name__ == '__main__':
    unittest.main()
