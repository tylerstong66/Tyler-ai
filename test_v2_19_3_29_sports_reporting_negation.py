import unittest

import app_v2_19_3_29 as v
from sports_answer_audit import _variance_erases_expectation


class ReportingNegationTests(unittest.TestCase):
    def test_bounded_reporting_denials(self):
        for prefix in ('without implying', 'without claiming', 'rather than suggesting', 'instead of asserting', 'not saying'):
            with self.subTest(prefix=prefix):
                self.assertFalse(_variance_erases_expectation(prefix+' that outcome variance or juice erases expected value.'))

    def test_later_affirmative_and_unrelated_negation_still_fail(self):
        self.assertTrue(_variance_erases_expectation('Without implying that variance erases EV, volatility cancels expected profit.'))
        self.assertTrue(_variance_erases_expectation('Without inputs, variance erases expected profit.'))
        self.assertTrue(_variance_erases_expectation('Instead of a wager, variance erodes expected value.'))

    def test_identity_and_manual_gate(self):
        self.assertEqual(v.sports_validation.HARNESS_VERSION, 'sports-validation-v19-reporting-negation')
        with v.app.app_context():
            status=v.status().get_json()
        self.assertFalse(status['automatic_skill_activation_enabled'])
        self.assertFalse(status['sports_profitability_proven'])


if __name__ == '__main__':
    unittest.main()
