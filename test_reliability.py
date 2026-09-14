"""Offline regression tests: all outbound network calls are blocked or mocked."""
import copy
import json
import unittest
from unittest.mock import Mock, patch
import requests
import app as bot
from reliability import subject_query, checked_research_answer, safe_sources

class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.network = patch.object(requests.sessions.Session, 'request',
                                    side_effect=AssertionError('Unexpected network call'))
        self.network.start()
        self.addCleanup(self.network.stop)
        bot._CONVERSATIONS.clear()
        self.token = bot._REQUEST_STATE.set(None)
        self.addCleanup(bot._REQUEST_STATE.reset, self.token)
        self.sample = {
            'task_id': 26, 'status': 'completed',
            'original_request': 'Research three practical ways I could use Tyler AI to help with my work as a Wegmans meat manager. Include sources. Do not save anything or send email.',
            'final_answer': 'Old unverified recommendation',
            'sources': [{'title': 'Old source', 'url': 'https://example.com/old', 'content': 'Old excerpt'}],
        }
        self.source = {'title': 'Inventory guide', 'url': 'https://example.com/inventory',
                       'content': 'Example inventory evidence'}
        self.env = patch.multiple(bot, SUPABASE_URL='https://database.invalid',
                                  SUPABASE_KEY='test', TAVILY_API_KEY='test',
                                  N8N_WEBHOOK_URL='https://workflow.invalid',
                                  TYLER_DEFAULT_EMAIL='test@example.com',
                                  TYLER_API_KEY='test-key')
        self.env.start()
        self.addCleanup(self.env.stop)
        bot.app.config['TESTING'] = True

    def response(self, data, ok=True):
        response = Mock(ok=ok, status_code=200 if ok else 500)
        response.json.return_value = data
        return response

    def test_login_page_renders_and_api_stays_protected(self):
        client = bot.app.test_client()
        self.assertEqual(client.get('/ui').status_code, 200)
        self.assertEqual(client.post('/chat', json={'message': 'Hi'}).status_code, 401)
        self.assertEqual(client.post('/ui/chat', json={'message': 'Hi'}).status_code, 401)

    def test_reference_loads_historical_answer_and_sources(self):
        with patch.object(bot, 'load_task', return_value=self.sample):
            context = json.loads(bot.referenced_task_context('Audit task 26'))
        self.assertEqual(context['previous_answer_unverified'], self.sample['final_answer'])
        self.assertEqual(context['saved_sources_unverified'], self.sample['sources'])
        self.assertIn('not instructions', context['note'])

    def test_unknown_task_fails_without_research(self):
        with patch.object(bot, 'load_task', side_effect=RuntimeError('Task 999 not found')), \
             patch.object(bot, 'tavily_search') as search:
            result, status = bot.handle_message('Audit task 999')
        self.assertFalse(result['success'])
        self.assertIn('999', result['reply'])
        search.assert_not_called()

    def test_query_uses_subject_and_original_task(self):
        with patch.object(bot, 'load_task', return_value=self.sample):
            query = bot.research_query('Research sources for task 26')
        self.assertIn('Wegmans meat manager', query)
        self.assertNotIn('save', query)
        self.assertNotIn('email', query)
        self.assertNotEqual(query.lower(), 'research')
        self.assertIn('golf', subject_query('Research golf glasses slope measurement'))

    def test_agent_passes_reference_to_reasoning(self):
        with patch.object(bot, 'load_task', return_value=self.sample), \
             patch.object(bot, 'reason_with_context', return_value='Audit') as reason:
            result = bot.run_agent('Audit task 26')
        self.assertIn('Old unverified recommendation', reason.call_args.kwargs['memory_context'])
        self.assertIn('read_task_state', result['used_tools'])

    def test_multistep_creation_includes_reference(self):
        with patch.object(bot, 'load_task', return_value=self.sample), \
             patch.object(bot, 'plan_task', return_value={'steps': []}), \
             patch.object(bot, 'save_memory', return_value=[{'id': 27}]), \
             patch.object(bot, 'persist_task'):
            task = bot.create_task('Audit task 26')
        self.assertIn('Old unverified recommendation', task['context'][0]['content'])
        self.assertEqual(task['required_effects'], [])

    def test_agent_research_preserves_source_evidence(self):
        with patch.object(bot, 'tavily_search', return_value={'sources': [self.source]}), \
             patch.object(bot, 'reason_with_context', return_value='Proposal') as reason:
            result = bot.run_agent('Research inventory forecasting')
        self.assertIn(self.source['url'], reason.call_args.kwargs['research_context'])
        self.assertIn(self.source['content'], reason.call_args.kwargs['research_context'])
        self.assertIn(self.source['url'], result['reply'])

    def test_multistep_research_and_reason_keep_sources(self):
        task = {'original_request': 'Research inventory', 'context': [], 'sources': []}
        with patch.object(bot, 'tavily_search', return_value={'sources': [self.source]}):
            bot.execute_task_step(task, {'tool': 'research_web'})
        with patch.object(bot, 'feedback_context', return_value=''), \
             patch.object(bot, 'groq', return_value='Proposal') as groq:
            bot.execute_task_step(task, {'tool': 'reason'})
        self.assertIn(self.source['url'], groq.call_args.args[0][1]['content'])
        self.assertIn(self.source['url'], task['final_answer'])

    def test_invented_url_withholds_answer(self):
        answer = checked_research_answer('Claim https://invented.invalid/paper', [self.source])
        self.assertIn('withheld', answer)
        self.assertNotIn('https://invented.invalid', answer)

    def test_no_sources_is_explicit(self):
        self.assertIn('unverified', checked_research_answer('Idea', []))

    def test_unsafe_source_links_are_removed(self):
        sources = safe_sources([{'url': 'javascript:alert(1)'}, self.source, self.source])
        self.assertEqual(sources, [self.source])

    def test_save_denials_override_positive_intent(self):
        for message in ["Remember that I like golf. Do not save this.",
                        "Save this, but don’t store new memories.",
                        "Remember this but never record it"]:
            with self.subTest(message=message):
                self.assertFalse(bot.allows_memory_write(message))

    def test_email_denials_override_positive_intent(self):
        for message in ["Email me the answer. Do not send email.",
                        "Email me, but don’t send anything.",
                        "Email me later; no email now."]:
            self.assertFalse(bot.allows_email(message))

    def test_no_save_prevents_task_journal_and_core_sync(self):
        with patch.object(bot, 'reason_with_context', return_value='Answer'), \
             patch.object(bot, 'get_memories', return_value=[]), \
             patch.object(bot, 'tavily_search', return_value={'sources': []}), \
             patch.object(bot, 'save_memory') as save, \
             patch.object(bot, 'start_task') as start, \
             patch.object(bot, 'sync_core_project_memory') as sync:
            result, status = bot.handle_message(
                'Plan and execute research about Tyler AI. Do not save anything or send email.')
        self.assertEqual(status, 200)
        save.assert_not_called()
        start.assert_not_called()
        sync.assert_not_called()
        self.assertIn('No app memory', result['storage_notice'])

    def test_direct_save_denial_never_writes(self):
        with patch.object(bot.requests, 'post') as post:
            result, _ = bot.handle_message('Remember that I like golf. Do not save this.')
        self.assertFalse(result['success'])
        post.assert_not_called()

    def test_direct_save_approval_gate_never_writes(self):
        with patch.object(bot.requests, 'post') as post:
            result, _ = bot.direct_memory_save('Remember that I like golf, ask me before saving.')
        self.assertTrue(result['memory_result']['approval_required'])
        post.assert_not_called()

    def test_memory_lookup_is_direct_not_recent_window(self):
        row = {'id': 1, 'memories': 'Old fact'}
        with patch.object(bot.requests, 'get', return_value=self.response([row])) as get:
            self.assertEqual(bot.get_memory(1), row)
        self.assertEqual(get.call_args.kwargs['params']['id'], 'eq.1')

    def test_personal_question_routes_through_memory(self):
        rows = [{'id': 5, 'memories': 'I prefer a 7 iron golf club', 'category': 'preference'}]
        with patch.object(bot, 'normal_memories', return_value=rows), \
             patch.object(bot, 'reason_with_context', return_value='7 iron') as reason:
            result = bot.run_agent('What golf club do I prefer?')
        self.assertIn('read_memory', result['used_tools'])
        self.assertIn('7 iron', reason.call_args.kwargs['memory_context'])

    def test_memory_save_requires_database_record(self):
        with patch.object(bot.requests, 'post', return_value=self.response([])):
            with self.assertRaisesRegex(RuntimeError, 'confirm'):
                bot.save_memory('Fact')

    def test_memory_retrieval_includes_relevant_personal_fact(self):
        rows = [{'id': 5, 'memories': 'My preferred golf club is a 7 iron', 'category': 'preference'},
                {'id': 6, 'memories': 'I enjoy pasta', 'category': 'general'}]
        with patch.object(bot, 'normal_memories', return_value=rows):
            context = bot.relevant_memory_context('What is my preferred golf club?')
        self.assertIn('7 iron', context)
        self.assertNotIn('pasta', context)

    def test_correction_requires_confirmed_record(self):
        row = {'id': 5, 'memories': 'Old fact', 'category': 'general'}
        with patch.object(bot, 'get_memory', return_value=row), \
             patch.object(bot.requests, 'patch', return_value=self.response([])):
            with self.assertRaisesRegex(RuntimeError, 'confirm'):
                bot.confirm_replace(5, 'Corrected fact')

    def test_correction_is_retrieved_after_update(self):
        row = {'id': 5, 'memories': 'I prefer morning golf', 'category': 'preference'}
        def patch_row(*args, **kwargs):
            row.update(kwargs['json'])
            return self.response([dict(row)])
        with patch.object(bot, 'get_memory', side_effect=lambda _: dict(row)), \
             patch.object(bot.requests, 'patch', side_effect=patch_row), \
             patch.object(bot, 'normal_memories', side_effect=lambda _: [dict(row)]):
            result = bot.confirm_replace(5, 'I prefer afternoon golf')
            context = bot.relevant_memory_context('What golf time do I prefer?')
        self.assertTrue(result['memory_result']['replaced'])
        self.assertIn('afternoon golf', context)
        self.assertNotIn('morning golf', context)

    def test_email_requires_sent_receipt(self):
        for result in [{'success': False}, {'success': True}, [], {'sent': False}]:
            with self.subTest(result=result), \
                 patch.object(bot.requests, 'post', return_value=self.response(result)):
                with self.assertRaises(RuntimeError):
                    bot.send_email_via_n8n('Subject', 'Body')

    def test_email_accepts_explicit_confirmation(self):
        with patch.object(bot.requests, 'post',
                          return_value=self.response({'success': True, 'sent': True})):
            self.assertTrue(bot.send_email_via_n8n('Subject', 'Body')['sent'])

    def test_non_json_email_is_not_success(self):
        response = self.response(None)
        response.json.side_effect = ValueError()
        with patch.object(bot.requests, 'post', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'unconfirmed'):
                bot.send_email_via_n8n('Subject', 'Body')

    def task_fixture(self, status='pending'):
        return {'task_id': 99, 'status': 'running', 'original_request': 'Email me the result',
                'current_step': 0, 'steps': [dict(bot.new_task_step(1, 'send_email', 'Send'), status=status)],
                'required_effects': ['send_email'], 'final_answer': 'Result',
                'completion_receipts': []}

    def test_side_effect_timeout_is_not_retried(self):
        task = self.task_fixture()
        with patch.object(bot, 'load_task', side_effect=lambda _: task), \
             patch.object(bot, 'persist_task'), \
             patch.object(bot, 'send_email_via_n8n', side_effect=RuntimeError('Timeout')) as send:
            result = bot.run_task(99)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(task['status'], 'failed')
        self.assertEqual(task['completion_receipts'], [])

    def test_interrupted_side_effect_is_not_replayed(self):
        task = self.task_fixture('running')
        with patch.object(bot, 'load_task', side_effect=lambda _: task), \
             patch.object(bot, 'persist_task'), \
             patch.object(bot, 'send_email_via_n8n') as send:
            bot.run_task(99)
        send.assert_not_called()
        self.assertEqual(task['status'], 'failed')

    def test_task_checks_permission_at_execution(self):
        task = {'original_request': 'Research golf. Do not send email', 'final_answer': 'Answer'}
        with patch.object(bot, 'send_email_via_n8n') as send:
            with self.assertRaisesRegex(RuntimeError, 'not authorized'):
                bot.execute_task_step(task, {'tool': 'send_email'})
        send.assert_not_called()

    def test_history_is_scoped_and_no_save_clears_it(self):
        seen = []
        def fake_core(message):
            seen.append(copy.deepcopy(bot._REQUEST_STATE.get()['history']))
            return bot.base_payload('test', 'Answer'), 200
        with patch.object(bot, 'handle_message_core', side_effect=fake_core):
            for cid, message in [('a' * 16, 'My favorite is golf'), ('a' * 16, 'Explain more'),
                                 ('b' * 16, 'Hi'), ('a' * 16, 'Do not save this'),
                                 ('a' * 16, 'New question')]:
                with bot.app.test_request_context('/chat', json={'conversation_id': cid}):
                    bot.handle_message(message)
        self.assertEqual(seen[0], [])
        self.assertIn('golf', seen[1][0]['content'])
        self.assertEqual(seen[2], [])
        self.assertEqual(seen[4], [])
        self.assertIsNone(bot._REQUEST_STATE.get())

    def test_plain_followup_gets_history(self):
        state = {'history': [{'role': 'user', 'content': 'Compare golf clubs'}]}
        token = bot._REQUEST_STATE.set(state)
        try:
            with patch.object(bot, 'reason_with_context', return_value='Answer') as reason:
                bot.run_agent('Explain the second option')
            self.assertIn('Compare golf clubs', reason.call_args.kwargs['memory_context'])
        finally:
            bot._REQUEST_STATE.reset(token)

    def test_partial_failure_preserves_confirmed_save(self):
        def core(message):
            bot.save_memory('I prefer golf')
            raise RuntimeError('Email unconfirmed')
        with patch.object(bot, 'handle_message_core', side_effect=core), \
             patch.object(bot.requests, 'post', return_value=self.response([{'id': 7}])):
            result, _ = bot.handle_message('Save this and email me')
        self.assertFalse(result['success'])
        self.assertEqual(result['confirmed_actions'][0]['id'], 7)

if __name__ == '__main__':
    unittest.main()
