import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import requests

import app_v2_17_1 as app2171


TARGET = 'c' * 40
ROLLBACK = 'b' * 40
MERGE_ID = 'MRG-1234567890'
DPL_ID = app2171._deployment_id(MERGE_ID, TARGET)
NOW = datetime(2026, 9, 16, 17, 0, tzinfo=timezone.utc)


def merge_record(**overrides):
    item = {
        'merge_id': MERGE_ID,
        'promotion_id': 'PRO-1234567890',
        'execution_id': 'EXE-1234567890',
        'review_id': 'REV-1234567890',
        'pull_request_number': 42,
        'status': 'merged',
        'human_gated_merge_performed': True,
        'automatic_merge_performed': False,
        'merge_commit_sha': TARGET,
    }
    item.update(overrides)
    return item


def deployment_record(status='approved', **overrides):
    item = {
        'deployment_id': DPL_ID,
        'merge_id': MERGE_ID,
        'promotion_id': 'PRO-1234567890',
        'execution_id': 'EXE-1234567890',
        'review_id': 'REV-1234567890',
        'pull_request_number': 42,
        'target_commit_sha': TARGET,
        'rollback_commit_sha': ROLLBACK,
        'status': status,
        'approval_code': 'A1B2C3',
        'approval_granted': status == 'approved',
        'approval_expires_at': (NOW + timedelta(minutes=30)).isoformat() if status == 'approved' else None,
        'deployment_dispatched': status in {'deployment_dispatched', 'deployed'},
        'production_deployment_performed': status == 'deployed',
        'post_deploy_health_verified': status == 'deployed',
        'rollback_performed': False,
        'unknown_dispatch_retry_performed': False,
    }
    item.update(overrides)
    return item


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload


