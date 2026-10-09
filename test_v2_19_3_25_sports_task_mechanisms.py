import json
import types
import unittest

import app_v2_19_3_25 as v
from skill_lab import SkillPromotionLab
from sports_answer_audit import audit_answer
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore

PASS = "COMPLETE=PASS\nMATH=PASS\nFACTS=PASS\nTASK=PASS\nSCORE=100\nWEAKNESSES=none"
PARLAY = "A football parlay combines quarterback passing over, a receiver's receiving over, and opponent scoring under. Can independent multiplication price it?"


class TaskMechanismTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._context = types.MethodType(v.harness.previous._sports_context, self.lab)
        self.lab._run = types.MethodType(v.coverage_module._run, self.lab)
        self.lab._judge = types.MethodType(v.coverage_module._judge, self.lab)

    def output(self, request, rationale, uncertainty="Inputs and probabilities remain unverified."):
        self.engine.complete = lambda *a, **kw: json.dumps({"decision":"NO BET", "rationale":rationale, "uncertainty":uncertainty})
        return self.lab._run(self.profile, request)

    def test_observed_correlation_omission_stays_failed(self):
        output = self.output(PARLAY, "Joint ticket probability is unknown. Quarterback passing and receiver receiving correlation shares opportunity; opponent-under versus game-total-under requires script-dependent analysis. The conditional direction remains hypothetical without data.")
        self.engine.complete = lambda *a, **kw: self.fail("Omission must fail before semantic grading")
        result = self.lab._judge(self.profile, {"case_id":"unseen-ticket", "input":PARLAY, "expected_behavior":"A conditional mechanism and joint model."}, output)
        self.assertFalse(result["passed"])
        self.assertIn("explanation_missing_directional_conditional_mechanism", result["weaknesses"])

    def test_concrete_hypothesis_reaches_semantic_review(self):
        output = self.output(PARLAY, "Independent multiplication cannot price this joint ticket probability. Quarterback passing and receiver receiving can be positively correlated through shared opportunity. If low opponent scoring permits protecting a lead by running more, passing opportunities may decrease for both; opponent-under differs from game-total-under.", "A correlation-aware joint estimate is needed; this conditional hypothesis provides no magnitude or verified participation fact.")
        self.assertEqual(audit_answer(output, input_text=PARLAY)[1], [])
        calls=[]
        self.engine.complete = lambda *a, **kw: calls.append(a) or PASS
        result=self.lab._judge(self.profile,{"case_id":"unseen-mechanism","input":PARLAY,"expected_behavior":"Qualitative mechanism, not an assumed joint probability."},output)
        self.assertTrue(result["passed"])
        self.assertEqual(len(calls),1)

    def test_generic_positive_ev_caveat_cannot_override_semantic_failure(self):
        request="The sportsbook implies 51% and Tyler estimates 51.5%. Recommend a strong bet."
        output=self.output(request,"The supplied point estimate gives positive expected profit at the offered price, but inputs are unverified.")
        self.engine.complete=lambda *a,**kw: "COMPLETE=FAIL\nMATH=PASS\nFACTS=PASS\nTASK=FAIL\nSCORE=100\nWEAKNESSES=Missing model-error sensitivity"
        result=self.lab._judge(self.profile,{"case_id":"unseen-small-gap","input":request,"expected_behavior":"Explain why a marginal gap is fragile to probability error."},output)
        self.assertFalse(result["passed"])
        self.assertLess(result["score"],80)

    def test_probability_error_does_not_change_owned_arithmetic(self):
        request="Synthetic +120 odds, estimated win probability 0.46, no pushes."
        output=self.output(request,"The supplied estimate gives positive expected profit at the offered price. The thin gap is sensitive to probability-model error: a slight overestimate could move the true chance below break-even.","Missing uncertainty bounds justify NO BET; outcome variance affects risk, not expected value.")
        answer=json.loads(output)
        self.assertAlmostEqual(answer["metrics"]["expected_profit_per_unit"],.012)
        self.assertEqual(audit_answer(output,input_text=request)[1],[])
        self.engine.complete=lambda *a,**kw:PASS
        self.assertTrue(self.lab._judge(self.profile,{"case_id":"unseen-price","input":request,"expected_behavior":"Positive point EV with model uncertainty."},output)["passed"])

    def test_final_mechanism_instruction_is_task_scoped_and_after_policy(self):
        prompts=[]
        self.lab._context=lambda profile:"PROFILE_SENTINEL"
        self.engine.complete=lambda messages,**kw:prompts.append(messages[0]["content"]) or json.dumps({"decision":"NO BET","rationale":"Joint probability is unknown.","uncertainty":"Inputs missing."})
        self.lab._run(self.profile,PARLAY)
        prompt=prompts[0]
        self.assertGreater(prompt.index("For this connected football ticket"),prompt.index("Before responding, check each causal statement"))
        self.assertGreater(prompt.index("For this connected football ticket"),prompt.index("PROFILE_SENTINEL"))
        self.assertNotIn("EXPECTED",prompt)
        self.assertEqual(v.task_rules("Check original prediction records.",{"metrics":{}}),[])
        self.assertEqual(v.task_rules("Use yesterday's injury report.",{"metrics":{}}),[])

    def test_larger_gap_receives_sensitivity_rule_without_a_new_decision_threshold(self):
        request="Synthetic +190 odds, estimated win probability 0.44, no pushes."
        facts=v.math_module.calculate(request,synthetic=True)
        rules=v.task_rules(request,facts)
        self.assertEqual(len(rules),1)
        self.assertIn("A larger supplied gap also needs evidence",rules[0])
        self.assertNotIn("football",rules[0])

    def test_old_checkpoint_and_active_profile_remain_protected(self):
        validator=SportsValidation(self.lab,self.store.get_rows,self.store.save_row,"gemini","fixture",lambda:"now")
        _,_,identity=validator.identity()
        old=dict(identity,harness_version="sports-validation-v14-evidence-uncertainty")
        validator._save({"validation_id":"old","identity":old,"status":"running","completed_cases":10,"results":[]})
        new=validator.start()
        self.assertNotEqual(new["validation_id"],"old")
        self.assertEqual(new["completed_cases"],0)
        self.assertEqual(validator._records()[1]["completed_cases"],10)
        self.assertEqual(self.engine.get_skill("Sports Betting Analyst")["version"],1)
        self.assertEqual(identity["harness_version"],v.HARNESS_VERSION)
        with v.app.app_context():status=v.status().get_json()
        self.assertFalse(status["automatic_skill_activation_enabled"])
        self.assertFalse(status["sports_profitability_proven"])


if __name__=="__main__":unittest.main()
