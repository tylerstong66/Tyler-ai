import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import requests

from maintenance_merge import MaintenanceMergeCoordinator, merge_id_for


EXECUTION_ID = 'EXE-ABCDEF1234'
REVIEW_ID = 'REV-1234567890'
PROMOTION_ID = 'PRO-1234567890'
BASE_SHA = 'a' * 40
PROPOSAL_SHA = 'b' * 40
MERGE_SHA = 'c' * 40
BRANCH = 'tyler-maintenance/exe-abcdef1234'
MERGE_ID = merge_id_for(PROMOTION_ID, PROPOSAL_SHA)
NOW = datetime(2026, 9, 16, 16, 0, tzinfo=timezone.utc)


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


def promotion(**overrides):
    item = {
        'promotion_id': PROMOTION_ID,
        'review_id': REVIEW_ID,
        'execution_id': EXECUTION_ID,
        'repository': 'tylerstong66/Tyler-ai',
        'base_branch': 'main',
        'review_branch': BRANCH,
        'base_commit_sha': BASE_SHA,
        'proposal_commit_sha': PROPOSAL_SHA,
        'status': 'pull_request_created',
        'pull_request_created': True,
        'pull_request_number': 17,
        'pull_request_url': 'https://github.com/tylerstong66/Tyler-ai/pull/17',
    }
    item.update(overrides)
    return item


def pr_payload(merged=False, **overrides):
    item = {
        'number': 17,
        'html_url': 'https://github.com/tylerstong66/Tyler-ai/pull/17',
        'state': 'closed' if merged else 'open',
        'draft': False,
        'merged': merged,
        'merged_at': NOW.isoformat() if merged else None,
        'merge_commit_sha': MERGE_SHA if merged else '',
        'mergeable': True,
        'head': {'ref': BRANCH, 'sha': PROPOSAL_SHA},
        'base': {'ref': 'main', 'sha': BASE_SHA},
    }
    item.update(overrides)
    return item


def merge_record(status='approved', **overrides):
    item = {
        'schema': 'tyler_maintenance_merge_v1',
        'merge_id': MERGE_ID,
        'promotion_id': PROMOTION_ID,
        'review_id': REVIEW_ID,
        'execution_id': EXECUTION_ID,
        'repository': 'tylerstong66/Tyler-ai',
        'base_branch': 'main',
        'review_branch': BRANCH,
        'base_commit_sha': BASE_SHA,
        'proposal_commit_sha': PROPOSAL_SHA,
        'pull_request_number': 17,
        'pull_request_url': 'https://github.com/tylerstong66/Tyler-ai/pull/17',
        'status': status,
        'approval_code': 'ABC123',
        'approval_granted': status == 'approved',
        'approval_expires_at': (NOW + timedelta(minutes=30)).isoformat() if status == 'approved' else None,
        'human_gated_merge_performed': False,
        'automatic_merge_performed': False,
        'production_deployment_performed': False,
        'unknown_side_effect_retry_performed': False,
    }
    item.update(overrides)
    return item


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

    def review(self, execution_id, persist=False):
        if not self.success:
            return {'success': False, 'error': self.error or 'review_failed'}
        return {'success': True, 'review': dict(self.current)}


