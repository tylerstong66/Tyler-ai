import unittest
from unittest.mock import patch

import app_v2_10_1 as app2101


class ResilientGroundedChatTests(unittest.TestCase):
    def setUp(self):
        app2101.v210.DEPENDENCIES.reset()

    def test_tool_call_failure_uses_adaptive_text_fallback(self):
        with patch.object(
            app2101,
            '_PRIMARY_NORMAL_GROQ',
            side_effect=RuntimeError('Tool choice is none, but model called a tool'),
        ), patch.object(
            app2101,
            '_observed_text_fallback',
            return_value='fallback answer',
        ) as fallback:
            result = app2101.groq_resilient([
                {'role': 'user', 'content': 'hello'}
            ])
        self.assertEqual(result, 'fallback answer')
        fallback.assert_called_once()

    def test_non_tool_failure_is_not_retried(self):
        with patch.object(
            app2101,
            '_PRIMARY_NORMAL_GROQ',
            side_effect=RuntimeError('rate limit exceeded'),
        ), patch.object(app2101, '_observed_text_fallback') as fallback:
            with self.assertRaisesRegex(RuntimeError, 'rate limit'):
                app2101.groq_resilient([
                    {'role': 'user', 'content': 'hello'}
                ])
        fallback.assert_not_called()

    def test_email_flow_survives_tool_call_failure_and_dispatches_once(self):
        with patch.object(
            app2101,
            '_PRIMARY_NORMAL_GROQ',
            side_effect=RuntimeError('Tool choice is none, but model called a tool'),
        ), patch.object(
            app2101,
            '_observed_text_fallback',
            return_value='This is a Tyler AI dependency observability test.',
        ), patch.object(
            app2101.base,
            'send_email_via_n8n',
            return_value={'success': True, 'sent': True, 'message_id': 'msg-123'},
        ) as send_email:
            result = app2101.base.run_agent(
                'Email me a test message with the subject Tyler AI Health Test.'
            )
        self.assertIn('send_email', result['used_tools'])
        self.assertTrue(result['email_result']['sent'])
        send_email.assert_called_once()

    def test_tyler_implementation_question_gets_verified_source_context(self):
        captured = {}

        def fake_reason(message, memory_context='', research_context=''):
            captured['memory_context'] = memory_context
            return 'answer'

        with patch.object(
            app2101.v210.v297,
            '_developer_grounding',
            return_value='VERIFIED LOCAL SOURCE SNAPSHOT\napp_v2_10_1.py',
        ), patch.object(
            app2101,
            '_ORIGINAL_REASON_WITH_CONTEXT',
            side_effect=fake_reason,
        ):
            result = app2101.reason_with_context_grounded(
                'Review Tyler AI model fallback configuration.',
                memory_context='saved project context',
            )
        self.assertEqual(result, 'answer')
        self.assertIn('saved project context', captured['memory_context'])
        self.assertIn('VERIFIED RUNNING-SOURCE CONTEXT', captured['memory_context'])
        self.assertIn('VERIFIED LOCAL SOURCE SNAPSHOT', captured['memory_context'])

    def test_unrelated_question_does_not_load_source_context(self):
        captured = {}

        def fake_reason(message, memory_context='', research_context=''):
            captured['memory_context'] = memory_context
            return 'answer'

        with patch.object(
            app2101.v210.v297,
            '_developer_grounding',
        ) as grounding, patch.object(
            app2101,
            '_ORIGINAL_REASON_WITH_CONTEXT',
            side_effect=fake_reason,
        ):
            result = app2101.reason_with_context_grounded(
                'What should I make for dinner?',
                memory_context='normal memory',
            )
        self.assertEqual(result, 'answer')
        self.assertEqual(captured['memory_context'], 'normal memory')
        grounding.assert_not_called()


if __name__ == '__main__':
    unittest.main()
