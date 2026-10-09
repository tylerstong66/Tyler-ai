import unittest

import app_v2_19_3_27 as v
from sports_answer_audit import _variance_erases_expectation


class NegationScopeTests(unittest.TestCase):
    def test_observed_denial_is_not_an_affirmative_error(self):
        self.assertFalse(_variance_erases_expectation(
            "This conditional sensitivity justifies withholding a wager despite positive expected value, never because outcome variance or vig erases expected profit."))
        self.assertFalse(_variance_erases_expectation(
            "Pass, never because volatility erodes expected value."))

    def test_negation_does_not_hide_a_later_affirmative_error(self):
        self.assertTrue(_variance_erases_expectation(
            "Never because outcome variance erases expected profit, but volatility cancels expected value."))
        self.assertTrue(_variance_erases_expectation(
            "Never because outcome variance erases EV. Outcome variance erases expected profit."))
        self.assertTrue(_variance_erases_expectation(
            "Never accept missing inputs because outcome variance erases expected profit."))

    def test_fresh_identity_keeps_the_manual_gate(self):
        self.assertEqual(v.sports_validation.HARNESS_VERSION, 'sports-validation-v17-negation-scope')
        with v.app.app_context():
            status = v.status().get_json()
        self.assertEqual(status['version_short'], 'v2.19.3.27')
        self.assertFalse(status['automatic_skill_activation_enabled'])
        self.assertFalse(status['sports_profitability_proven'])


if __name__ == '__main__':
    unittest.main()
