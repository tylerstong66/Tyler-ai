import json
import types
import unittest

import app_v2_19_3_23 as v
from skill_lab import SkillPromotionLab
from sports_answer_audit import _variance_erases_expectation, audit_answer
from sports_explanation_checks import missing
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class InputIsolationTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._context = types.MethodType(v.harness.previous._sports_context, self.lab)
        self.lab._run = types.MethodType(v.previous.coverage_module._run, self.lab)
        self.lab._judge = types.MethodType(v.previous.previous.previous.previous._judge, self.lab)

    def test_contrasts_and_local_negation_are_not_affirmative_claims(self):
        for prose in ("Variance affects risk rather than erasing expected value.",
                      "Volatility changes risk instead of eroding an edge.",
                      "Variance alters risk without negating expected profit.",
                      "Variance does not materially reduce risk but never erases EV.",
                      "Variance is not erasing the estimated edge."):
            with self.subTest(prose=prose):
                self.assertFalse(_variance_erases_expectation(prose))

    def test_one_negated_claim_cannot_hide_another_error(self):
        for prose in ("Variance does not erase EV, but volatility cancels expected profit.",
                      "Variance affects risk rather than erasing an edge, although variance overwhelms EV.",
                      "Variance does not affect the mean but erases the edge.",
                      "Never implying that variance erases EV; volatility erodes the edge."):
            with self.subTest(prose=prose):
                self.assertTrue(_variance_erases_expectation(prose))

    def test_expected_return_and_value_are_equivalent_topics_not_proof(self):
        for noun in ("return", "value", "net profit"):
            answer = {"rationale":"The supplied estimate gives positive expected " + noun + " at the offered price.",
                      "uncertainty":"The probability is unverified.","metrics":{"expected_profit_per_unit":.1}}
            self.assertEqual(missing("Check this supplied probability.", answer), [])
        answer["rationale"] = "The offered price is interesting."
        self.assertIn("explanation_missing_positive_ev_meaning", missing("Check this supplied probability.", answer))

    def test_unknown_quote_contrast_reaches_coverage_which_still_rejects_echo(self):
        request = "Parlay QB passing over, receiver receiving over and opponent scoring under."
        prose = "A joint probability model is needed; QB passing and receiver receiving are positively correlated; opponent scoring depends on script; leading or trailing changes volume."
        self.engine.complete = lambda *a, **kw: json.dumps({"decision":"NO BET","rationale":prose,"uncertainty":"Variance affects risk rather than erasing an edge; probabilities are unavailable."})
        output = self.lab._run(self.profile, request)
        self.assertEqual(audit_answer(output, input_text=request)[1], [])
        self.engine.complete = lambda *a, **kw: self.fail("Checklist echo must still fail before judging")
        result = self.lab._judge(self.profile,{"case_id":"other-echo","input":request,"expected_behavior":"Directional conditional mechanism"},output)
        self.assertEqual(result["score"], 0)
        self.assertIn("explanation_missing_directional_conditional_mechanism",result["weaknesses"])

    def test_quote_change_guidance_is_scoped_and_prompt_instructions_are_not_facts(self):
        prompts = []
        self.engine.complete = lambda messages, **kw: prompts.append(messages[0]["content"]) or json.dumps({"decision":"NO BET","rationale":"No verified inputs.","uncertainty":"Inputs are unavailable."})
        self.lab._run(self.profile,"A running back has a winning streak.")
        self.assertIn("do not describe evidence or a change that was not supplied", prompts[-1])
        self.assertNotIn("This supplies a bookmaker quote change", prompts[-1])
        self.engine.complete = lambda messages, **kw: prompts.append(messages[0]["content"]) or json.dumps({"decision":"RE-EVALUATE","rationale":"Reassess the new number and price.","uncertainty":"No independent quotes."})
        self.lab._run(self.profile,json.dumps({"previous_odds":-115,"odds":-135}))
        self.assertIn("This supplies a bookmaker quote change", prompts[-1])

    def test_semantic_fact_failure_still_overrides_a_perfect_score(self):
        request = "Evaluate a streak without any quote supplied."
        self.engine.complete = lambda *a, **kw: json.dumps({"decision":"NO BET","rationale":"The line moved.","uncertainty":"Probability is unavailable."})
        output = self.lab._run(self.profile,request)
        prompts=[]
        self.engine.complete = lambda messages, **kw: prompts.append(messages[1]["content"]) or "COMPLETE=PASS\nMATH=PASS\nFACTS=FAIL\nTASK=PASS\nSCORE=100\nWEAKNESSES=Invented quote change"
        result = self.lab._judge(self.profile,{"case_id":"other-unquoted-input","input":request,"expected_behavior":"No invented observations"},output)
        self.assertIn("literal INPUT",prompts[0])
        self.assertFalse(result["passed"])
        self.assertLess(result["score"],80)

    def test_validation_identity_and_protected_active_profile(self):
        validator=SportsValidation(self.lab,self.store.get_rows,self.store.save_row,"gemini","fixture",lambda:"now")
        self.assertEqual(validator.identity()[2]["harness_version"],v.HARNESS_VERSION)
        self.assertEqual(self.engine.get_skill("Sports Betting Analyst")["version"],1)
        with v.app.app_context():
            self.assertFalse(v.status().get_json()["automatic_skill_activation_enabled"])


if __name__ == "__main__":
    unittest.main()