class ProductionGateTests(unittest.TestCase):
    def test_version_and_fail_closed_status(self):
        self.assertEqual(app2171.VERSION_SHORT, 'v2.17.1')
        self.assertIs(app2171.base.handle_message, app2171.handle_message_v2171)
        self.assertFalse(app2171.production_status()['automatic_production_deployment_enabled'])
        self.assertFalse(app2171.production_status()['blind_retry_after_unknown_dispatch_outcome_enabled'])

    def test_deployment_id_is_bound_to_merge_and_target(self):
        self.assertEqual(DPL_ID, app2171._deployment_id(MERGE_ID.lower(), TARGET.upper()))
        self.assertNotEqual(DPL_ID, app2171._deployment_id(MERGE_ID, 'd' * 40))

    def test_prepare_pins_current_runtime_as_rollback_without_deploy(self):
        with patch.object(app2171, '_merged_record', return_value=(merge_record(), None)), patch.object(
            app2171, '_validate', return_value=({'current_main': TARGET, 'target': TARGET, 'runtime': ROLLBACK}, None)
        ), patch.object(app2171, '_record', return_value=None), patch.object(app2171, '_post', return_value=True):
            result = app2171.prepare_production(MERGE_ID)
        self.assertTrue(result['success'])
        record = result['deployment']
        self.assertEqual(record['status'], 'awaiting_approval')
        self.assertEqual(record['target_commit_sha'], TARGET)
        self.assertEqual(record['rollback_commit_sha'], ROLLBACK)
        self.assertFalse(record['production_deployment_performed'])
        self.assertRegex(record['approval_code'], r'^[A-F0-9]{6}$')

    def test_approval_revalidates_runtime_identity(self):
        waiting = deployment_record(status='awaiting_approval', approval_granted=False, approval_expires_at=None)
        with patch.object(app2171, '_record', return_value=waiting), patch.object(
            app2171, '_merged_record', return_value=(merge_record(), None)
        ), patch.object(app2171, '_validate', return_value=({'runtime': 'd' * 40}, 'runtime_commit_drift')), patch.object(
            app2171, '_post'
        ) as save:
            result = app2171.approve_production(DPL_ID, 'A1B2C3')
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'runtime_commit_drift')
        save.assert_not_called()

    def test_execute_dispatches_exact_target_and_rollback_once(self):
        captured = {}
        def github(method, path, **kwargs):
            captured.update({'method': method, 'path': path, 'json': kwargs.get('json')})
            return FakeResponse(204, {})
        with patch.object(app2171, '_now', return_value=NOW), patch.object(
            app2171, '_record', return_value=deployment_record()
        ), patch.object(app2171, '_merged_record', return_value=(merge_record(), None)), patch.object(
            app2171, '_validate', return_value=({'runtime': ROLLBACK}, None)
        ), patch.object(app2171, '_github', side_effect=github), patch.object(app2171, '_post', return_value=True):
            result = app2171.execute_production(DPL_ID)
        self.assertTrue(result['success'])
        self.assertEqual(captured['method'], 'POST')
        self.assertEqual(captured['path'], '/dispatches')
        payload = captured['json']['client_payload']
        self.assertEqual(payload['target_sha'], TARGET)
        self.assertEqual(payload['rollback_sha'], ROLLBACK)

    def test_unknown_dispatch_outcome_blocks_blind_retry(self):
        with patch.object(app2171, '_now', return_value=NOW), patch.object(
            app2171, '_record', return_value=deployment_record()
        ), patch.object(app2171, '_merged_record', return_value=(merge_record(), None)), patch.object(
            app2171, '_validate', return_value=({'runtime': ROLLBACK}, None)
        ), patch.object(app2171, '_github', side_effect=requests.Timeout('unknown')), patch.object(
            app2171, '_find_run', return_value=None
        ), patch.object(app2171, '_post', return_value=True):
            result = app2171.execute_production(DPL_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['deployment']['status'], 'dispatch_outcome_unknown')
        self.assertFalse(result['deployment']['unknown_dispatch_retry_performed'])

    def test_verify_success_requires_exact_runtime_commit(self):
        rec = deployment_record(status='deployment_dispatched', approval_granted=True)
        run = {'id': 1, 'status': 'completed', 'conclusion': 'success', 'html_url': 'https://github/actions/1'}
        with patch.object(app2171, '_record', return_value=rec), patch.object(app2171, '_find_run', return_value=run), patch.object(
            app2171, '_runtime_status', return_value={'commit': TARGET, 'version': 'v2.17.1'}
        ), patch.object(app2171, '_post', return_value=True):
            result = app2171.verify_production(DPL_ID)
        self.assertTrue(result['success'])
        self.assertEqual(result['deployment']['status'], 'deployed')
        self.assertTrue(result['deployment']['post_deploy_health_verified'])

    def test_verify_failed_target_recognizes_rollback(self):
        rec = deployment_record(status='deployment_dispatched', approval_granted=True)
        run = {'id': 2, 'status': 'completed', 'conclusion': 'failure', 'html_url': 'https://github/actions/2'}
        with patch.object(app2171, '_record', return_value=rec), patch.object(app2171, '_find_run', return_value=run), patch.object(
            app2171, '_runtime_status', return_value={'commit': ROLLBACK, 'version': 'v2.17.1'}
        ), patch.object(app2171, '_post', return_value=True):
            result = app2171.verify_production(DPL_ID)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'deployment_failed_and_rolled_back')
        self.assertTrue(result['deployment']['rollback_performed'])

    def test_status_command_is_model_free(self):
        with patch.object(app2171, '_recent', return_value=[]), patch.object(app2171, 'production_status', return_value={
            'github_token_present': True,
            'render_auto_deploy_confirmed_disabled': True,
            'runtime_commit_present': True,
            'automatic_production_deployment_enabled': False,
            'blind_retry_after_unknown_dispatch_outcome_enabled': False,
        }), patch.object(app2171.base, 'groq') as groq:
            payload, status = app2171.handle_message_v2171('Show production promotion gate')
        self.assertEqual(status, 200)
        self.assertIn('Required workflow secret: RENDER_DEPLOY_HOOK_URL', payload['reply'])
        groq.assert_not_called()

    def test_diagnostics_unauthenticated_is_401(self):
        client = app2171.app.test_client()
        with patch.object(app2171.base, 'authorized', return_value=False), patch.object(app2171.base, 'ui_logged_in', return_value=False):
            response = client.get('/diagnostics/maintenance/production')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()