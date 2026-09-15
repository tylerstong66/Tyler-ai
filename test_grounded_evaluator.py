import json
import unittest
from unittest.mock import patch

import app_v2_9_2 as app292


SKILL = {
    'skill_id': 'tyler-ai-developer',
    'name': 'Tyler AI Developer',
    'purpose': 'Develop and debug Tyler AI safely.',
    'version': 1,
    'success_criteria': ['Accurate', 'Safe', 'Specific'],
}

EXAMPLES = [
    {
        'input': 'Email sending fails with an unauthorized error.',
        'ideal_output': (
            'Inspect send_email_via_n8n(), N8N_WEBHOOK_KEY, and N8N_AUTH_HEADER. '
            'Check n8n execution history before retrying an unknown-outcome email.'
        ),
    }
]


class GroundedEvaluatorTests(unittest.TestCase):
    def evaluator_json(self, score=94):
        return json.dumps({
            'score': score,
            'passed': score >= 80,
            'strengths': ['Grounded in the Tyler AI architecture'],
            'weaknesses': [],
            'improvement': '',
        })

    def run_eval(self, candidate, evaluator_score=94):
        saved = {}

        def save(category, payload, importance=5):
            saved['category'] = category
            saved['payload'] = payload
            saved['importance'] = importance
            return payload

        with patch.object(app292.v291.ENGINE, 'get_skill', return_value=SKILL), \
             patch.object(app292.v291.ENGINE, 'run_skill', return_value=candidate), \
             patch.object(app292.v291.ENGINE, 'examples_for_skill', return_value=EXAMPLES), \
             patch.object(app292.v291.ENGINE, 'complete', return_value=self.evaluator_json(evaluator_score)) as complete, \
             patch.object(app292.v291.ENGINE, '_save', side_effect=save):
            result = app292._grounded_evaluate_skill(
                'Tyler AI Developer',
                'Email sending fails with an unauthorized error. Fix it.',
            )
        return result, saved, complete

    def test_evaluator_is_grounded_in_examples_and_project_invariants(self):
        candidate = (
            'Inspect send_email_via_n8n and compare N8N_AUTH_HEADER and '
            'N8N_WEBHOOK_KEY with n8n. Check the n8n execution before retrying.'
        )
        result, saved, complete = self.run_eval(candidate)
        self.assertTrue(result['grounded_evaluation'])
        self.assertEqual(result['reference_example_count'], 1)
        self.assertEqual(saved['category'], 'skill_score')

        evaluator_request = json.loads(complete.call_args.args[0][1]['content'])
        invariants = ' '.join(evaluator_request['authoritative_project_invariants'])
        self.assertIn('Supabase is not the email transport', invariants)
        self.assertIn('must not be retried automatically', invariants)
        self.assertEqual(len(evaluator_request['authoritative_training_examples']), 1)
        rules = ' '.join(evaluator_request['evaluation_rules'])
        self.assertIn('Do not invent additional systems', rules)
        self.assertIn('unrelated to the user test request', rules)

    def test_safe_specific_email_answer_can_pass_in_nineties(self):
        candidate = (
            'Inspect send_email_via_n8n(). Verify N8N_WEBHOOK_URL, '
            'N8N_WEBHOOK_KEY, and N8N_AUTH_HEADER match the n8n webhook. '
            'Inspect n8n execution history and verify the outcome before retrying. '
            'Do not retry automatically when the email outcome may be unknown.'
        )
        result, _, _ = self.run_eval(candidate, evaluator_score=94)
        self.assertEqual(result['score'], 94)
        self.assertTrue(result['passed'])
        self.assertTrue(all(result['architecture_checks'].values()))

    def test_invented_supabase_email_path_caps_score_and_fails(self):
        candidate = (
            'Check the Supabase email table and send email through Supabase, then '
            'inspect n8n. Verify N8N_WEBHOOK_KEY and N8N_AUTH_HEADER.'
        )
        result, _, _ = self.run_eval(candidate, evaluator_score=98)
        self.assertEqual(result['score'], 60)
        self.assertFalse(result['passed'])
        self.assertFalse(result['architecture_checks']['avoids_invented_supabase_email_path'])

    def test_unsafe_automatic_retry_caps_score_and_fails(self):
        candidate = (
            'Inspect send_email_via_n8n and N8N_WEBHOOK_KEY, then automatically '
            'retry the email several times after any timeout.'
        )
        result, _, _ = self.run_eval(candidate, evaluator_score=97)
        self.assertEqual(result['score'], 65)
        self.assertFalse(result['passed'])
        self.assertFalse(result['architecture_checks']['avoids_unsafe_automatic_retry'])

    def test_missing_actual_email_path_caps_score(self):
        candidate = 'Check the server configuration and review authentication settings.'
        result, _, _ = self.run_eval(candidate, evaluator_score=96)
        self.assertEqual(result['score'], 78)
        self.assertFalse(result['architecture_checks']['mentions_actual_email_path'])


if __name__ == '__main__':
    unittest.main()
