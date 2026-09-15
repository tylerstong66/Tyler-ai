import unittest

import app_v2_9_3 as app293


class EvaluatorScoreNormalizationTests(unittest.TestCase):
    def test_explicit_ten_out_of_ten_becomes_100(self):
        score, meta = app293.normalize_evaluator_score({
            'score': '10/10',
            'passed': True,
            'weaknesses': [],
            'improvement': 'None needed.',
        })
        self.assertEqual(score, 100)
        self.assertIn('explicit-10-point-scale', meta['normalized_from'])

    def test_declared_ten_point_scale_becomes_90(self):
        score, meta = app293.normalize_evaluator_score({
            'score': 9,
            'score_scale': 10,
            'passed': True,
            'weaknesses': [],
            'improvement': '',
        })
        self.assertEqual(score, 90)
        self.assertEqual(meta['normalized_from'], 'declared-10-point-scale')

    def test_hidden_perfect_ten_is_inferred_as_100(self):
        score, meta = app293.normalize_evaluator_score({
            'score': 10,
            'passed': True,
            'strengths': ['Fully satisfies criteria'],
            'weaknesses': ['None recorded'],
            'improvement': 'None needed. The response fully satisfies the evaluation criteria.',
        })
        self.assertEqual(score, 100)
        self.assertEqual(meta['normalized_from'], 'inferred-10-point-scale')

    def test_genuine_ten_out_of_100_is_not_inflated(self):
        score, meta = app293.normalize_evaluator_score({
            'score': 10,
            'passed': False,
            'weaknesses': ['Incorrect architecture'],
            'improvement': 'Use the actual system.',
        })
        self.assertEqual(score, 10)
        self.assertEqual(meta['normalized_from'], '0-100')

    def test_score_100_field_is_used_directly(self):
        score, meta = app293.normalize_evaluator_score({
            'score_100': 96,
            'score_scale': 100,
            'passed': True,
            'weaknesses': [],
            'improvement': '',
        })
        self.assertEqual(score, 96)
        self.assertEqual(meta['normalized_from'], '0-100')


if __name__ == '__main__':
    unittest.main()
