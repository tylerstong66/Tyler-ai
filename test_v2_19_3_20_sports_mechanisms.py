import json
import types
import unittest

import app_v2_19_3_20 as v
from skill_lab import SkillPromotionLab
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore

REQUEST = "Parlay quarterback passing over, receiver receiving over and opponent scoring under."
ECHO = "Joint probability model required; quarterback passing and receiver receiving can be positively correlated; opponent scoring and game script must be discussed; a concrete conditional game-script link shows that leading or trailing changes rushing and passing volume and opponent scoring without a fixed correlation sign."
ACTUAL = "A joint probability model is required. Quarterback passing and receiver receiving can be positively correlated. If the offense is leading and runs more, passing opportunities may fall for both; low opponent scoring may support that script. Signs remain game-dependent."


class ConditionalMechanismTests(unittest.TestCase):
    def answer(self, prose):
        return {"decision":"NO BET", "rationale":prose, "uncertainty":"Unknown joint probability and unverified inputs."}

    def test_observed_checklist_echo_is_rejected_without_case_id(self):
        self.assertIn("explanation_missing_directional_conditional_mechanism",v.missing(REQUEST,self.answer(ECHO)))

    def test_conditional_direction_is_accepted_but_not_proof_of_semantics(self):
        self.assertEqual(v.missing(REQUEST,self.answer(ACTUAL)),[])
        self.assertEqual(v.missing(REQUEST,self.answer(ACTUAL.replace("If the offense is leading and runs more, passing opportunities may fall for both", "When trailing, passing opportunities may increase for both"))),[])

    def test_other_sports_scenarios_do_not_receive_football_background(self):
        for request in ("Analyze a basketball prop.", "Parlay three unavailable leg estimates.", "Check a prediction ledger."):
            self.assertEqual(v.background(request,{}),[])
            self.assertNotIn("explanation_missing_directional_conditional_mechanism",v.missing(request,self.answer("No defensible estimate.")))

    def test_background_is_labelled_hypothetical_and_supplied_in_answer_prompt(self):
        store,engine=MemoryStore(),FakeEngine()
        lab=SkillPromotionLab(engine,store.get_rows,store.save_row)
        profile=lab.bootstrap_sports_betting_skill()["skill"]
        lab._context=types.MethodType(v.harness.previous._sports_context,lab)
        lab._run=types.MethodType(v.coverage_module._run,lab)
        prompts=[]
        def complete(messages,**kwargs):
            prompts.append(messages[0]["content"])
            return json.dumps(self.answer(ACTUAL))
        engine.complete=complete
        lab._run(profile,REQUEST)
        self.assertIn("hypotheses, not observed facts",prompts[0])
        self.assertIn("do not establish a fixed sign",prompts[0])

    def test_echo_scores_zero_without_a_semantic_judge(self):
        store,engine=MemoryStore(),FakeEngine()
        lab=SkillPromotionLab(engine,store.get_rows,store.save_row)
        profile=lab.bootstrap_sports_betting_skill()["skill"]
        lab._context=types.MethodType(v.harness.previous._sports_context,lab)
        lab._run=types.MethodType(v.coverage_module._run,lab)
        lab._judge=types.MethodType(v.previous._judge,lab)
        engine.complete=lambda *a,**kw:json.dumps(self.answer(ECHO))
        output=lab._run(profile,REQUEST)
        engine.complete=lambda *a,**kw:self.fail("Incomplete mechanism cannot reach semantic grading")
        result=lab._judge(profile,{"case_id":"unseen-qb-receiver","input":REQUEST,"expected_behavior":"Conditional mechanism"},output)
        self.assertEqual(result["score"],0)
        self.assertFalse(result["passed"])

    def test_live_echo_fails_closed_and_identity_is_separate(self):
        store,engine=MemoryStore(),FakeEngine()
        lab=SkillPromotionLab(engine,store.get_rows,store.save_row)
        profile=lab.bootstrap_sports_betting_skill()["skill"]
        lab._context=types.MethodType(v.harness.previous._sports_context,lab)
        lab._run=types.MethodType(v.coverage_module._run,lab)
        engine.complete=lambda *a,**kw:json.dumps(self.answer(ECHO))
        token=v.math_module._LIVE_INPUT.set(True)
        try:
            with self.assertRaisesRegex(RuntimeError,"directional_conditional"):
                lab._run(profile,REQUEST)
        finally:v.math_module._LIVE_INPUT.reset(token)
        validator=SportsValidation(lab,store.get_rows,store.save_row,"gemini","fixture",lambda:"now")
        self.assertEqual(validator.identity()[2]["harness_version"],v.HARNESS_VERSION)
        with v.app.app_context():self.assertFalse(v.status().get_json()["automatic_skill_activation_enabled"])


if __name__=="__main__":unittest.main()
