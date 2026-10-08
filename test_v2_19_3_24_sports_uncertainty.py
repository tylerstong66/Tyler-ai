import json
import types
import unittest

import app_v2_19_3_24 as v
from skill_lab import SkillPromotionLab
from sports_answer_audit import _variance_erases_expectation, audit_answer
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class EvidenceUncertaintyTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._context = types.MethodType(v.harness.previous._sports_context, self.lab)
        self.lab._run = types.MethodType(v.coverage_module._run, self.lab)
        self.lab._judge = types.MethodType(v.coverage_module._judge, self.lab)

    def test_denial_of_a_claim_is_not_an_assertion(self):
        for prefix in ("rather than a claim that", "instead of the claim that", "not a claim that", "without a claim that"):
            with self.subTest(prefix=prefix):
                self.assertFalse(_variance_erases_expectation(prefix + " variance or vig erases expected value."))
                self.assertTrue(_variance_erases_expectation(prefix + " variance erases EV, but volatility cancels expected profit."))

    def test_positive_ev_with_denial_reaches_semantic_review(self):
        request = "Synthetic +185 odds, estimated probability 0.43, no pushes."
        self.engine.complete = lambda *a, **kw: json.dumps({"decision":"NO BET", "rationale":"The supplied estimate gives positive expected profit at the offered price.", "uncertainty":"Missing evidence justifies caution rather than a claim that variance or vig erases expected value."})
        output = self.lab._run(self.profile, request)
        self.assertEqual(audit_answer(output, input_text=request)[1], [])
        calls=[]
        self.engine.complete = lambda *a, **kw: calls.append(a) or "COMPLETE=PASS\nMATH=PASS\nFACTS=PASS\nTASK=PASS\nSCORE=100\nWEAKNESSES=none"
        self.assertTrue(self.lab._judge(self.profile, {"case_id":"other-denial", "input":request,"expected_behavior":"Point EV with uncertainty."}, output)["passed"])
        self.assertEqual(len(calls), 1)

    def test_lead_synonym_reaches_semantic_review_and_strength_still_fails(self):
        request = "Parlay QB passing over, receiver receiving over and opponent scoring under."
        self.engine.complete = lambda *a, **kw: json.dumps({"decision":"NO BET", "rationale":"Joint ticket probability is unknown; QB passing and receiver receiving are positively correlated through shared opportunity. If low opponent scoring supports protecting a lead by running more, passing volume may decrease; opponent-under differs from game-total-under.", "uncertainty":"That does not establish a correlation magnitude or a joint probability."})
        output = self.lab._run(self.profile, request)
        self.assertEqual(v.coverage_module.missing(request, json.loads(output)), [])
        prompts=[]
        self.engine.complete = lambda messages, **kw: prompts.append(messages[1]["content"]) or "COMPLETE=PASS\nMATH=PASS\nFACTS=FAIL\nTASK=PASS\nSCORE=100\nWEAKNESSES=Unsupported strength"
        result = self.lab._judge(self.profile,{"case_id":"other-lead","input":request,"expected_behavior":"Conditional dependence without invented strength."},output)
        self.assertLess(result["score"],80)
        self.assertFalse(result["passed"])
        self.assertIn("conditional magnitude", prompts[0])

    def test_lead_keyword_without_a_directional_mechanism_still_fails(self):
        request = "Parlay QB passing over, receiver receiving over and opponent scoring under."
        answer={"rationale":"Joint probability is unknown; QB and receiver are positively correlated; opponent scoring affects the lead.","uncertainty":"Inputs unknown.","metrics":{}}
        self.assertIn("explanation_missing_directional_conditional_mechanism", v.coverage_module.missing(request,answer))

    def test_final_task_policy_follows_profile_and_does_not_include_expected_answer(self):
        prompts=[]
        self.engine.complete = lambda messages, **kw: prompts.append(messages[0]["content"]) or json.dumps({"decision":"NO BET","rationale":"Current information is needed.","uncertainty":"Availability is unverified."})
        self.lab._context = lambda profile: "PROFILE_SENTINEL"
        self.lab._run(self.profile, "An old availability report is all we have.")
        self.assertGreater(prompts[0].index("Apply the full skill profile as policy"),prompts[0].index("PROFILE_SENTINEL"))
        self.assertIn("do not establish increased or extreme outcome variance",prompts[0])
        self.assertNotIn("EXPECTED", prompts[0])

    def test_stale_evidence_semantic_failure_cannot_receive_passing_score(self):
        request = "Use an old injury report without current data."
        self.engine.complete = lambda *a, **kw: json.dumps({"decision":"NO BET","rationale":"Current inputs are missing.","uncertainty":"Stale evidence creates extreme variance."})
        output=self.lab._run(self.profile,request)
        prompts=[]
        self.engine.complete=lambda messages, **kw: prompts.append(messages[1]["content"]) or "COMPLETE=PASS\nMATH=PASS\nFACTS=FAIL\nTASK=PASS\nSCORE=100\nWEAKNESSES=Invented outcome variance"
        result=self.lab._judge(self.profile,{"case_id":"other-stale","input":request,"expected_behavior":"Require current evidence."},output)
        self.assertIn("Evidence uncertainty is not outcome variance",prompts[0])
        self.assertFalse(result["passed"])
        self.assertLess(result["score"],80)

    def test_identity_and_active_profile_remain_protected(self):
        validator=SportsValidation(self.lab,self.store.get_rows,self.store.save_row,"gemini","fixture",lambda:"now")
        self.assertEqual(validator.identity()[2]["harness_version"],v.HARNESS_VERSION)
        self.assertEqual(self.engine.get_skill("Sports Betting Analyst")["version"],1)
        with v.app.app_context():
            status=v.status().get_json()
        self.assertFalse(status["automatic_skill_activation_enabled"])
        self.assertFalse(status["sports_profitability_proven"])


if __name__ == "__main__":
    unittest.main()
