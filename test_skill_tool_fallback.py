import unittest
from unittest.mock import Mock, patch

import app_v2_9_1 as app291


class SkillToolFallbackTests(unittest.TestCase):
    def test_model_facing_context_does_not_expose_allowed_tools_label(self):
        with patch.object(app291, '_original_build_context', return_value=(
            'ACTIVE SKILL: Test\n'
            'PURPOSE: Test skill\n'
            'ALLOWED TOOLS: read_memory, research_web, reason\n'
            'TRAINING EXAMPLES:\n'
            'Example 1 input: hello\n'
            'Example 1 ideal output: hi'
        )):
            context = app291._text_only_context('test')
        self.assertNotIn('ALLOWED TOOLS:', context)
        self.assertIn('ACTIVE SKILL: Test', context)
        self.assertIn('Example 1 input: hello', context)

    def test_tool_use_failure_retries_once_with_fallback(self):
        with patch.object(
            app291,
            '_original_skill_complete',
            side_effect=RuntimeError('Tool choice is none, but model called a tool'),
        ) as primary, patch.object(
            app291,
            '_fallback_groq',
            return_value='fallback answer',
        ) as fallback:
            result = app291._skill_complete(
                [{'role': 'user', 'content': 'Fix it'}],
                tokens=500,
                temperature=0.1,
                json_mode=False,
            )
        self.assertEqual(result, 'fallback answer')
        self.assertEqual(primary.call_count, 1)
        self.assertEqual(fallback.call_count, 1)

    def test_non_tool_failure_is_not_retried(self):
        with patch.object(
            app291,
            '_original_skill_complete',
            side_effect=RuntimeError('rate limit exceeded'),
        ), patch.object(app291, '_fallback_groq') as fallback:
            with self.assertRaisesRegex(RuntimeError, 'rate limit'):
                app291._skill_complete(
                    [{'role': 'user', 'content': 'hello'}]
                )
            fallback.assert_not_called()

    def test_fallback_uses_text_only_system_instruction(self):
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {
            'choices': [
                {'message': {'content': 'plain text answer'}}
            ]
        }
        with patch.object(app291.v29.base, 'GROQ_API_KEY', 'test-key'), patch.object(
            app291.v29.base.requests,
            'post',
            return_value=response,
        ) as post:
            result = app291._fallback_groq(
                [{'role': 'user', 'content': 'Fix it'}],
                tokens=600,
            )
        self.assertEqual(result, 'plain text answer')
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['model'], app291.SKILL_FALLBACK_MODEL)
        self.assertIn('TEXT-ONLY MODE', payload['messages'][0]['content'])
        self.assertNotIn('tools', payload)


if __name__ == '__main__':
    unittest.main()
