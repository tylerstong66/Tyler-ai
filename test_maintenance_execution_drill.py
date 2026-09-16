import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from maintenance_execution_drill import (
    DRILL_CATEGORY,
    DRILL_FIND,
    DRILL_REPLACE,
    DRILL_TARGET_FILE,
    SafeMaintenanceExecutionDrillCoordinator,
    deterministic_drill_patch,
    make_drill_plan,
)


class FakeResponse:
    def __init__(self, ok=True, status_code=200, payload=None):
        self.ok = ok
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class DrillCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / DRILL_TARGET_FILE).write_text(
            'DRILL_MARKER = "base"\n\n\ndef drill_marker():\n    return DRILL_MARKER\n',
            encoding='utf-8',
        )
        self.plan_id = 'MNT-D214100001'
        self.plan = make_drill_plan(self.plan_id)
        self.coordinator = SafeMaintenanceExecutionDrillCoordinator(
            plan_loader=lambda identifier: self.plan if identifier == self.plan_id else None,
            safe_source_files_fn=lambda: [DRILL_TARGET_FILE],
            patch_generator_fn=deterministic_drill_patch,
            supabase_url_fn=lambda: 'https://example.supabase.co',
            headers_fn=lambda: {'apikey': 'test', 'Authorization': 'Bearer test'},
            version_fn=lambda: 'v2.14.1',
            source_root=self.root,
            github_token_fn=lambda: 'test-token',
            github_repository_fn=lambda: 'tylerstong66/Tyler-ai',
            github_base_branch_fn=lambda: 'main',
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_drill_plan_is_source_grounded_and_isolated(self):
        self.assertTrue(self.plan['source_grounded'])
        self.assertTrue(self.plan['drill'])
        self.assertNotIn('simulation', self.plan)
        self.assertEqual(self.plan['affected_code'][0]['file'], DRILL_TARGET_FILE)
        self.assertEqual(DRILL_CATEGORY, 'maintenance_execution_drill')

    def test_deterministic_patch_only_changes_dedicated_marker(self):
        patch_spec = deterministic_drill_patch(self.plan, 'source', 'EXE-1234567890')
        self.assertEqual(len(patch_spec['changes']), 1)
        change = patch_spec['changes'][0]
        self.assertEqual(change['path'], DRILL_TARGET_FILE)
        self.assertEqual(change['find'], DRILL_FIND)
        self.assertEqual(change['replace'], DRILL_REPLACE)

    def test_prepare_never_publishes(self):
        with patch.object(self.coordinator, '_post_memory', return_value=True), patch.object(
            self.coordinator, 'execution', return_value=None
        ), patch.object(self.coordinator, '_publish_atomic_review_branch') as publisher:
            result = self.coordinator.prepare(self.plan_id, persist=True)
        self.assertTrue(result['success'])
        self.assertEqual(result['package']['status'], 'awaiting_approval')
        self.assertFalse(result['package']['github_publish_performed'])
        publisher.assert_not_called()

    def test_verification_requires_main_unchanged_and_review_changed(self):
        main_text = 'DRILL_MARKER = "base"\n'
        branch_text = 'DRILL_MARKER = "review-branch-test"\n'

        def fake_request(_method, _path, **kwargs):
            ref = (kwargs.get('params') or {}).get('ref')
            text = branch_text if str(ref).startswith('tyler-maintenance/') else main_text
            encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
            return FakeResponse(payload={'content': encoded})

        package = {
            'status': 'published_for_review',
            'github_publish': {
                'branch': 'tyler-maintenance/exe-abcdef1234',
                'base_branch': 'main',
            },
        }
        with patch.object(self.coordinator, '_github_request', side_effect=fake_request):
            result = self.coordinator.verify_published_drill(package)
        self.assertTrue(result['success'])
        self.assertTrue(result['main_unchanged'])
        self.assertTrue(result['review_branch_changed'])
        self.assertFalse(result['production_deployment_performed'])


class V2141IntegrationTests(unittest.TestCase):
    def test_import_and_safety_contract(self):
        import app_v2_14_1 as app2141
        self.assertEqual(app2141.VERSION_SHORT, 'v2.14.1')
        self.assertIn(DRILL_CATEGORY, app2141.base.SPECIAL_MEMORY_CATEGORIES)
        self.assertIn('maintenance_execution_drill.py', app2141.v210.v297._safe_source_files())
        status = app2141.DRILL_EXECUTOR.status()
        self.assertFalse(status['automatic_github_writes_enabled'])
        self.assertFalse(status['automatic_production_deployment_enabled'])
        self.assertTrue(status['approval_required_before_github_write'])

    def test_prepare_command_stops_before_approval_and_write(self):
        import app_v2_14_1 as app2141
        package = {
            'execution_id': 'EXE-ABCDEF1234',
            'status': 'awaiting_approval',
            'approval_code': 'A1B2C3',
        }
        with patch.object(app2141.DRILL_EXECUTOR, 'github_configured', return_value=True), patch.object(
            app2141.DRILL_EXECUTOR,
            'prepare',
            return_value={'success': True, 'package': package, 'saved': True},
        ) as prepare, patch.object(app2141.DRILL_EXECUTOR, 'approve') as approve, patch.object(
            app2141.DRILL_EXECUTOR, 'execute_approved'
        ) as execute:
            payload, status = app2141.handle_message_v2141('Run maintenance execution test')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        prepare.assert_called_once()
        approve.assert_not_called()
        execute.assert_not_called()
        self.assertIn('PREPARE STAGE PASSED', payload['reply'])
        self.assertIn('Approve maintenance execution drill EXE-ABCDEF1234 code A1B2C3', payload['reply'])

    def test_approval_still_does_not_execute(self):
        import app_v2_14_1 as app2141
        package = {
            'execution_id': 'EXE-ABCDEF1234',
            'status': 'approved',
            'approval_expires_at': '2026-09-16T13:00:00+00:00',
        }
        with patch.object(
            app2141.DRILL_EXECUTOR,
            'approve',
            return_value={'success': True, 'package': package},
        ) as approve, patch.object(app2141.DRILL_EXECUTOR, 'execute_approved') as execute:
            payload, status = app2141.handle_message_v2141(
                'Approve maintenance execution drill EXE-ABCDEF1234 code A1B2C3'
            )
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        approve.assert_called_once_with('EXE-ABCDEF1234', 'A1B2C3')
        execute.assert_not_called()
        self.assertIn('APPROVAL STAGE PASSED', payload['reply'])

    def test_execute_reports_pass_only_after_remote_verification(self):
        import app_v2_14_1 as app2141
        package = {
            'execution_id': 'EXE-ABCDEF1234',
            'status': 'published_for_review',
            'github_publish': {
                'branch': 'tyler-maintenance/exe-abcdef1234',
                'proposal_commit_sha': 'abc123',
            },
        }
        verification = {
            'success': True,
            'main_unchanged': True,
            'review_branch_changed': True,
            'production_deployment_performed': False,
        }
        with patch.object(
            app2141.DRILL_EXECUTOR,
            'execute_approved',
            return_value={'success': True, 'package': package, 'saved': True},
        ) as execute, patch.object(
            app2141.DRILL_EXECUTOR,
            'verify_published_drill',
            return_value=verification,
        ) as verify:
            payload, status = app2141.handle_message_v2141(
                'Execute approved maintenance drill EXE-ABCDEF1234'
            )
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        execute.assert_called_once_with('EXE-ABCDEF1234')
        verify.assert_called_once_with(package)
        self.assertIn('Result: PASS', payload['reply'])
        self.assertIn('Main verified unchanged: yes', payload['reply'])

    def test_health_reports_v2141(self):
        import app_v2_14_1 as app2141
        with app2141.app.test_client() as client:
            response = client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['version_short'], 'v2.14.1')


if __name__ == '__main__':
    unittest.main()
