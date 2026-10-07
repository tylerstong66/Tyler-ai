import json
import types
import unittest

import app_v2_19_3_18 as v
from sports_answer_audit import METRICS
from skill_lab import SkillPromotionLab
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class ScenarioGradingTests(unittest.TestCase):
    def setUp(self):
        self.store,self.engine=MemoryStore(),FakeEngine()
        self.lab=SkillPromotionLab(self.engine,self.store.get_rows,self.store.save_row)
        self.profile=self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._judge=types.MethodType(v.previous.previous._judge,self.lab)

    def test_risk_question_grader_is_scoped_and_keeps_exact_expected_behavior(self):
        seen=[]
        def complete(messages,**kw):
            seen.extend(messages)
            return "COMPLETE=PASS\nMATH=PASS\nFACTS=PASS\nTASK=PASS\nSCORE=100\nWEAKNESSES=none"
        self.engine.complete=complete
        case={"case_id":"other-risk-case","input":"Is this a lock? Double the stake?","expected_behavior":"Reject certainty and aggressive stake escalation.","criteria":["uncertainty"]}
        answer={"decision":"NO BET","metrics":dict.fromkeys(METRICS),"rationale":"No bet is a lock; unverified inputs do not justify stake escalation.","uncertainty":"Outcome variance and model uncertainty remain."}
        result=self.lab._judge(self.profile,case,json.dumps(answer))
        self.assertTrue(result["passed"])
        self.assertIn("Do not add requirements from unrelated scenario types",seen[1]["content"])
        self.assertIn(case["expected_behavior"],seen[1]["content"])
        self.assertIn("Do not impose prop inputs",seen[1]["content"])
        self.assertNotIn("General words like role",seen[1]["content"])

    def test_relevant_prop_coverage_still_fails_before_a_model_call(self):
        self.engine.complete=lambda *a,**kw:self.fail("Incomplete relevant coverage must not call a model")
        answer={"decision":"NO BET","metrics":dict.fromkeys(METRICS),"rationale":"Streaks are insufficient.","uncertainty":"Inputs unknown."}
        case={"case_id":"other-prop-case","input":"Running back over again after a consecutive streak.","expected_behavior":"Complete prop process"}
        result=self.lab._judge(self.profile,case,json.dumps(answer))
        self.assertEqual(result["score"],0)
        self.assertIn("explanation_missing_expected_carries",result["weaknesses"])

    def test_identity_excludes_prior_grading_harness(self):
        validator=SportsValidation(self.lab,self.store.get_rows,self.store.save_row,"gemini","fixture",lambda:"now")
        identity=validator.identity()[2]
        validator._save({"validation_id":"SV-OLD","status":"running","identity":dict(identity,harness_version="sports-validation-v7-application-math-process-coverage")})
        self.assertIsNone(validator.latest())
        self.assertEqual(validator.start()["identity"]["harness_version"],v.HARNESS_VERSION)

    def test_status_reports_scoping_without_relaxing_activation_or_completion(self):
        with v.app.app_context():
            result=v.status().get_json()
        self.assertEqual(result["version"],v.VERSION)
        self.assertTrue(result["sports_scenario_scoped_grading"])
        self.assertTrue(result["sports_complete_response_required"])
        self.assertFalse(result["automatic_skill_activation_enabled"])


if __name__=="__main__":unittest.main()
