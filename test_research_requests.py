import unittest
from unittest.mock import Mock, patch

import app
from dependency_observability import classify_error
from research_requests import search_query


LONG_REQUEST = (
    'NFL FULL-WEEK PARLAY — ADVANCED RESEARCH & PREDICTIVE ANALYSIS\n'
    'Act as an elite NFL analyst.\n'
    'Your mission is to research every NFL game scheduled for October 22–26, 2026, '
    'and construct three full-week parlays.\n'
    + ('Research injuries, EPA, FanDuel odds and touchdown usage. ' * 180)
    + '\nDo not fabricate simulations or current prices.'
)


class ResearchRequestTests(unittest.TestCase):
    def test_large_task_fits_real_search_api_and_keeps_scope(self):
        response = Mock(ok=True)
        response.json.return_value = {'answer': '', 'results': []}
        with patch.object(app, 'TAVILY_API_KEY', 'synthetic'), patch.object(
                app.requests, 'post', return_value=response) as post:
            app.tavily_search(LONG_REQUEST)
        query = post.call_args.kwargs['json']['query']
        self.assertLessEqual(len(query), 1500)
        self.assertIn('October 22–26, 2026', query)
        self.assertIn('NFL', query)
        self.assertIn('FanDuel', query)

    def test_short_queries_and_late_dates_are_preserved(self):
        self.assertEqual(search_query('NFL injury report October 22'), 'NFL injury report October 22')
        self.assertIn('2026-10-26', search_query('research weather ' * 200 + '2026-10-26'))
        self.assertLessEqual(len(search_query('界' * 6000)), 1500)

    def test_reasoning_receives_full_original_and_source_urls(self):
        source = {'title': 'Official schedule', 'url': 'https://www.nfl.com/schedules/', 'content': 'Schedule excerpt'}
        with patch.object(app, 'tavily_search', return_value={'answer': 'Limited evidence', 'sources': [source]}), \
                patch.object(app, 'feedback_context', return_value=''), \
                patch.object(app, 'groq', return_value='Supported partial analysis') as model:
            result = app.run_agent(LONG_REQUEST)
        content = model.call_args.args[0][1]['content']
        self.assertIn(LONG_REQUEST, content)
        self.assertIn(source['url'], content)
        self.assertIn('research_web', result['used_tools'])
        self.assertGreater(model.call_args.kwargs['tokens'], 1100)

    def test_research_failure_is_actionable_without_fabricated_picks_or_model_call(self):
        with patch.object(app, 'feedback_context', return_value=''), patch.object(app, 'groq') as model:
            result = app.reason_with_context(LONG_REQUEST, research_context='Live research failed: timeout')
        self.assertIn('timeout', result)
        self.assertIn('not verified', result)
        model.assert_not_called()

    def test_normal_chat_budget_and_provider_unchanged(self):
        with patch.object(app, 'feedback_context', return_value=''), patch.object(app, 'groq', return_value='hello') as model:
            self.assertEqual(app.reason_with_context('Hello'), 'hello')
        self.assertEqual(model.call_args.kwargs['tokens'], 1100)

    def test_1500_in_validation_error_is_not_a_500_outage(self):
        self.assertEqual(classify_error('Query is too long. Max query length is 1500 characters.'), 'invalid_request')


if __name__ == '__main__':
    unittest.main()
