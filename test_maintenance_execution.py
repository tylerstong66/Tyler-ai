import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from maintenance_execution import (
    MAINTENANCE_EXECUTION_CATEGORY,
    MaintenanceExecutionCoordinator,
    execution_id_for,
)


def plan(kind='live_unhealthy', source_grounded=True, simulation=False):
    return {
        'maintenance_plan_id': 'MNT-1234567890',
        'incident_id': 'INC-1234567890',
        'service': 'groq',
        'severity': 'critical',
        'kind': kind,
        'source_grounded': source_grounded,
        'simulation': simulation,
        'likely_cause': 'Verified test failure.',
        'affected_code': [{'file': 'app.py', 'functions': ['target']}],
        'proposed_patch': {'strategy': 'Minimal reversible fix.', 'changes': ['Change target.']},
        'test_plan': ['Run targeted regression test.', 'Run full suite.'],
        'rollback_plan': ['Restore prior version.'],
        'deployment_plan': ['Publish only after approval.'],
    }


class MaintenanceExecutionUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.original = "def target():\n    return 'old'\n"
        (self.root / 'app.py').write_text(self.original, encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def make_executor(self, item=None, generator=None, now_fn=None, token=''):
        selected = item if item is not None else plan()
        generator = generator or (lambda _plan, _context, _execution_id: {
            'summary': 'Change target safely.',
            'changes': [{
                'path': 'app.py',
                'find': "def target():\n    return 'old'\n",
                'replace': "def target():\n    return 'new'\n",
                'reason': 'Verified regression fix.',
            }],
        })
        return MaintenanceExecutionCoordinator(
            plan_loader=lambda _identifier: selected,
            safe_source_files_fn=lambda: ['app.py'],
            patch_generator_fn=generator,
            supabase_url_fn=lambda: 'https://example.supabase.co',
            headers_fn=lambda: {'apikey': 'test', 'Authorization': 'Bearer test'},
            version_fn=lambda: 'v2.14.0',
            source_root=self.root,
            approval_ttl_minutes=30,
            now_fn=now_fn,
            github_token_fn=lambda: token,
            github_repository_fn=lambda: 'tylerstong66/Tyler-ai',
            github_base_branch_fn=lambda: 'main',
        )

    def prepared_package(self, executor=None):
        executor = executor or self.make_executor()
        with patch.object(executor, '_post_memory', return_value=True), patch.object(executor, 'execution', return_value=None):
            result = executor.prepare('MNT-1234567890', persist=True)
        self.assertTrue(result['success'])
        return executor, result['package']

    def test_execution_id_is_stable(self):
        self.assertEqual(execution_id_for('MNT-1234567890'), execution_id_for('mnt-1234567890'))
        self.assertTrue(execution_id_for('MNT-1234567890').startswith('EXE-'))

    def test_category_is_dedicated(self):
        self.assertEqual(MAINTENANCE_EXECUTION_CATEGORY, 'maintenance_execution')

    def test_prepare_builds_exact_match_patch_and_waits_for_approval(self):
        executor = self.make_executor()
        with patch.object(executor, '_post_memory', return_value=True), patch.object(executor, 'execution', return_value=None):
            result = executor.prepare('MNT-1234567890', persist=True)
        self.assertTrue(result['success'])
        package = result['package']
        self.assertEqual(package['status'], 'awaiting_approval')
        self.assertFalse(package['approval_granted'])
        self.assertRegex(package['approval_code'], r'^[A-F0-9]{6}$')
        self.assertFalse(package['github_publish_performed'])
        self.assertFalse(package['production_deployment_performed'])
        self.assertEqual(package['patch_spec']['changed_files'][0]['path'], 'app.py')
        self.assertFalse(package['target']['direct_main_write'])
        self.assertFalse(package['target']['pull_request_created_automatically'])

    def test_unknown_external_outcome_is_blocked_before_patch_generation(self):
        generator = MagicMock()
        executor = self.make_executor(item=plan(kind='unknown_external_outcome'), generator=generator)
        result = executor.prepare('MNT-1234567890', persist=False)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'outcome_verification_required_before_patch')
        generator.assert_not_called()

    def test_simulation_and_ungrounded_plan_are_not_executable(self):
        self.assertEqual(
            self.make_executor(item=plan(simulation=True)).prepare('MNT-1234567890', persist=False)['error'],
            'simulation_plan_not_executable',
        )
        self.assertEqual(
            self.make_executor(item=plan(source_grounded=False)).prepare('MNT-1234567890', persist=False)['error'],
            'maintenance_plan_not_source_grounded',
        )

    def test_patch_cannot_target_unverified_file(self):
        executor = self.make_executor(generator=lambda *_args: {
            'summary': 'bad',
            'changes': [{'path': 'evil.py', 'find': 'x', 'replace': 'y', 'reason': 'bad'}],
        })
        with patch.object(executor, 'execution', return_value=None):
            result = executor.prepare('MNT-1234567890', persist=False)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'patch_generation_or_validation_failed')
        self.assertIn('patch_path_not_allowed', result['detail'])

    def test_patch_with_literal_secret_is_rejected(self):
        executor = self.make_executor(generator=lambda *_args: {
            'summary': 'bad',
            'changes': [{
                'path': 'app.py',
                'find': "def target():\n    return 'old'\n",
                'replace': "def target():\n    token = 'ghp_123456789012345678901234567890'\n    return token\n",
                'reason': 'bad',
            }],
        })
        with patch.object(executor, 'execution', return_value=None):
            result = executor.prepare('MNT-1234567890', persist=False)
        self.assertFalse(result['success'])
        self.assertIn('patch_contains_secret_literal', result['detail'])

    def test_wrong_approval_code_never_persists_approval(self):
        executor, package = self.prepared_package()
        with patch.object(executor, 'execution', return_value=package), patch.object(executor, '_post_memory') as writer:
            result = executor.approve(package['execution_id'], 'FFFFFF')
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'approval_code_invalid')
        writer.assert_not_called()

    def test_approval_revalidates_source_and_must_persist(self):
        executor, package = self.prepared_package()
        with patch.object(executor, 'execution', return_value=package), patch.object(executor, '_post_memory', return_value=True) as writer:
            result = executor.approve(package['execution_id'], package['approval_code'])
        self.assertTrue(result['success'])
        self.assertEqual(result['package']['status'], 'approved')
        self.assertTrue(result['package']['approval_granted'])
        self.assertIsNotNone(result['package']['approval_expires_at'])
        writer.assert_called_once()

    def test_source_drift_blocks_approval(self):
        executor, package = self.prepared_package()
        (self.root / 'app.py').write_text("def target():\n    return 'drifted'\n", encoding='utf-8')
        with patch.object(executor, 'execution', return_value=package), patch.object(executor, '_post_memory') as writer:
            result = executor.approve(package['execution_id'], package['approval_code'])
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'source_or_patch_drift')
        writer.assert_not_called()

    def test_execute_requires_prior_approval(self):
        executor, package = self.prepared_package()
        with patch.object(executor, 'execution', return_value=package), patch.object(executor, '_publish_atomic_review_branch') as publisher:
            result = executor.execute_approved(package['execution_id'])
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'execution_not_approved')
        publisher.assert_not_called()

    def test_approval_expiry_blocks_github_write(self):
        now = datetime(2026, 9, 15, 22, 0, tzinfo=timezone.utc)
        executor, package = self.prepared_package(self.make_executor(now_fn=lambda: now, token='test-token'))
        package = dict(package)
        package.update({
            'status': 'approved',
            'approval_granted': True,
            'approval_expires_at': (now - timedelta(minutes=1)).isoformat(),
        })
        with patch.object(executor, 'execution', return_value=package), patch.object(executor, '_post_memory', return_value=True), patch.object(
            executor, '_publish_atomic_review_branch'
        ) as publisher:
            result = executor.execute_approved(package['execution_id'])
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'approval_expired')
        publisher.assert_not_called()

    def test_approved_package_without_github_token_cannot_write(self):
        now = datetime(2026, 9, 15, 22, 0, tzinfo=timezone.utc)
        executor, package = self.prepared_package(self.make_executor(now_fn=lambda: now, token=''))
        package = dict(package)
        package.update({
            'status': 'approved',
            'approval_granted': True,
            'approval_expires_at': (now + timedelta(minutes=10)).isoformat(),
        })
        with patch.object(executor, 'execution', return_value=package), patch.object(executor, '_publish_atomic_review_branch') as publisher:
            result = executor.execute_approved(package['execution_id'])
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'github_write_not_configured')
        publisher.assert_not_called()

    def test_approved_execution_only_publishes_review_branch_and_never_production(self):
        now = datetime(2026, 9, 15, 22, 0, tzinfo=timezone.utc)
        executor, package = self.prepared_package(self.make_executor(now_fn=lambda: now, token='test-token'))
        package = dict(package)
        package.update({
            'status': 'approved',
            'approval_granted': True,
            'approval_expires_at': (now + timedelta(minutes=10)).isoformat(),
        })
        publish = {
            'repository': 'tylerstong66/Tyler-ai',
            'base_branch': 'main',
            'branch': 'tyler-maintenance/exe-test',
            'proposal_commit_sha': 'abc123',
            'pull_request_created': False,
            'production_branch_changed': False,
        }
        with patch.object(executor, 'execution', return_value=package), patch.object(
            executor, '_publish_atomic_review_branch', return_value=publish
        ) as publisher, patch.object(executor, '_post_memory', return_value=True):
            result = executor.execute_approved(package['execution_id'])
        self.assertTrue(result['success'])
        publisher.assert_called_once()
        final_package = result['package']
        self.assertEqual(final_package['status'], 'published_for_review')
        self.assertTrue(final_package['github_publish_performed'])
        self.assertFalse(final_package['production_deployment_performed'])
        self.assertFalse(final_package['github_publish']['production_branch_changed'])
        self.assertFalse(final_package['github_publish']['pull_request_created'])

    def test_status_safety_flags_are_off_by_default(self):
        status = self.make_executor().status()
        self.assertFalse(status['automatic_patch_generation_enabled'])
        self.assertFalse(status['automatic_github_writes_enabled'])
        self.assertFalse(status['automatic_production_deployment_enabled'])
        self.assertTrue(status['approval_required_before_github_write'])
        self.assertTrue(status['separate_execute_command_required_after_approval'])
        self.assertFalse(status['writes_to_main_branch_directly'])


