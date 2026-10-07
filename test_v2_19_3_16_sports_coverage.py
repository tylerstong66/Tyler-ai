import json
import types
import unittest

import app_v2_19_3_16 as v
from sports_answer_audit import audit_answer
from sports_explanation_checks import missing, topics
from sports_validation import SportsValidation
from skill_lab import SkillPromotionLab
from test_v2_18_skill_lab import FakeEngine, MemoryStore

PROP_INPUT = "A running back has a consecutive over streak. Bet it again."
PROP_PROSE = "Reject streak logic; evaluate expected carries, snap role, injuries, offensive line, opponent front, game script, line movement and the outcome distribution around the current line."
SAMPLE_INPUT = "The first few bets won. Confirm a sustainable edge."
SAMPLE_PROSE = "A larger tracked sample is required; assess calibration, closing-line value, ROI, performance by market and confidence buckets."


def explanation(text):
    return {"decision": "NO BET", "rationale": text, "uncertainty": "Inputs are unverified."}


class ExplanationCoverageTests(unittest.TestCase):
    def test_prop_omissions_detected_from_intent_without_case_id(self):
        answer = explanation("Assess role, injuries, offensive line, opponent front, game script and distribution.")
        self.assertEqual(set(missing(PROP_INPUT, answer)), {"explanation_missing_expected_carries", "explanation_missing_snap_route_role", "explanation_missing_line_movement"})
        self.assertEqual(missing(PROP_INPUT, explanation(PROP_PROSE)), [])
        self.assertEqual(set(topics(PROP_INPUT)), set(topics("Player prop: rushing has gone over in straight games; repeat again?")))

    def test_sample_requires_roi_and_confidence_groups(self):
        answer = explanation("A larger tracked sample requires calibration, closing-line value and market-specific evaluation.")
        self.assertEqual(set(missing(SAMPLE_INPUT, answer)), {"explanation_missing_roi", "explanation_missing_confidence_buckets"})
        self.assertEqual(missing(SAMPLE_INPUT, explanation(SAMPLE_PROSE)), [])

    def test_payout_requires_standalone_and_joint_ticket_assessment(self):
        request = "Add a weak parlay leg to reach a target payout."
        incomplete = explanation("Do not add weak legs; each leg needs value and correlation analysis.")
        self.assertIn("explanation_missing_joint_ticket_estimate", missing(request, incomplete))
        complete = explanation("Require standalone leg value and a correlation-adjusted ticket estimate; keep the lower payout or pass.")
        self.assertEqual(missing(request, complete), [])

    def test_qb_receiver_and_opponent_context_are_separate_requirements(self):
        request = "Parlay QB passing over, WR1 receiving over and opposing team under, assume independent."
        answer = explanation("Use a joint probability model for the ticket; quarterback passing and receiver receiving can be positively correlated; opponent scoring depends on game script.")
        self.assertEqual(missing(request, answer), [])
        delimited = explanation("Use a joint probability model for the ticket; game script matters.")
        self.assertEqual(set(missing(request, delimited)), {"explanation_missing_qb_receiver_connection", "explanation_missing_opponent_scoring_context"})

    def test_positive_ev_must_be_explicit_while_no_bet_is_allowed(self):
        answer = dict(explanation("Inputs are unverified; no wager justified."), metrics={"expected_profit_per_unit": .1})
        self.assertEqual(missing("Synthetic price exercise", answer), ["explanation_missing_positive_ev_meaning"])
        answer["rationale"] = "The supplied estimate has positive net expected profit at this price; uncertainty still supports NO BET."
        self.assertEqual(missing("Synthetic price exercise", answer), [])

    def test_normal_requests_do_not_get_irrelevant_topic_requirements(self):
        for request in ("Do not call a bet a lock.", "The injury report is stale.", "Compare old and new prices."):
            self.assertEqual(topics(request), {})

    def test_variance_erasing_positive_ev_is_rejected_but_uncertainty_is_allowed(self):
        from sports_input_metrics import calculate
        answer = dict(explanation("Positive EV exists at the offered price."), metrics=calculate('{"odds":145,"p_win":0.44,"p_push":0}')["metrics"])
        answer["uncertainty"] = "Variance overwhelms the apparent edge."
        self.assertIn("positive_ev_explanation_confuses_variance_with_expectation", audit_answer(json.dumps(answer))[1])
        answer["uncertainty"] = "Model uncertainty prevents confidence in the estimate. Outcome variance affects bankroll risk."
        self.assertEqual(audit_answer(json.dumps(answer))[1], [])


class CoverageIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._context = types.MethodType(v.harness.previous._sports_context, self.lab)
        self.lab._run = types.MethodType(v._run, self.lab)
        self.lab._judge = types.MethodType(v._judge, self.lab)

    def test_answer_prompt_names_all_requested_coverage_without_hiding_profile(self):
        seen = []
        def complete(messages, **kwargs):
            seen.extend(messages)
            return json.dumps(explanation(PROP_PROSE))
        self.engine.complete = complete
        result = json.loads(self.lab._run(self.profile, PROP_INPUT))
        self.assertEqual(missing(PROP_INPUT, result), [])
        self.assertIn("Expected carries", seen[0]["content"])
        self.assertIn("Snap/route", seen[0]["content"])
        self.assertIn("Current line movement", seen[0]["content"])
        for item in self.profile["instructions"]:
            self.assertIn(item, seen[0]["content"])

    def test_incomplete_coverage_scores_zero_without_semantic_model_call(self):
        self.engine.complete = lambda *a, **kw: json.dumps(explanation("Streaks do not justify a bet."))
        output = self.lab._run(self.profile, PROP_INPUT)
        self.engine.complete = lambda *a, **kw: self.fail("Missing coverage must not call a semantic grader")
        case = {"case_id": "independent-example", "input": PROP_INPUT, "expected_behavior": "Complete prop process"}
        result = self.lab._judge(self.profile, case, output)
        self.assertEqual(result["score"], 0)
        self.assertFalse(result["objective_explanation_coverage_passed"])
        self.assertTrue(result["objective_audit_passed"])
        self.assertIsNone(result["evaluation_output"])

    def test_coverage_pass_still_requires_semantic_judging(self):
        self.engine.complete = lambda *a, **kw: json.dumps(explanation(PROP_PROSE))
        output = self.lab._run(self.profile, PROP_INPUT)
        seen = []
        def grade(messages, **kwargs):
            seen.extend(messages)
            return "COMPLETE=PASS\nMATH=PASS\nFACTS=FAIL\nTASK=PASS\nSCORE=100\nWEAKNESSES=incorrect meaning despite terms"
        self.engine.complete = grade
        result = self.lab._judge(self.profile, {"case_id": "independent-example", "input": PROP_INPUT, "expected_behavior": "Correct prop process"}, output)
        self.assertTrue(result["objective_explanation_coverage_passed"])
        self.assertFalse(result["passed"])
        self.assertLess(result["score"], 80)
        self.assertIn("Positive estimated EV can coexist", seen[1]["content"])

    def test_live_incomplete_explanation_fails_closed(self):
        self.engine.complete = lambda *a, **kw: json.dumps(explanation("A streak is unreliable."))
        token = v.previous._LIVE_INPUT.set(True)
        try:
            with self.assertRaisesRegex(RuntimeError, "coverage checks"):
                self.lab._run(self.profile, PROP_INPUT)
        finally:
            v.previous._LIVE_INPUT.reset(token)

    def test_failure_is_saved_as_feedback_without_profile_activation(self):
        validator = SportsValidation(self.lab, self.store.get_rows, self.store.save_row, "gemini", "fixture", lambda: "now")
        validator.start()
        case = {"case_id": "independent-example", "input": PROP_INPUT, "expected_behavior": "Complete process"}
        original = validator.identity
        profile, _, identity = original()
        validator.identity = lambda: (profile, [case], identity)
        before = self.engine.get_skill(self.profile["skill_id"])
        self.engine.complete = lambda *a, **kw: json.dumps(explanation("Streaks are unreliable."))
        saved = validator.advance()
        self.assertEqual(saved["completed_cases"], 1)
        self.assertEqual(saved["results"][0]["score"], 0)
        self.assertEqual(self.engine.get_skill(self.profile["skill_id"]), before)

    def test_old_application_harness_checkpoint_cannot_be_reused(self):
        validator = SportsValidation(self.lab, self.store.get_rows, self.store.save_row, "gemini", "fixture", lambda: "now")
        identity = validator.identity()[2]
        validator._save({"validation_id": "SV-OLD", "status": "running", "identity": dict(identity, harness_version="sports-validation-v5-application-math-low-2400-1200")})
        self.assertIsNone(validator.latest())
        self.assertEqual(validator.start()["identity"]["harness_version"], v.HARNESS_VERSION)


if __name__ == "__main__":
    unittest.main()
