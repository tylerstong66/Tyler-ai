import unittest
from unittest.mock import Mock, patch

import app_v2_9_6 as app296


class AdaptiveGroqFallbackTests(unittest.TestCase):
    def setUp(self):
        app296._MODEL_CACHE['ids'] = None
        app296._MODEL_CACHE['expires_at'] = 0
        app296._WORKING_FALLBACK_MODEL = None

    def test_discovery_filters_to_accessible_preferred_models(self):
        response = Mock()
        response.ok = True
        response.json.return_value = {
            'data': [
                {'id': 'openai/gpt-oss-20b'},
                {'id': 'openai/gpt-oss-120b'},
            ]
        }
        with patch.object(app296._base_module(), 'GROQ_API_KEY', 'test-key'), patch.object(
            app296.requests,
            'get',
            return_value=response,
        ):
            candidates = app296._candidate_models()
        self.assertIn('openai/gpt-oss-120b', candidates)
        self.assertIn('openai/gpt-oss-20b', candidates)
        self.assertNotIn('qwen/qwen3.6-27b', candidates)

    def test_unavailable_preview_model_is_skipped(self):
        model_list = Mock()
        model_list.ok = True
        model_list.json.return_value = {
            'data': [
                {'id': 'qwen/qwen3.6-27b'},
                {'id': 'openai/gpt-oss-20b'},
            ]
        }

        unavailable = Mock()
        unavailable.ok = False
        unavailable.status_code = 404
        unavailable.json.return_value = {
            'error': {'message': 'The model does not exist or you do not have access to it.'}
        }

        success = Mock()
        success.ok = True
        success.status_code = 200
        success.json.return_value = {
            'choices': [{'message': {'content': 'fallback worked'}}]
        }

        def post_side_effect(*args, **kwargs):
            model = kwargs['json']['model']
            if model == 'qwen/qwen3.6-27b':
                return unavailable
            return success

        with patch.object(app296._base_module(), 'GROQ_API_KEY', 'test-key'), patch.object(
            app296.requests,
            'get',
            return_value=model_list,
        ), patch.object(
            app296.requests,
            'post',
            side_effect=post_side_effect,
        ) as post:
            result = app296._adaptive_fallback_groq(
                [{'role': 'user', 'content': 'hello'}]
            )

        self.assertEqual(result, 'fallback worked')
        attempted = [call.kwargs['json']['model'] for call in post.call_args_list]
        self.assertIn('qwen/qwen3.6-27b', attempted)
        self.assertIn('openai/gpt-oss-20b', attempted)
        self.assertEqual(app296._WORKING_FALLBACK_MODEL, 'openai/gpt-oss-20b')

    def test_working_model_is_reused_first(self):
        app296._WORKING_FALLBACK_MODEL = 'openai/gpt-oss-120b'
        app296._MODEL_CACHE['ids'] = {'openai/gpt-oss-120b', 'openai/gpt-oss-20b'}
        app296._MODEL_CACHE['expires_at'] = 9999999999

        response = Mock()
        response.ok = True
        response.status_code = 200
        response.json.return_value = {
            'choices': [{'message': {'content': 'ok'}}]
        }
        with patch.object(app296._base_module(), 'GROQ_API_KEY', 'test-key'), patch.object(
            app296.requests,
            'post',
            return_value=response,
        ) as post:
            result = app296._adaptive_fallback_groq(
                [{'role': 'user', 'content': 'hello'}]
            )
        self.assertEqual(result, 'ok')
        self.assertEqual(post.call_args.kwargs['json']['model'], 'openai/gpt-oss-120b')

    def test_tool_call_failure_moves_to_next_model(self):
        app296._MODEL_CACHE['ids'] = {'openai/gpt-oss-120b', 'openai/gpt-oss-20b'}
        app296._MODEL_CACHE['expires_at'] = 9999999999

        tool_failure = Mock()
        tool_failure.ok = False
        tool_failure.status_code = 400
        tool_failure.json.return_value = {
            'error': {'message': 'Tool choice is none, but model called a tool'}
        }

        success = Mock()
        success.ok = True
        success.status_code = 200
        success.json.return_value = {
            'choices': [{'message': {'content': 'plain answer'}}]
        }

        with patch.object(app296._base_module(), 'GROQ_API_KEY', 'test-key'), patch.object(
            app296.requests,
            'post',
            side_effect=[tool_failure, success],
        ):
            result = app296._adaptive_fallback_groq(
                [{'role': 'user', 'content': 'hello'}]
            )
        self.assertEqual(result, 'plain answer')

    def test_model_discovery_failure_does_not_block_fallback(self):
        discovery = Mock()
        discovery.ok = False
        discovery.status_code = 500

        success = Mock()
        success.ok = True
        success.status_code = 200
        success.json.return_value = {
            'choices': [{'message': {'content': 'still works'}}]
        }
        with patch.object(app296._base_module(), 'GROQ_API_KEY', 'test-key'), patch.object(
            app296.requests,
            'get',
            return_value=discovery,
        ), patch.object(
            app296.requests,
            'post',
            return_value=success,
        ):
            result = app296._adaptive_fallback_groq(
                [{'role': 'user', 'content': 'hello'}]
            )
        self.assertEqual(result, 'still works')


if __name__ == '__main__':
    unittest.main()
