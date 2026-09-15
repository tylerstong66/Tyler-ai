import copy
import json
import unittest
from unittest.mock import Mock, patch

import app


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.config = patch.multiple(app, SUPABASE_URL='https://example.invalid',
                                     SUPABASE_KEY='test-only', N8N_WEBHOOK_URL='https://example.invalid/email',
                                     N8N_WEBHOOK_KEY='test-only', TYLER_DEFAULT_EMAIL='test@example.invalid')
        self.config.start()
        self.addCleanup(self.config.stop)

    def response(self, payload, status=200):
        return Mock(ok=status < 400, status_code=status, json=Mock(return_value=payload))

    def task(self, tool='send_email', status='pending'):
        return {'task_id': 1, 'status': 'running', 'current_step': 0,
                'goal': 'test', 'original_request': 'test', 'final_answer': 'test',
                'required_effects': [], 'steps': [{'id': 1, 'tool': tool,
                'status': status, 'attempts': 0, 'approved': True}],
                'completion_receipts': [], 'replans': 0}

    def run_with_store(self, task, execute):
        saved = copy.deepcopy(task)
        def persist(t):
            saved.clear()
            saved.update(copy.deepcopy(t))
        with patch.object(app, 'load_task', side_effect=lambda _: copy.deepcopy(saved)), \
             patch.object(app, 'persist_task', side_effect=persist), \
             patch.object(app, 'execute_task_step', execute), \
             patch.object(app, 'replan_task') as replan:
            result = app.run_task(1)
        return result, replan

    def test_old_memory_is_queried_by_id(self):
        with patch.object(app.requests, 'get', return_value=self.response([{'id': 1}])) as get:
            self.assertEqual(app.get_memory(1), {'id': 1})
            self.assertEqual(get.call_args.kwargs['params']['id'], 'eq.1')
            self.assertEqual(get.call_args.kwargs['params']['limit'], 1)

    def test_missing_memory_returns_none(self):
        with patch.object(app.requests, 'get', return_value=self.response([])):
            self.assertIsNone(app.get_memory(1))

    def test_email_requires_auth_before_dispatch(self):
        with patch.object(app, 'N8N_WEBHOOK_KEY', None), patch.object(app.requests, 'post') as post:
            with self.assertRaises(RuntimeError):
                app.send_email_via_n8n('test', 'test')
            post.assert_not_called()

    def test_email_accepts_only_explicit_receipt(self):
        receipt = {'success': True, 'sent': True, 'message_id': 'gmail-test'}
        with patch.object(app.requests, 'post', return_value=self.response(receipt)) as post:
            self.assertEqual(app.send_email_via_n8n('test', 'test'), receipt)
            self.assertEqual(post.call_args.kwargs['headers'], {'X-Tyler-Key': 'test-only'})
            self.assertFalse(post.call_args.kwargs['allow_redirects'])

    def test_rejects_false_or_missing_receipts(self):
        for receipt in ({'success': False}, {}, [], {'success': True, 'sent': True},
                        {'success': True, 'sent': True, 'message_id': ''}):
            with self.subTest(receipt=receipt), patch.object(app.requests, 'post', return_value=self.response(receipt)):
                with self.assertRaises(RuntimeError):
                    app.send_email_via_n8n('test', 'test')

    def test_plain_text_response_is_not_success(self):
        response = self.response(None)
        response.json.side_effect = ValueError('not JSON')
        with patch.object(app.requests, 'post', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'unconfirmed'):
                app.send_email_via_n8n('test', 'test')

    def test_timeout_dispatches_once(self):
        with patch.object(app.requests, 'post', side_effect=app.requests.Timeout()) as post:
            with self.assertRaisesRegex(RuntimeError, 'unknown'):
                app.send_email_via_n8n('test', 'test')
            self.assertEqual(post.call_count, 1)

    def test_task_never_retries_or_replans_side_effect(self):
        for tool in app.SIDE_EFFECT_TOOLS:
            with self.subTest(tool=tool):
                execute = Mock(side_effect=RuntimeError('timeout'))
                result, replan = self.run_with_store(self.task(tool), execute)
                self.assertFalse(result['success'])
                self.assertEqual(execute.call_count, 1)
                replan.assert_not_called()

    def test_resume_of_interrupted_write_does_not_dispatch(self):
        execute = Mock()
        result, _ = self.run_with_store(self.task(status='running'), execute)
        self.assertFalse(result['success'])
        execute.assert_not_called()

    def test_safe_step_still_retries(self):
        execute = Mock(side_effect=[RuntimeError('temporary'), 'ok'])
        result, replan = self.run_with_store(self.task('reason'), execute)
        self.assertTrue(result['success'])
        self.assertEqual(execute.call_count, 2)
        replan.assert_not_called()

    def test_stale_update_is_rejected(self):
        task = self.task()
        task['_storage_revision'] = '{"old":"state"}'
        with patch.object(app.requests, 'patch', return_value=self.response([])) as update:
            with self.assertRaisesRegex(RuntimeError, 'another request'):
                app.persist_task(task)
            params = update.call_args.kwargs['params']
            self.assertEqual(params['id'], 'eq.1')
            self.assertEqual(params['category'], 'eq.task_state')
            # PostgREST top-level eq consumes the literal remainder after eq.;
            # JSON-quoting here would compare against added quote characters.
            self.assertEqual(params['memories'][3:], task['_storage_revision'])

    def test_revision_not_persisted_inside_state(self):
        task = self.task()
        task['_storage_revision'] = 'old'
        with patch.object(app.requests, 'patch', return_value=self.response([{'memories': 'new'}])) as update:
            app.persist_task(task)
            payload = json.loads(update.call_args.kwargs['json']['memories'])
            self.assertNotIn('_storage_revision', payload)
            self.assertNotIn('task_id', payload)
            self.assertEqual(task['_storage_revision'], 'new')


if __name__ == '__main__':
    unittest.main()
