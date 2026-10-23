import unittest
from unittest.mock import Mock, patch

import app
from dependency_observability import classify_error
from research_requests import search_query, search_queries


LONG_REQUEST = (
    'NFL FULL-WEEK PARLAY — ADVANCED RESEARCH & PREDICTIVE ANALYSIS\n'
    'Act as an elite NFL analyst.\n'
    'Your mission is to research every NFL game scheduled for October 22–26, 2026, '
    'and construct three full-week parlays.\n'
    + ('Research injuries, EPA, FanDuel odds and touchdown usage. ' * 180)
    + '\nDo not fabricate simulations or current prices.'
)


class ResearchRequestTests(unittest.TestCase):
    def test_nba_picks_tonight_reaches_research_and_three_evidence_queries(self):
        from research_requests import is_sports_research
        self.assertTrue(is_sports_research("NBA picks tonight"))
        self.assertTrue(app.needs_research("NBA picks tonight"))
        queries = search_queries("NBA picks tonight")
        self.assertEqual(len(queries), 3)
        self.assertIn("schedule", queries[0])
        self.assertIn("injury", queries[1])
        self.assertIn("FanDuel", queries[2])

    def test_sports_prediction_and_non_sports_routing(self):
        from research_requests import is_sports_research
        self.assertTrue(is_sports_research("NHL predictions"))
        self.assertTrue(app.needs_research("NFL winners"))
        self.assertFalse(is_sports_research("What are my personal goals?"))
        self.assertFalse(app.needs_research("What are my personal goals?"))

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
        self.assertIn('Missing search evidence does not establish', content)
        self.assertIn('Current server date and time (UTC)', model.call_args.args[0][0]['content'])
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

    def test_nfl_brief_retrieves_distinct_evidence_for_the_requested_dates(self):
        queries = search_queries(LONG_REQUEST)
        self.assertEqual(len(queries), 3)
        for query in queries:
            self.assertIn('October 22–26, 2026', query)
            self.assertLess(len(query), 400)
            self.assertNotIn('Act as', query)
        self.assertIn('schedule', queries[0])
        self.assertIn('FanDuel', queries[1])
        self.assertIn('injury', queries[2])

    def test_nba_recommendations_retrieve_distinct_evidence_for_explicit_date(self):
        request = ('Research tonight NBA games October 23, 2026 and return three '
                   'hypothetical recommendations with FanDuel odds and injuries')
        queries = search_queries(request)
        self.assertEqual(len(queries), 3)
        self.assertTrue(all('October 23, 2026' in query for query in queries))
        self.assertIn('official NBA schedule', queries[0])
        self.assertIn('injury report', queries[1])
        self.assertIn('FanDuel', queries[2])
        self.assertTrue(all(len(query) < 400 for query in queries))

    def test_nba_chat_uses_all_research_categories_without_fabricating_model_output(self):
        message = 'Research NBA games October 23, 2026 and suggest hypothetical picks'
        searches = [{'answer': 'Schedule evidence', 'sources': []},
                    {'answer': 'Injury evidence', 'sources': []},
                    {'answer': 'Odds not independently verified', 'sources': []}]
        with patch.object(app, 'tavily_search', side_effect=searches) as search, \\
                patch.object(app, 'reason_with_context', return_value='No verified model picks') as reason:
            result = app.run_agent(message)
        self.assertEqual(search.call_count, 3)
        context = reason.call_args.kwargs['research_context']
        for evidence in ('Schedule evidence', 'Injury evidence', 'Odds not independently verified'):
            self.assertIn(evidence, context)
        self.assertEqual(result['reply'], 'No verified model picks')

    def test_partial_retrieval_retains_successes_and_discloses_failure(self):
        results = [{'answer': 'Official schedule', 'sources': []},
                   RuntimeError('timeout'), {'answer': 'Limited injuries', 'sources': []}]
        with patch.object(app, 'tavily_search', side_effect=results), \
                patch.object(app, 'reason_with_context', return_value='partial') as reason:
            app.run_agent(LONG_REQUEST)
        context = reason.call_args.kwargs['research_context']
        self.assertIn('Official schedule', context)
        self.assertIn('Partial research failure: timeout', context)
        self.assertIn('retrieval time (UTC)', context)

    def test_1500_in_validation_error_is_not_a_500_outage(self):
        self.assertEqual(classify_error('Query is too long. Max query length is 1500 characters.'), 'invalid_request')


if __name__ == '__main__':
    unittest.main()
