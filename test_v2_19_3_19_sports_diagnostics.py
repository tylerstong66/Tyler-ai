import json
import types
import unittest

import app_v2_19_3_19 as v
from skill_lab import SkillPromotionLab
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class ExplanationDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.store,self.engine=MemoryStore(),FakeEngine()
        self.lab=SkillPromotionLab(self.engine,self.store.get_rows,self.store.save_row)
        self.profile=self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._context=types.MethodType(v.harness.previous._sports_context,self.lab)
        self.lab._run=types.MethodType(v.coverage_module._run,self.lab)
        self.lab._judge=types.MethodType(v._judge,self.lab)

    def response(self,prose):
        return json.dumps({"decision":"NO BET","rationale":prose,"uncertainty":"Inputs and probability estimates are unverified."})

    def test_only_supplied_identifiers_are_permitted_not_numeric_calculations(self):
        self.assertFalse(v.unsupported_numeric_prose("WR1 and QB share opportunity.","WR1 receiving and QB passing."))
        self.assertFalse(v.unsupported_numeric_prose("49ers remain unverified.","49ers input."))
        for prose in ("WR2 shares opportunity.","The price is -110.","EV is 0.175."):
            with self.subTest(prose=prose):
                self.assertTrue(v.unsupported_numeric_prose(prose,"WR1, -110, supplied EV 0.175."))

    def test_supplied_receiver_label_does_not_abort_complete_answer(self):
        self.engine.complete=lambda *a,**kw:self.response("WR1 usage is unverified; no edge established.")
        output=self.lab._run(self.profile,"WR1 usage is unavailable.")
        self.assertIn("WR1",json.loads(output)["rationale"])
        self.assertNotIn("explanation_contract_errors",json.loads(output))

    def test_complete_unsupported_numeric_prose_is_preserved_and_scores_zero(self):
        self.engine.complete=lambda *a,**kw:self.response("The invented edge is 12 percent.")
        output=self.lab._run(self.profile,"Evaluate this unknown quote.")
        self.assertIn("12 percent",json.loads(output)["rationale"])
        self.engine.complete=lambda *a,**kw:self.fail("Unsupported numeric prose must not call a semantic judge")
        result=self.lab._judge(self.profile,{"case_id":"other-numeric-failure","input":"Evaluate this unknown quote.","expected_behavior":"No invented math"},output)
        self.assertEqual(result["score"],0)
        self.assertFalse(result["objective_explanation_contract_passed"])

    def test_complete_failure_advances_one_failed_checkpoint_not_profile(self):
        validator=SportsValidation(self.lab,self.store.get_rows,self.store.save_row,"gemini","fixture",lambda:"now")
        validator.start()
        before=self.engine.get_skill(self.profile["skill_id"])
        self.engine.complete=lambda *a,**kw:self.response("There is an invented 12 percent edge.")
        result=validator.advance()
        self.assertEqual(result["completed_cases"],1)
        self.assertEqual(result["results"][0]["score"],0)
        self.assertEqual(self.engine.get_skill(self.profile["skill_id"]),before)

    def test_live_unsupported_numeric_prose_still_fails_closed(self):
        self.engine.complete=lambda *a,**kw:self.response("The invented edge is 12 percent.")
        token=v.math_module._LIVE_INPUT.set(True)
        try:
            with self.assertRaisesRegex(RuntimeError,"without numerals"):
                self.lab._run(self.profile,"Evaluate this quote.")
        finally:
            v.math_module._LIVE_INPUT.reset(token)

    def test_provider_failure_does_not_advance_or_create_failed_grade(self):
        validator=SportsValidation(self.lab,self.store.get_rows,self.store.save_row,"gemini","fixture",lambda:"now")
        validator.start()
        def fail(*a,**kw):raise RuntimeError("Unconfirmed complete response")
        self.engine.complete=fail
        with self.assertRaises(RuntimeError):validator.advance()
        self.assertEqual(validator.latest()["completed_cases"],0)
        self.assertEqual(validator.latest()["results"],[])

    def test_status_and_identity_preserve_separate_new_harness(self):
        validator=SportsValidation(self.lab,self.store.get_rows,self.store.save_row,"gemini","fixture",lambda:"now")
        self.assertEqual(validator.identity()[2]["harness_version"],v.HARNESS_VERSION)
        with v.app.app_context():result=v.status().get_json()
        self.assertTrue(result["sports_failed_numeric_prose_diagnostics_saved"])
        self.assertFalse(result["automatic_skill_activation_enabled"])


if __name__=="__main__":unittest.main()
