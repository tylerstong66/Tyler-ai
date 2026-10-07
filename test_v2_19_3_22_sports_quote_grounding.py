import json
import types
import unittest

import app_v2_19_3_22 as v
from sports_answer_audit import _variance_erases_expectation, audit_answer
from skill_lab import SkillPromotionLab
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class QuoteGroundingTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._context = types.MethodType(v.harness.previous._sports_context, self.lab)
        self.lab._run = types.MethodType(v.coverage_module._run, self.lab)
        self.lab._judge = types.MethodType(v.previous.previous.previous._judge, self.lab)

    def response(self, rationale, uncertainty="Inputs and probabilities are unverified.", decision="NO BET"):
        return json.dumps(dict(decision=decision, rationale=rationale, uncertainty=uncertainty))

    def test_negated_implying_is_not_an_assertion_but_later_assertions_still_fail(self):
        for prose in ("Never implying that variance or the vig erases an edge.",
                      "Not implying that volatility cancels expected profit.",
                      "Never suggesting that variance overwhelms the apparent edge."):
            with self.subTest(prose=prose):
                self.assertFalse(_variance_erases_expectation(prose))
        for prose in ("Variance overwhelms the apparent edge.",
                      "Never implying that variance erases an edge. Volatility erodes EV.",
                      "Never skip checking prices; variance erases positive EV."):
            with self.subTest(prose=prose):
                self.assertTrue(_variance_erases_expectation(prose))

    def test_unknown_estimate_does_not_license_variance_erases_edge(self):
        self.engine.complete = lambda *a, **kw: self.response("Variance overwhelms any apparent edge.")
        output = self.lab._run(self.profile, "Evaluate this unavailable quote.")
        _, errors = audit_answer(output, input_text="Evaluate this unavailable quote.")
        self.assertIn("explanation_confuses_variance_with_expectation", errors)

    def test_other_positive_price_with_negated_warning_reaches_semantic_judge(self):
        request = "Synthetic exercise: +185 odds, win probability 0.43, no pushes."
        self.engine.complete = lambda *a, **kw: self.response(
            "The supplied estimate gives positive expected profit at the offered price.",
            "Unverified estimates justify withholding a bet, never implying that variance or vig erases an edge.")
        output = self.lab._run(self.profile, request)
        _, errors = audit_answer(output, input_text=request)
        self.assertEqual(errors, [])
        calls = []
        self.engine.complete = lambda *a, **kw: calls.append(a) or "COMPLETE=PASS\nMATH=PASS\nFACTS=PASS\nTASK=PASS\nSCORE=100\nWEAKNESSES=none"
        result = self.lab._judge(self.profile, {"case_id":"other-positive-price", "input":request, "expected_behavior":"Correct arithmetic and uncertainty."}, output)
        self.assertTrue(result["passed"])
        self.assertEqual(len(calls), 1)

    def test_equivalent_causal_language_and_volume_direction_are_required(self):
        for prose in ("Since the offense is trailing, passing attempts may increase.",
                      "A scenario where low opponent scoring supports protecting a lead by running more, reducing passing volume.",
                      "When ahead, passing opportunities may fall."):
            with self.subTest(prose=prose):
                self.assertTrue(v.causal_direction(prose))
        for prose in ("Leading and trailing changes volume.",
                      "Discuss how game script affects passing.",
                      "When leading, confidence increases.",
                      "When leading, review the passing volume. Odds are more attractive."):
            with self.subTest(prose=prose):
                self.assertFalse(v.causal_direction(prose))

    def test_causal_presence_does_not_skip_semantic_judging(self):
        request = "Parlay QB passing over, receiver receiving over and opponent scoring under."
        prose = "Joint probability is unknown; QB passing and receiver receiving can be positively correlated. Since trailing, passing opportunities may increase while opponent scoring under becomes less likely."
        self.engine.complete = lambda *a, **kw: self.response(prose)
        output = self.lab._run(self.profile, request)
        calls = []
        self.engine.complete = lambda *a, **kw: calls.append(a) or "COMPLETE=PASS\nMATH=PASS\nFACTS=FAIL\nTASK=PASS\nSCORE=100\nWEAKNESSES=Unsupported empirical correlation strength"
        result = self.lab._judge(self.profile, {"case_id":"other-parlay", "input":request, "expected_behavior":"Explain conditional dependence without inventing strength."}, output)
        self.assertEqual(len(calls), 1)
        self.assertFalse(result["passed"])
        self.assertLess(result["score"], 80)

    def test_consensus_negations_and_uncertainty_are_not_unsupported_assertions(self):
        for prose in ("A single quote does not establish market consensus.",
                      "This cannot confirm betting consensus.",
                      "We do not know whether it reflects market consensus.",
                      "Without independent quotes, consensus remains unknown."):
            with self.subTest(prose=prose):
                self.assertFalse(v.unsupported_consensus(prose))
        for prose in ("The new price reflects altered market consensus.",
                      "It confirms bookmaker consensus. Inputs remain unverified.",
                      "It does not establish market consensus; however the movement reflects new market consensus."):
            with self.subTest(prose=prose):
                self.assertTrue(v.unsupported_consensus(prose))

    def test_new_quote_case_rejected_and_retained_without_semantic_call(self):
        request = json.dumps({"previous_odds":-115,"odds":-135,"previous_line":41.5,"line":44.5})
        prose = "The price change reflects altered market consensus; re-evaluate the new number."
        self.engine.complete = lambda *a, **kw: self.response(prose, decision="RE-EVALUATE")
        output = self.lab._run(self.profile, request)
        self.engine.complete = lambda *a, **kw: self.fail("Unsupported consensus cannot reach judging")
        result = self.lab._judge(self.profile, {"case_id":"other-changed-quote", "input":request, "expected_behavior":"Reassess without invented market consensus."}, output)
        self.assertEqual(result["score"], 0)
        self.assertIn("explanation_quote_change_does_not_establish_market_consensus", result["weaknesses"])
        self.assertEqual(result["output"], output)

    def test_live_quote_failure_stays_closed(self):
        request = "Earlier Over 41.5 at -115. It is now Over 44.5 at -135."
        self.engine.complete = lambda *a, **kw: self.response("The change shows market consensus.", decision="RE-EVALUATE")
        token = v.math_module._LIVE_INPUT.set(True)
        try:
            with self.assertRaisesRegex(RuntimeError, "consensus"):
                self.lab._run(self.profile, request)
        finally:
            v.math_module._LIVE_INPUT.reset(token)

    def test_quote_background_scope_identity_and_activation(self):
        self.assertEqual(v.background("Ordinary unknown odds.", {}), [])
        lines = v.background("The quote changed.", {"metrics":{"previous_implied_probability":.5}})
        self.assertTrue(any("new number" in x for x in lines))
        validator = SportsValidation(self.lab, self.store.get_rows, self.store.save_row, "gemini", "fixture", lambda:"now")
        self.assertEqual(validator.identity()[2]["harness_version"], v.HARNESS_VERSION)
        with v.app.app_context():
            status = v.status().get_json()
        self.assertFalse(status["automatic_skill_activation_enabled"])
        self.assertFalse(status["sports_profitability_proven"])


if __name__ == "__main__":
    unittest.main()
