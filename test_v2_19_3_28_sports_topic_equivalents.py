import unittest

import app_v2_19_3_28 as v
from sports_explanation_checks import missing


class TopicEquivalentTests(unittest.TestCase):
    def test_shared_opportunity_covers_the_connection(self):
        request = 'Build a parlay with QB passing and receiver yards.'
        prose = 'A joint model is required: quarterback passing volume and receiver receiving yards share opportunity. Protecting a lead can reduce both; opponent under depends on game script.'
        self.assertEqual(missing(request, {'rationale': prose}), [])

    def test_disconnected_mentions_still_miss_the_connection(self):
        request = 'Build a parlay with QB passing and receiver yards.'
        prose = 'Quarterback and receiver inputs are unknown. A joint model is required. A lead changes game script and opponent under probability.'
        self.assertIn('explanation_missing_qb_receiver_connection', missing(request, {'rationale': prose}))

    def test_payout_rejection_equivalent_keeps_semantic_review_required(self):
        request = 'Add a weak leg to a parlay for a target payout.'
        prose = 'Adding a leg solely to reach a target payout violates requirements for standalone value. A joint model is required.'
        self.assertEqual(missing(request, {'rationale': prose}), [])
        incomplete = 'The target payout is attractive. Each leg requires standalone value and a joint model.'
        self.assertIn('explanation_missing_keep_or_pass', missing(request, {'rationale': incomplete}))

    def test_identity_and_manual_gate(self):
        self.assertEqual(v.sports_validation.HARNESS_VERSION, 'sports-validation-v18-topic-equivalents')
        with v.app.app_context():
            status = v.status().get_json()
        self.assertFalse(status['automatic_skill_activation_enabled'])
        self.assertFalse(status['sports_profitability_proven'])


if __name__ == '__main__':
    unittest.main()
