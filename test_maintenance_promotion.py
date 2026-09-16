import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import requests

from maintenance_promotion import MaintenancePromotionCoordinator, promotion_id_for


EXECUTION_ID = 'EXE-ABCDEF1234'
REVIEW_ID = 'REV-1234567890'
BASE_SHA = 'a' * 40
PROPOSAL_SHA = 'b' * 40
BRANCH = 'tyler-maintenance/exe-abcdef1234'
PROMOTION_ID = promotion_id_for(EXECUTION_ID, PROPOSAL_SHA)
NOW = datetime(2026, 9, 16, 14, 0, tzinfo=timezone.utc)


def ready_review(**overrides):
    item = {
        'review_id': REVIEW_ID,
        'execution_id': EXECUTION_ID,
        'repository': 'tylerstong66/Tyler-ai',
        'base_branch': 'main',
        'review_branch': BRANCH,
        'base_commit_sha': BASE_SHA,
        'proposal_commit_sha': PROPOSAL_SHA,
        'gate_status': 'ready',
        'checks': {'review_ci_passed': True},
        'ci': {'state': 'success'},
    }
    item.update(overrides)
    return item


def promotion(status='approved', **overrides):
    item = {
        'schema': 'tyler_maintenance_promotion_v1',
        'promotion_id': PROMOTION_ID,
        'review_id': REVIEW_ID,
        'execution_id': EXECUTION_ID,
        'repository': 'tylerstong66/Tyler-ai',
        'base_branch': 'main',
        'review_branch': BRANCH,
        'base_commit_sha': BASE_SHA,
        'proposal_commit_sha': PROPOSAL_SHA,
        'version': 'v2.16.0',
        'status': status,
        'approval_required': True,
        'approval_code': 'ABC123',
        'approval_granted': status == 'approved',
        'approval_expires_at': (NOW + timedelta(minutes=30)).isoformat() if status == 'approved' else None,
        'github_write_performed': False,
        'pull_request_created': False,
        'automatic_merge_performed': False,
        'direct_main_write_performed': False,
        'production_deployment_performed': False,
        'unknown_side_effect_retry_performed': False,
    }
    item.update(overrides)
    return item


def pr_payload():
    return {
        'number': 17,
        'html_url': 'https://github.com/tylerstong66/Tyler-ai/pull/17',
        'state': 'open',
        'draft': False,
        'head': {'ref': BRANCH, 'sha': PROPOSAL_SHA},
        'base': {'ref': 'main'},
    }


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=''):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeReviewGate:
    def __init__(self, review=None, success=True, error=None):
        self.current = ready_review() if review is None else review
        self.success = success
        self.error = error
        self.calls = []

    def review(self, execution_id, persist=False):
        self.calls.append((execution_id, persist))
        if not self.success:
            return {'success': False, 'error': self.error or 'review_failed'}
        return {'success': True, 'review': dict(self.current)}


