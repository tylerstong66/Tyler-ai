import unittest
from unittest.mock import patch

from maintenance_review_gate import MaintenanceReviewGate, review_id_for


EXECUTION_ID = 'EXE-ABCDEF1234'
BASE_SHA = 'a' * 40
PROPOSAL_SHA = 'b' * 40
BRANCH = 'tyler-maintenance/exe-abcdef1234'


def package(status='published_for_review'):
    return {
        'execution_id': EXECUTION_ID,
        'maintenance_plan_id': 'MNT-1234567890',
        'incident_id': 'INC-1234567890',
        'service': 'groq',
        'status': status,
        'patch_spec': {
            'summary': 'Minimal safe patch.',
            'changed_files': [{'path': 'app.py'}],
        },
        'target': {
            'repository': 'tylerstong66/Tyler-ai',
            'base_branch': 'main',
        },
        'github_publish': {
            'repository': 'tylerstong66/Tyler-ai',
            'base_branch': 'main',
            'branch': BRANCH,
            'base_commit_sha': BASE_SHA,
            'proposal_commit_sha': PROPOSAL_SHA,
            'production_branch_changed': False,
        },
        'production_deployment_performed': False,
        'configuration_change_performed': False,
        'external_side_effect_retry_performed': False,
    }


class MaintenanceReviewGateTests(unittest.TestCase):
    def make_gate(self, item=None):
        selected = package() if item is None else item
        return MaintenanceReviewGate(
            execution_loader=lambda _execution_id: selected,
            supabase_url_fn=lambda: 'https://example.supabase.co',
            headers_fn=lambda: {'apikey': 'test', 'Authorization': 'Bearer test'},
            version_fn=lambda: 'v2.15.0',
            github_token_fn=lambda: 'test-token',
            github_repository_fn=lambda: 'tylerstong66/Tyler-ai',
            github_base_branch_fn=lambda: 'main',
        )

    def wire_good_github(self, gate, ci=None, text="def target():\n    return 'safe'\n"):
        def ref_sha(branch):
            return PROPOSAL_SHA if branch == BRANCH else BASE_SHA

        compare = {
            'ahead_by': 1,
            'behind_by': 0,
            'files': [{'filename': 'app.py', 'status': 'modified'}],
        }
        commit = {'parents': [{'sha': BASE_SHA}]}
        ci = ci or {'state': 'success', 'reason': 'review_ci_passed', 'run_id': 123}
        return patch.multiple(
            gate,
            _fetch_ref_sha=ref_sha,
            _fetch_commit=lambda _sha: commit,
            _compare=lambda _base, _head: compare,
            _fetch_text=lambda _path, _ref: text,
            _ci_status=lambda _sha, _branch: ci,
        )

    def test_review_id_is_stable(self):
        self.assertEqual(
            review_id_for(EXECUTION_ID, PROPOSAL_SHA),
            review_id_for(EXECUTION_ID.lower(), PROPOSAL_SHA.upper()),
        )
        self.assertTrue(review_id_for(EXECUTION_ID, PROPOSAL_SHA).startswith('REV-'))

    def test_status_never_enables_merge_or_deploy(self):
        status = self.make_gate().status()
        self.assertFalse(status['automatic_merge_enabled'])
        self.assertFalse(status['automatic_pull_request_creation_enabled'])
        self.assertFalse(status['automatic_production_deployment_enabled'])
        self.assertFalse(status['automatic_branch_mutation_enabled'])
        self.assertTrue(status['review_requires_ci_success'])
        self.assertTrue(status['review_requires_exact_diff_scope'])
        self.assertTrue(status['review_requires_current_base'])

    def test_missing_execution_cannot_be_reviewed(self):
        gate = MaintenanceReviewGate(
            execution_loader=lambda _execution_id: None,
            supabase_url_fn=lambda: '',
            headers_fn=lambda: {},
            version_fn=lambda: 'v2.15.0',
            github_repository_fn=lambda: 'tylerstong66/Tyler-ai',
            github_base_branch_fn=lambda: 'main',
        )
        result = gate.review(EXECUTION_ID, persist=False)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'execution_not_found')

    def test_execution_must_be_published_for_review(self):
        result = self.make_gate(package(status='approved')).review(EXECUTION_ID, persist=False)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'execution_not_published_for_review')

    def test_good_branch_and_successful_ci_are_ready(self):
        gate = self.make_gate()
        with self.wire_good_github(gate), patch.object(gate, '_post_memory', return_value=True) as save:
            result = gate.review(EXECUTION_ID, persist=True)
        self.assertTrue(result['success'])
        review = result['review']
        self.assertEqual(review['gate_status'], 'ready')
        self.assertTrue(review['checks']['exact_diff_scope'])
        self.assertTrue(review['checks']['source_safety_scan_passed'])
        self.assertTrue(review['checks']['review_ci_passed'])
        self.assertFalse(review['automatic_merge_performed'])
        self.assertFalse(review['production_deployment_performed'])
        save.assert_called_once()

    def test_ci_still_running_is_pending_and_not_persisted(self):
        gate = self.make_gate()
        ci = {'state': 'pending', 'reason': 'review_ci_in_progress', 'run_id': 123}
        with self.wire_good_github(gate, ci=ci), patch.object(gate, '_post_memory') as save:
            result = gate.review(EXECUTION_ID, persist=True)
        self.assertEqual(result['review']['gate_status'], 'pending')
        self.assertIn('review_ci_in_progress', result['review']['reasons'])
        save.assert_not_called()

    def test_failed_ci_is_not_ready(self):
        gate = self.make_gate()
        ci = {'state': 'failure', 'reason': 'review_ci_failure', 'run_id': 123}
        with self.wire_good_github(gate, ci=ci), patch.object(gate, '_post_memory', return_value=True):
            result = gate.review(EXECUTION_ID, persist=True)
        self.assertEqual(result['review']['gate_status'], 'not_ready')
        self.assertIn('review_ci_failure', result['review']['reasons'])

    def test_main_advancing_after_preparation_blocks_readiness(self):
        gate = self.make_gate()

        def ref_sha(branch):
            return PROPOSAL_SHA if branch == BRANCH else 'c' * 40

        with patch.object(gate, '_fetch_ref_sha', side_effect=ref_sha), patch.object(
            gate, '_fetch_commit', return_value={'parents': [{'sha': BASE_SHA}]}
        ), patch.object(
            gate,
            '_compare',
            return_value={
                'ahead_by': 1,
                'behind_by': 0,
                'files': [{'filename': 'app.py', 'status': 'modified'}],
            },
        ), patch.object(gate, '_post_memory', return_value=True), patch.object(gate, '_ci_status') as ci:
            result = gate.review(EXECUTION_ID, persist=True)
        self.assertEqual(result['review']['gate_status'], 'not_ready')
        self.assertIn('main_still_at_review_base', result['review']['reasons'])
        ci.assert_not_called()

    def test_unexpected_extra_file_blocks_readiness(self):
        gate = self.make_gate()
        compare = {
            'ahead_by': 1,
            'behind_by': 0,
            'files': [
                {'filename': 'app.py', 'status': 'modified'},
                {'filename': 'unexpected.py', 'status': 'added'},
            ],
        }
        with patch.object(gate, '_fetch_ref_sha', side_effect=lambda branch: PROPOSAL_SHA if branch == BRANCH else BASE_SHA), patch.object(
            gate, '_fetch_commit', return_value={'parents': [{'sha': BASE_SHA}]}
        ), patch.object(gate, '_compare', return_value=compare), patch.object(gate, '_post_memory', return_value=True), patch.object(
            gate, '_ci_status'
        ) as ci:
            result = gate.review(EXECUTION_ID, persist=True)
        self.assertEqual(result['review']['gate_status'], 'not_ready')
        self.assertIn('exact_diff_scope', result['review']['reasons'])
        self.assertIn('only_existing_files_modified', result['review']['reasons'])
        ci.assert_not_called()

    def test_secret_like_literal_blocks_readiness(self):
        gate = self.make_gate()
        unsafe = "API = 'ghp_123456789012345678901234567890'\n"
        with self.wire_good_github(gate, text=unsafe), patch.object(gate, '_post_memory', return_value=True), patch.object(
            gate, '_ci_status'
        ) as ci:
            # patch.multiple already replaces _ci_status, so the outer patch is intentionally not used.
            pass
        # Run again with explicit structural stubs so we can assert CI was skipped.
        with patch.object(gate, '_fetch_ref_sha', side_effect=lambda branch: PROPOSAL_SHA if branch == BRANCH else BASE_SHA), patch.object(
            gate, '_fetch_commit', return_value={'parents': [{'sha': BASE_SHA}]}
        ), patch.object(
            gate,
            '_compare',
            return_value={
                'ahead_by': 1,
                'behind_by': 0,
                'files': [{'filename': 'app.py', 'status': 'modified'}],
            },
        ), patch.object(gate, '_fetch_text', return_value=unsafe), patch.object(gate, '_ci_status') as ci, patch.object(
            gate, '_post_memory', return_value=True
        ):
            result = gate.review(EXECUTION_ID, persist=True)
        self.assertEqual(result['review']['gate_status'], 'not_ready')
        self.assertIn('source_safety_scan_failed', result['review']['reasons'])
        ci.assert_not_called()

    def test_wrong_review_branch_name_is_rejected_before_github_calls(self):
        item = package()
        item['github_publish'] = dict(item['github_publish'])
        item['github_publish']['branch'] = 'main'
        gate = self.make_gate(item)
        with patch.object(gate, '_fetch_ref_sha') as fetch_ref, patch.object(gate, '_post_memory', return_value=True):
            result = gate.review(EXECUTION_ID, persist=True)
        self.assertEqual(result['review']['gate_status'], 'not_ready')
        self.assertIn('safe_review_branch', result['review']['reasons'])
        fetch_ref.assert_not_called()