class MaintenanceMergeTests(unittest.TestCase):
    def make_coordinator(self, review_gate=None, auto_deploy_disabled=True):
        return MaintenanceMergeCoordinator(
            promotion_loader=lambda _: promotion(),
            review_gate=review_gate or FakeReviewGate(),
            supabase_url_fn=lambda: 'https://example.supabase.co',
            headers_fn=lambda: {'apikey': 'test', 'Authorization': 'Bearer test'},
            version_fn=lambda: 'v2.17.0',
            github_token_fn=lambda: 'test-token',
            github_repository_fn=lambda: 'tylerstong66/Tyler-ai',
            github_base_branch_fn=lambda: 'main',
            render_auto_deploy_disabled_fn=lambda: auto_deploy_disabled,
            now_fn=lambda: NOW,
        )

    def test_merge_id_is_bound_to_promotion_and_commit(self):
        self.assertEqual(MERGE_ID, merge_id_for(PROMOTION_ID.lower(), PROPOSAL_SHA.upper()))
        self.assertTrue(MERGE_ID.startswith('MRG-'))
        self.assertNotEqual(MERGE_ID, merge_id_for(PROMOTION_ID, 'd' * 40))

    def test_status_is_fail_closed(self):
        status = self.make_coordinator(auto_deploy_disabled=False).status()
        self.assertFalse(status['render_auto_deploy_confirmed_disabled'])
        self.assertTrue(status['render_auto_deploy_must_be_disabled_before_merge'])
        self.assertTrue(status['human_merge_approval_required'])
        self.assertFalse(status['automatic_merge_enabled'])
        self.assertFalse(status['automatic_production_deployment_enabled'])
        self.assertFalse(status['blind_retry_after_unknown_merge_outcome_enabled'])

    def test_prepare_blocks_when_render_auto_deploy_not_confirmed_disabled(self):
        coordinator = self.make_coordinator(auto_deploy_disabled=False)
        with patch.object(coordinator, '_github_request') as github, patch.object(coordinator, '_post_memory') as save:
            result = coordinator.prepare(PROMOTION_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'render_auto_deploy_not_confirmed_disabled')
        github.assert_not_called()
        save.assert_not_called()

    def test_prepare_requires_fresh_ready_review(self):
        gate = FakeReviewGate(review=ready_review(gate_status='pending'))
        coordinator = self.make_coordinator(gate)
        with patch.object(coordinator, '_github_request') as github:
            result = coordinator.prepare(PROMOTION_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'fresh_review_failed:review_pending')
        github.assert_not_called()

    def test_prepare_rejects_pr_head_drift(self):
        coordinator = self.make_coordinator()
        bad = pr_payload()
        bad['head']['sha'] = 'd' * 40
        with patch.object(coordinator, '_github_request', return_value=FakeResponse(200, bad)), patch.object(
            coordinator, '_post_memory'
        ) as save:
            result = coordinator.prepare(PROMOTION_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'pull_request_head_sha_drift')
        save.assert_not_called()

    def test_prepare_persists_human_approval_request_without_merge(self):
        coordinator = self.make_coordinator()
        with patch.object(coordinator, '_github_request', return_value=FakeResponse(200, pr_payload())), patch.object(
            coordinator, 'merge_record', return_value=None
        ), patch.object(coordinator, '_post_memory', return_value=True) as save:
            result = coordinator.prepare(PROMOTION_ID)
        self.assertTrue(result['success'])
        record = result['merge']
        self.assertEqual(record['status'], 'awaiting_approval')
        self.assertRegex(record['approval_code'], r'^[A-F0-9]{6}$')
        self.assertFalse(record['human_gated_merge_performed'])
        self.assertFalse(record['production_deployment_performed'])
        save.assert_called_once()

    def test_approval_revalidates_pr_and_ready_review(self):
        coordinator = self.make_coordinator()
        awaiting = merge_record(status='awaiting_approval', approval_granted=False, approval_expires_at=None)
        with patch.object(coordinator, 'merge_record', return_value=awaiting), patch.object(
            coordinator, '_github_request', return_value=FakeResponse(200, pr_payload())
        ), patch.object(coordinator, '_post_memory', return_value=True):
            result = coordinator.approve(MERGE_ID, 'ABC123')
        self.assertTrue(result['success'])
        self.assertEqual(result['merge']['status'], 'approved')
        self.assertTrue(result['merge']['approval_granted'])

    def test_execute_requires_unexpired_approval(self):
        coordinator = self.make_coordinator()
        expired = merge_record(approval_expires_at=(NOW - timedelta(minutes=1)).isoformat())
        with patch.object(coordinator, 'merge_record', return_value=expired), patch.object(coordinator, '_github_request') as github:
            result = coordinator.execute(MERGE_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'merge_approval_expired')
        github.assert_not_called()

    def test_execute_revalidates_before_merge_write(self):
        gate = FakeReviewGate(review=ready_review(gate_status='not_ready'))
        coordinator = self.make_coordinator(gate)
        with patch.object(coordinator, 'merge_record', return_value=merge_record()), patch.object(coordinator, '_github_request') as github:
            result = coordinator.execute(MERGE_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'fresh_review_failed:review_not_ready')
        github.assert_not_called()

    def test_successful_execute_merges_exact_sha_and_does_not_deploy(self):
        coordinator = self.make_coordinator()
        calls = []

        def github(method, path, **kwargs):
            calls.append((method, path, kwargs))
            if method == 'GET':
                return FakeResponse(200, pr_payload()) if len([c for c in calls if c[0] == 'GET']) == 1 else FakeResponse(200, pr_payload(merged=True))
            if method == 'PUT' and path == '/pulls/17/merge':
                return FakeResponse(200, {'merged': True, 'sha': MERGE_SHA, 'message': 'Pull Request successfully merged'})
            raise AssertionError((method, path))

        with patch.object(coordinator, 'merge_record', return_value=merge_record()), patch.object(
            coordinator, '_github_request', side_effect=github
        ), patch.object(coordinator, '_post_memory', return_value=True):
            result = coordinator.execute(MERGE_ID)
        self.assertTrue(result['success'])
        record = result['merge']
        self.assertEqual(record['status'], 'merged')
        self.assertEqual(record['merge_commit_sha'], MERGE_SHA)
        self.assertTrue(record['human_gated_merge_performed'])
        self.assertFalse(record['automatic_merge_performed'])
        self.assertFalse(record['production_deployment_performed'])
        put = [c for c in calls if c[0] == 'PUT'][0]
        self.assertEqual(put[2]['json']['sha'], PROPOSAL_SHA)
        self.assertEqual(put[2]['json']['merge_method'], 'merge')

    def test_timeout_verifies_read_only_and_never_blindly_retries_merge(self):
        coordinator = self.make_coordinator()
        calls = []
        gets = {'n': 0}

        def github(method, path, **kwargs):
            calls.append((method, path))
            if method == 'GET':
                gets['n'] += 1
                if gets['n'] == 1:
                    return FakeResponse(200, pr_payload())
                return FakeResponse(200, pr_payload(merged=True))
            if method == 'PUT':
                raise requests.Timeout('unknown')
            raise AssertionError((method, path))

        with patch.object(coordinator, 'merge_record', return_value=merge_record()), patch.object(
            coordinator, '_github_request', side_effect=github
        ), patch.object(coordinator, '_post_memory', return_value=True):
            result = coordinator.execute(MERGE_ID)
        self.assertTrue(result['success'])
        self.assertTrue(result['merge']['merge_verified_after_unknown_outcome'])
        self.assertFalse(result['merge']['unknown_side_effect_retry_performed'])
        self.assertEqual(calls.count(('PUT', '/pulls/17/merge')), 1)