class MaintenancePromotionTests(unittest.TestCase):
    def make_coordinator(self, review_gate=None):
        return MaintenancePromotionCoordinator(
            review_gate=review_gate or FakeReviewGate(),
            supabase_url_fn=lambda: 'https://example.supabase.co',
            headers_fn=lambda: {'apikey': 'test', 'Authorization': 'Bearer test'},
            version_fn=lambda: 'v2.16.0',
            github_token_fn=lambda: 'test-token',
            github_repository_fn=lambda: 'tylerstong66/Tyler-ai',
            github_base_branch_fn=lambda: 'main',
            now_fn=lambda: NOW,
        )

    def test_promotion_id_is_bound_to_execution_and_commit(self):
        self.assertEqual(
            promotion_id_for(EXECUTION_ID.lower(), PROPOSAL_SHA.upper()),
            promotion_id_for(EXECUTION_ID, PROPOSAL_SHA),
        )
        self.assertTrue(PROMOTION_ID.startswith('PRO-'))
        self.assertNotEqual(PROMOTION_ID, promotion_id_for(EXECUTION_ID, 'c' * 40))

    def test_status_never_enables_merge_main_write_or_deploy(self):
        status = self.make_coordinator().status()
        self.assertTrue(status['fresh_ready_review_required'])
        self.assertTrue(status['fresh_human_approval_required'])
        self.assertTrue(status['separate_execute_command_required_after_approval'])
        self.assertFalse(status['automatic_pull_request_creation_enabled'])
        self.assertFalse(status['automatic_merge_enabled'])
        self.assertFalse(status['direct_main_write_enabled'])
        self.assertFalse(status['automatic_production_deployment_enabled'])
        self.assertFalse(status['blind_retry_after_unknown_pr_outcome_enabled'])

    def test_prepare_requires_fresh_ready_review(self):
        gate = FakeReviewGate(review=ready_review(gate_status='pending'))
        coordinator = self.make_coordinator(gate)
        with patch.object(coordinator, '_post_memory') as save, patch.object(coordinator, '_github_request') as github:
            result = coordinator.prepare(EXECUTION_ID, persist=True)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'review_pending')
        save.assert_not_called()
        github.assert_not_called()

    def test_prepare_persists_approval_request_but_performs_no_github_write(self):
        coordinator = self.make_coordinator()
        with patch.object(coordinator, '_post_memory', return_value=True) as save, patch.object(
            coordinator, 'promotion', return_value=None
        ), patch.object(coordinator, '_github_request') as github:
            result = coordinator.prepare(EXECUTION_ID, persist=True)
        self.assertTrue(result['success'])
        prepared = result['promotion']
        self.assertEqual(prepared['status'], 'awaiting_approval')
        self.assertEqual(prepared['promotion_id'], PROMOTION_ID)
        self.assertEqual(prepared['proposal_commit_sha'], PROPOSAL_SHA)
        self.assertFalse(prepared['github_write_performed'])
        self.assertFalse(prepared['pull_request_created'])
        self.assertRegex(prepared['approval_code'], r'^[A-F0-9]{6}$')
        save.assert_called_once()
        github.assert_not_called()

    def test_wrong_approval_code_is_rejected_without_github_write(self):
        coordinator = self.make_coordinator()
        with patch.object(coordinator, 'promotion', return_value=promotion(status='awaiting_approval')), patch.object(
            coordinator, '_post_memory'
        ) as save, patch.object(coordinator, '_github_request') as github:
            result = coordinator.approve(PROMOTION_ID, 'BAD999')
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'approval_code_invalid')
        save.assert_not_called()
        github.assert_not_called()

    def test_approval_revalidates_exact_review_identity(self):
        gate = FakeReviewGate(review=ready_review(proposal_commit_sha='c' * 40))
        coordinator = self.make_coordinator(gate)
        with patch.object(coordinator, 'promotion', return_value=promotion(status='awaiting_approval')), patch.object(
            coordinator, '_post_memory'
        ) as save:
            result = coordinator.approve(PROMOTION_ID, 'ABC123')
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'review_identity_drift')
        save.assert_not_called()

    def test_valid_approval_is_persisted_and_still_does_not_write_github(self):
        coordinator = self.make_coordinator()
        with patch.object(coordinator, 'promotion', return_value=promotion(status='awaiting_approval')), patch.object(
            coordinator, '_post_memory', return_value=True
        ) as save, patch.object(coordinator, '_github_request') as github:
            result = coordinator.approve(PROMOTION_ID, 'ABC123')
        self.assertTrue(result['success'])
        approved = result['promotion']
        self.assertEqual(approved['status'], 'approved')
        self.assertTrue(approved['approval_granted'])
        self.assertIsNotNone(approved['approval_expires_at'])
        save.assert_called_once()
        github.assert_not_called()

    def test_execute_requires_unexpired_approval(self):
        coordinator = self.make_coordinator()
        expired = promotion(status='approved', approval_expires_at=(NOW - timedelta(minutes=1)).isoformat())
        with patch.object(coordinator, 'promotion', return_value=expired), patch.object(
            coordinator, '_github_request'
        ) as github:
            result = coordinator.execute(PROMOTION_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'promotion_approval_expired')
        github.assert_not_called()

    def test_execute_revalidates_ready_review_before_any_pr_write(self):
        gate = FakeReviewGate(review=ready_review(gate_status='not_ready'))
        coordinator = self.make_coordinator(gate)
        with patch.object(coordinator, 'promotion', return_value=promotion()), patch.object(
            coordinator, '_github_request'
        ) as github:
            result = coordinator.execute(PROMOTION_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'fresh_review_failed:review_not_ready')
        github.assert_not_called()

    def test_existing_exact_pr_is_idempotently_reused_without_post(self):
        coordinator = self.make_coordinator()
        calls = []

        def github(method, path, **kwargs):
            calls.append((method, path, kwargs))
            self.assertEqual(method, 'GET')
            return FakeResponse(200, [pr_payload()])

        with patch.object(coordinator, 'promotion', return_value=promotion()), patch.object(
            coordinator, '_github_request', side_effect=github
        ), patch.object(coordinator, '_post_memory', return_value=True):
            result = coordinator.execute(PROMOTION_ID)
        self.assertTrue(result['success'])
        self.assertFalse(result['promotion']['github_write_performed'])
        self.assertTrue(result['promotion']['pull_request_created'])
        self.assertEqual([call[0] for call in calls], ['GET'])

    def test_successful_execute_creates_only_pr_and_persists_exact_head(self):
        coordinator = self.make_coordinator()
        calls = []

        def github(method, path, **kwargs):
            calls.append((method, path, kwargs))
            if method == 'GET':
                return FakeResponse(200, [])
            if method == 'POST' and path == '/pulls':
                return FakeResponse(201, pr_payload())
            raise AssertionError((method, path))

        with patch.object(coordinator, 'promotion', return_value=promotion()), patch.object(
            coordinator, '_github_request', side_effect=github
        ), patch.object(coordinator, '_post_memory', return_value=True) as save:
            result = coordinator.execute(PROMOTION_ID)

        self.assertTrue(result['success'])
        updated = result['promotion']
        self.assertEqual(updated['status'], 'pull_request_created')
        self.assertEqual(updated['pull_request_head_sha'], PROPOSAL_SHA)
        self.assertTrue(updated['github_write_performed'])
        self.assertTrue(updated['pull_request_created'])
        self.assertFalse(updated['automatic_merge_performed'])
        self.assertFalse(updated['direct_main_write_performed'])
        self.assertFalse(updated['production_deployment_performed'])
        self.assertFalse(updated['unknown_side_effect_retry_performed'])
        self.assertEqual([call[0] for call in calls], ['GET', 'POST'])
        post_payload = calls[1][2]['json']
        self.assertEqual(post_payload['head'], BRANCH)
        self.assertEqual(post_payload['base'], 'main')
        self.assertNotIn('merge', post_payload)
        save.assert_called_once()

    def test_permission_denied_is_safe_and_does_not_retry_post(self):
        coordinator = self.make_coordinator()
        calls = []

        def github(method, path, **kwargs):
            calls.append((method, path))
            if method == 'GET':
                return FakeResponse(200, [])
            return FakeResponse(403, {'message': 'Resource not accessible by personal access token'})

        with patch.object(coordinator, 'promotion', return_value=promotion()), patch.object(
            coordinator, '_github_request', side_effect=github
        ), patch.object(coordinator, '_post_memory') as save:
            result = coordinator.execute(PROMOTION_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'github_pull_request_permission_denied')
        self.assertEqual(calls, [('GET', '/pulls'), ('POST', '/pulls')])
        save.assert_not_called()

    def test_timeout_verifies_read_only_and_never_blindly_retries_post(self):
        coordinator = self.make_coordinator()
        calls = []
        get_count = {'value': 0}

        def github(method, path, **kwargs):
            calls.append((method, path))
            if method == 'GET':
                get_count['value'] += 1
                return FakeResponse(200, [] if get_count['value'] == 1 else [pr_payload()])
            if method == 'POST':
                raise requests.Timeout('unknown outcome')
            raise AssertionError((method, path))

        with patch.object(coordinator, 'promotion', return_value=promotion()), patch.object(
            coordinator, '_github_request', side_effect=github
        ), patch.object(coordinator, '_post_memory', return_value=True):
            result = coordinator.execute(PROMOTION_ID)
        self.assertTrue(result['success'])
        self.assertTrue(result['promotion']['pr_verified_after_unknown_outcome'])
        self.assertFalse(result['promotion']['unknown_side_effect_retry_performed'])
        self.assertEqual(calls.count(('POST', '/pulls')), 1)
        self.assertEqual(calls.count(('GET', '/pulls')), 2)

    def test_unknown_timeout_outcome_blocks_retry_when_verification_finds_nothing(self):
        coordinator = self.make_coordinator()
        calls = []

        def github(method, path, **kwargs):
            calls.append((method, path))
            if method == 'GET':
                return FakeResponse(200, [])
            if method == 'POST':
                raise requests.Timeout('unknown outcome')
            raise AssertionError((method, path))

        with patch.object(coordinator, 'promotion', return_value=promotion()), patch.object(
            coordinator, '_github_request', side_effect=github
        ):
            result = coordinator.execute(PROMOTION_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'github_pr_outcome_unknown')
        self.assertTrue(result['retry_blocked'])
        self.assertEqual(calls.count(('POST', '/pulls')), 1)


