import json
import unittest
from unittest.mock import patch

import app_v2_9_4 as app294


SKILL = {
    'skill_id': 'tyler-ai-developer',
    'name': 'Tyler AI Developer',
    'purpose': 'Develop and debug Tyler AI safely.',
    'version': 1,
    'success_criteria': ['Accurate', 'Safe', 'Specific'],
}

EXAMPLES = [
    {
        'input': 'Deploy a Tyler AI update safely.',
        'ideal_output': 'Verify GitHub, Render start command, deployment status, and rollback path.',
    }
]


class AuditableEvaluatorTests(unittest.TestCase):
    def run_eval(self, candidate, evaluator_payload):
        saved = {}

        def save(category, payload, importance=5):
            saved['category'] = category
            saved['payload'] = payload
            return payload

        with patch.object(app294.v293.v292.v291.ENGINE, 'get_skill', return_value=SKILL), \
             patch.object(app294.v293.v292.v291.ENGINE, 'run_skill', return_value=candidate), \
             patch.object(app294.v293.v292.v291.ENGINE, 'examples_for_skill', return_value=EXAMPLES), \
             patch.object(app294.v293.v292.v291.ENGINE, 'complete', return_value=json.dumps(evaluator_payload)), \
             patch.object(app294.v293.v292.v291.ENGINE, '_save', side_effect=save):
            result = app294._evaluate_skill_v294(
                'Tyler AI Developer',
                'A new GitHub update is not live on Render. Diagnose it safely.',
            )
        return result, saved

    def test_no_deductions_means_100_and_pass(self):
        candidate = (
            'Verify the GitHub commit, Render branch, start command, deployment logs, '
            'and live version. Keep the old start command ready for rollback.'
        )
        result, _ = self.run_eval(candidate, {
            'deductions': [],
            'strengths': ['Grounded and reversible'],
            'improvement': '',
        })
        self.assertEqual(result['score'], 100)
        self.assertTrue(result['passed'])
        self.assertEqual(result['weaknesses'], [])
        self.assertEqual(result['deduction_total'], 0)

    def test_deductions_are_calculated_not_trusted_from_model(self):
        candidate = 'Check GitHub and Render.'
        result, _ = self.run_eval(candidate, {
            'score': 12,
            'deductions': [
                {
                    'dimension': 'specificity_actionability',
                    'points': 12,
                    'reason': 'Does not explain what to inspect in Render.',
                },
                {
                    'dimension': 'completeness',
                    'points': 8,
                    'reason': 'Does not mention rollback or version verification.',
                },
            ],
            'strengths': ['Relevant'],
            'improvement': 'Add concrete Render checks and rollback verification.',
        })
        self.assertEqual(result['score'], 80)
        self.assertTrue(result['passed'])
        self.assertEqual(result['deduction_total'], 20)
        self.assertEqual(len(result['weaknesses']), 2)

    def test_invalid_deductions_are_ignored(self):
        candidate = 'Check GitHub and Render.'
        result, _ = self.run_eval(candidate, {
            'deductions': [
                {'dimension': 'made_up_dimension', 'points': 50, 'reason': 'Invalid'},
                {'dimension': 'completeness', 'points': 10, 'reason': ''},
                {'dimension': 'task_relevance', 'points': -5, 'reason': 'Invalid points'},
            ],
            'strengths': ['Relevant'],
            'improvement': '',
        })
        self.assertEqual(result['score'], 100)
        self.assertEqual(result['deduction_total'], 0)

    def test_per_item_deduction_is_capped(self):
        candidate = 'Check GitHub and Render.'
        result, _ = self.run_eval(candidate, {
            'deductions': [
                {
                    'dimension': 'completeness',
                    'points': 99,
                    'reason': 'Missing multiple required deployment checks.',
                },
            ],
            'strengths': [],
            'improvement': 'Add the missing checks.',
        })
        self.assertEqual(result['score'], 75)
        self.assertFalse(result['passed'])
        self.assertEqual(result['deduction_total'], 25)

    def test_email_safety_cap_still_overrides_evaluator(self):
        candidate = (
            'Use send_email_via_n8n with N8N_WEBHOOK_KEY, then automatically retry '
            'the email after any timeout without checking whether Gmail sent it.'
        )
        with patch.object(
            app294.v293.v292,
            '_architecture_checks',
            return_value={
                'mentions_actual_email_path': True,
                'mentions_auth_configuration': True,
                'avoids_invented_supabase_email_path': True,
                'avoids_unsafe_automatic_retry': False,
            },
        ):
            result, _ = self.run_eval(candidate, {
                'deductions': [],
                'strengths': ['Specific'],
                'improvement': '',
            })
        self.assertEqual(result['score'], 65)
        self.assertFalse(result['passed'])
        self.assertTrue(any('unsafe_automatic_retry' in item for item in result['weaknesses']))


if __name__ == '__main__':
    unittest.main()