class V217IntegrationTests(unittest.TestCase):
    def test_v217_import_and_safety_contract(self):
        import app_v2_17 as app217
        self.assertEqual(app217.VERSION_SHORT, 'v2.17.0')
        self.assertIsNotNone(app217.app)
        self.assertIs(app217.base.handle_message, app217.handle_message_v217)
        self.assertIn('maintenance_merge', app217.base.SPECIAL_MEMORY_CATEGORIES)
        self.assertIn('maintenance_merge.py', app217.v210.v297._safe_source_files())
        status = app217.MERGE_GATE.status()
        self.assertFalse(status['automatic_merge_enabled'])
        self.assertFalse(status['automatic_production_deployment_enabled'])

    def test_status_command_is_model_free(self):
        import app_v2_17 as app217
        with patch.object(app217.MERGE_GATE, 'recent', return_value=[]), patch.object(
            app217.MERGE_GATE,
            'status',
            return_value={'github_token_present': True, 'render_auto_deploy_confirmed_disabled': False},
        ), patch.object(app217.base, 'groq') as groq:
            payload, status = app217.handle_message_v217('Show maintenance merge gate')
        self.assertEqual(status, 200)
        self.assertTrue(payload['success'])
        self.assertIn('Merge is blocked unless Render Auto Deploy is confirmed disabled: yes', payload['reply'])
        groq.assert_not_called()

    def test_diagnostics_unauthenticated_is_401(self):
        import app_v2_17 as app217
        client = app217.app.test_client()
        with patch.object(app217.base, 'authorized', return_value=False), patch.object(app217.base, 'ui_logged_in', return_value=False):
            response = client.get('/diagnostics/maintenance/merge')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
