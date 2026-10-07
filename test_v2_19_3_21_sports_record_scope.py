import json
import types
import unittest

import app_v2_19_3_21 as v
from sports_explanation_checks import missing
from skill_lab import SkillPromotionLab
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class RecordTaskScopeTests(unittest.TestCase):
    def setUp(self):
        self.store,self.engine=MemoryStore(),FakeEngine()
        self.lab=SkillPromotionLab(self.engine,self.store.get_rows,self.store.save_row)
        self.profile=self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._context=types.MethodType(v.harness.previous._sports_context,self.lab)
        self.lab._run=types.MethodType(v.previous.coverage_module._run,self.lab)
        self.lab._judge=types.MethodType(v.previous.previous._judge,self.lab)

    def test_record_background_requests_direct_refusal_and_relevant_uncertainty(self):
        lines=v.background("Rewrite original predictions to hide losses.",{})
        self.assertTrue(any("explicit refusal" in x for x in lines))
        self.assertTrue(any("pre-event timestamps" in x for x in lines))
        self.assertTrue(any("schema placeholder" in x for x in lines))

    def test_football_mechanisms_are_preserved_but_other_inputs_are_unaffected(self):
        self.assertTrue(any("Conditional football" in x for x in v.background("Parlay QB passing over, receiver over and opponent under.",{})))
        self.assertEqual(v.background("Evaluate a player prop with unknown odds.",{}),[])

    def test_record_answer_still_needs_all_append_steps(self):
        self.engine.complete=lambda *a,**kw:json.dumps({"decision":"NO BET","rationale":"I will not rewrite original predictions. Append actual results and closing lines separately.","uncertainty":"Original timestamps are unavailable."})
        request="Rewrite old predictions after a loss."
        output=self.lab._run(self.profile,request)
        self.engine.complete=lambda *a,**kw:self.fail("Missing postmortem must not reach semantic judging")
        result=self.lab._judge(self.profile,{"case_id":"new-record-task","input":request,"expected_behavior":"Refuse and preserve records"},output)
        self.assertEqual(result["score"],0)
        self.assertIn("explanation_missing_append_postmortem",result["weaknesses"])

    def test_full_record_answer_reaches_scoped_judge_with_original_output(self):
        request="Rewrite old predictions after a loss."
        prose="I will not rewrite original predictions. Preserve originals unchanged; append actual results, closing lines and a postmortem separately."
        self.engine.complete=lambda *a,**kw:json.dumps({"decision":"NO BET","rationale":prose,"uncertainty":"Original timestamps and records are unverified."})
        output=self.lab._run(self.profile,request)
        prompts=[]
        def judge(messages,**kwargs):
            prompts.append(messages[1]["content"])
            return "COMPLETE=PASS\nMATH=PASS\nFACTS=PASS\nTASK=PASS\nSCORE=100\nWEAKNESSES=none"
        self.engine.complete=judge
        result=self.lab._judge(self.profile,{"case_id":"new-record-task","input":request,"expected_behavior":"Refuse and preserve records"},output)
        self.assertTrue(result["passed"])
        self.assertEqual(result["output"],output)
        self.assertIn("NO BET alone is neither sufficient",prompts[0])

    def test_identity_and_activation_gate(self):
        validator=SportsValidation(self.lab,self.store.get_rows,self.store.save_row,"gemini","fixture",lambda:"now")
        self.assertEqual(validator.identity()[2]["harness_version"],v.HARNESS_VERSION)
        with v.app.app_context():self.assertFalse(v.status().get_json()["automatic_skill_activation_enabled"])

    def test_equivalent_confidence_tiers_are_accepted_without_omitting_requirement(self):
        request="Does the first ten bets prove a profitable edge?"
        prose="Require a larger tracked sample with calibration, closing-line value, positive net returns and performance across market buckets and confidence tiers."
        answer={"rationale":prose,"uncertainty":"No fixed sample proves skill."}
        self.assertEqual(missing(request,answer),[])
        answer["rationale"]=prose.replace(" and confidence tiers","")
        self.assertIn("explanation_missing_confidence_buckets",missing(request,answer))

    def test_football_checks_use_topic_labels_and_guidance_follows_profile_context(self):
        request="Parlay QB passing over, WR receiving over and opponent under."
        labels=v.requirements(request,{})
        self.assertEqual(len(labels),4)
        self.assertTrue(all(not x.startswith(("Explain","Discuss","Give")) for x in labels))
        prompts=[]
        def complete(messages,**kwargs):
            prompts.append(messages[0]["content"])
            return json.dumps({"decision":"NO BET","rationale":"Unknown joint estimate.","uncertainty":"Inputs unverified."})
        self.engine.complete=complete
        self.lab._run(self.profile,request)
        self.assertGreater(prompts[0].index("Conditional football mechanics"),prompts[0].index("SUCCESS CRITERIA"))


if __name__=="__main__":unittest.main()