class V214IntegrationTests(unittest.TestCase):
    def test_v214_import_and_safety_contract(self):
        import app_v2_14 as app214
        self.assertEqual(app214.VERSION_SHORT, 'v2.14.0')
        self.assertIn(MAINTENANCE_EXECUTION_CATEGORY, app214.base.SPECIAL_MEMORY_CATEGORIES)
        self.assertIn('maintenance_execution.py', app214.v210.v297._safe_source_files())
        status = app214.EXECUTOR.status()
        self.assertFalse(status['automatic_github_writes_enabled'])
        self.assertFalse(status['automatic_production_deployment_enabled'])
        self.assertTrue(status['approval_required_before_github_write'])

    def test_status_command_is_model_free(self):
        import app_v2_14 as app214
        with patch.object(app214.EXECUTOR, 'recent', return_value=[]), patch.object(
            app214.EXECUTOR,
            'status',
            return_value={
                'github_write_configured': False,
                'automatic_patch_generation_enabled': False,
                'automatic_github_writes_enabled': False,
                'automatic_production_deployment_enabled': False,
                'approval_required_before_github_write': True,
                'separate_execute_command_required_after_approval': True,
            },
        ), patch.object(app214.base, 'groq') as groq:
            payload, status = app214.handle_message_v214('Show maintenance execution')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        self.assertIn('Automatic GitHub writes: disabled', payload['reply'])
        groq.assert_not_called()

    def test_prepare_command_surfaces_exact_approval_phrase(self):
        import app_v2_14 as app214
        package = {
            'execution_id': 'EXE-ABCDEF1234',
            'maintenance_plan_id': 'MNT-1234567890',
            'incident_id': 'INC-1234567890',
            'service': 'groq',
            'status': 'awaiting_approval',
            'approval_code': 'A1B2C3',
            'patch_spec': {
                'summary': 'Minimal patch.',
                'changed_files': [{'path': 'app.py'}],
            },
            'target': {
                'repository': 'tylerstong66/Tyler-ai',
                'base_branch': 'main',
            },
        }
        with patch.object(
            app214.EXECUTOR,
            'prepare',
            return_value={'success': True, 'package': package, 'saved': True},
        ) as prepare:
            payload, status = app214.handle_message_v214('Prepare maintenance execution for MNT-1234567890')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        prepare.assert_called_once_with('MNT-1234567890', persist=True)
        self.assertIn('Approve maintenance execution EXE-ABCDEF1234 code A1B2C3', payload['reply'])
        self.assertIn('Approval alone does not execute the patch', payload['reply'])

    def test_approval_parser_requires_code(self):
        import app_v2_14 as app214
        self.assertEqual(app214._approval_parts('Approve maintenance execution EXE-ABCDEF1234'), (None, None))
        self.assertEqual(
            app214._approval_parts('Approve maintenance execution EXE-ABCDEF1234 code A1B2C3'),
            ('EXE-ABCDEF1234', 'A1B2C3'),
        )

    def test_diagnostics_route_requires_authentication(self):
        import app_v2_14 as app214
        with app214.app.test_client() as client:
            response = client.get('/diagnostics/maintenance/execution')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