class V215IntegrationTests(unittest.TestCase):
    def test_v215_import_and_safety_contract(self):
        import app_v2_15 as app215
        self.assertEqual(app215.VERSION_SHORT, 'v2.15.0')
        self.assertIsNotNone(app215.app)
        self.assertIs(app215.base.handle_message, app215.handle_message_v215)
        self.assertIn('maintenance_review_gate', app215.base.SPECIAL_MEMORY_CATEGORIES)
        self.assertIn('maintenance_review_gate.py', app215.v210.v297._safe_source_files())
        status = app215.REVIEW_GATE.status()
        self.assertFalse(status['automatic_merge_enabled'])
        self.assertFalse(status['automatic_production_deployment_enabled'])

    def test_status_command_is_model_free(self):
        import app_v2_15 as app215
        with patch.object(app215.REVIEW_GATE, 'recent', return_value=[]), patch.object(
            app215.REVIEW_GATE,
            'status',
            return_value={
                'github_read_configured': True,
                'automatic_merge_enabled': False,
                'automatic_pull_request_creation_enabled': False,
                'automatic_production_deployment_enabled': False,
                'automatic_branch_mutation_enabled': False,
            },
        ), patch.object(app215.base, 'groq') as groq:
            payload, status = app215.handle_message_v215('Show maintenance review gate')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        self.assertIn('Automatic merge: disabled', payload['reply'])
        groq.assert_not_called()

    def test_review_command_surfaces_ready_without_merging(self):
        import app_v2_15 as app215
        fake = {
            'review_id': 'REV-1234567890',
            'execution_id': EXECUTION_ID,
            'gate_status': 'ready',
            'review_branch': BRANCH,
            'proposal_commit_sha': PROPOSAL_SHA,
            'changed_files': ['app.py'],
            'checks': {
                'branch_points_to_proposal': True,
                'proposal_parent_matches_base': True,
                'main_still_at_review_base': True,
                'single_commit_proposal': True,
                'exact_diff_scope': True,
                'only_existing_files_modified': True,
                'source_safety_scan_passed': True,
            },
            'ci': {'state': 'success', 'reason': 'review_ci_passed'},
            'reasons': [],
        }
        with patch.object(app215.REVIEW_GATE, 'review', return_value={'success': True, 'review': fake}):
            payload, status = app215.handle_message_v215(f'Review maintenance execution {EXECUTION_ID}')
        self.assertEqual(status, 200)
        self.assertIn('Maintenance review gate: READY', payload['reply'])
        self.assertIn('Automatic merge performed: no', payload['reply'])

    def test_diagnostics_route_requires_authentication(self):
        import app_v2_15 as app215
        with app215.app.test_client() as client:
            response = client.get('/diagnostics/maintenance/review-gate')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