class V216IntegrationTests(unittest.TestCase):
    def test_v216_import_and_safety_contract(self):
        import app_v2_16 as app216
        self.assertEqual(app216.VERSION_SHORT, 'v2.16.0')
        self.assertIsNotNone(app216.app)
        self.assertIs(app216.base.handle_message, app216.handle_message_v216)
        self.assertIn('maintenance_promotion', app216.base.SPECIAL_MEMORY_CATEGORIES)
        self.assertIn('maintenance_promotion.py', app216.v210.v297._safe_source_files())
        status = app216.PROMOTION.status()
        self.assertFalse(status['automatic_pull_request_creation_enabled'])
        self.assertFalse(status['automatic_merge_enabled'])
        self.assertFalse(status['direct_main_write_enabled'])
        self.assertFalse(status['automatic_production_deployment_enabled'])

    def test_status_command_is_model_free(self):
        import app_v2_16 as app216
        with patch.object(app216.PROMOTION, 'recent', return_value=[]), patch.object(
            app216.PROMOTION, 'status', return_value={'github_token_present': True}
        ), patch.object(app216.base, 'groq') as groq:
            payload, status = app216.handle_message_v216('Show maintenance promotion gate')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        self.assertIn('Automatic merge: disabled', payload['reply'])
        groq.assert_not_called()

    def test_prepare_command_surfaces_fresh_approval_code(self):
        import app_v2_16 as app216
        fake = promotion(status='awaiting_approval', approval_granted=False, approval_expires_at=None)
        with patch.object(
            app216.PROMOTION, 'prepare',
            return_value={'success': True, 'promotion': fake, 'saved': True, 'existing': False},
        ):
            payload, status = app216.handle_message_v216(f'Prepare maintenance promotion {EXECUTION_ID}')
        self.assertEqual(status, 200)
        self.assertIn(f'Promotion: {PROMOTION_ID}', payload['reply'])
        self.assertIn('Approval code: ABC123', payload['reply'])
        self.assertIn('No GitHub write occurred during preparation.', payload['reply'])

    def test_execute_command_never_claims_merge_or_deploy(self):
        import app_v2_16 as app216
        fake = promotion(
            status='pull_request_created', pull_request_created=True, github_write_performed=True,
            pull_request_number=17, pull_request_url='https://github.com/tylerstong66/Tyler-ai/pull/17',
        )
        with patch.object(
            app216.PROMOTION, 'execute',
            return_value={'success': True, 'promotion': fake, 'pull_request': {'number': 17}},
        ):
            payload, status = app216.handle_message_v216(f'Execute approved maintenance promotion {PROMOTION_ID}')
        self.assertEqual(status, 200)
        self.assertIn('Automatic merge performed: no', payload['reply'])
        self.assertIn('Production deployment performed: no', payload['reply'])
        self.assertIn('The pull request has NOT been merged.', payload['reply'])

    def test_diagnostics_route_requires_authentication(self):
        import app_v2_16 as app216
        with app216.app.test_client() as client:
            response = client.get('/diagnostics/maintenance/promotion')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
