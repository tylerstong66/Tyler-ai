import json
import os
import types
import unittest
from unittest.mock import patch

import app_v2_19_3_11 as v
from sports_answer_audit import METRICS, ORACLES, audit_answer, render_answer
from sports_validation import SportsValidation
from skill_lab import SkillPromotionLab
from test_v2_18_skill_lab import FakeEngine, MemoryStore
from test_v2_19_3_3_gemini_training import FakeResponse

PASS = "COMPLETE=PASS\nMATH=PASS\nFACTS=PASS\nTASK=PASS\nSCORE=100\nWEAKNESSES=none"


def answer(cid=None):
    metrics = dict.fromkeys(METRICS)
    if cid in ORACLES:
        metrics.update(ORACLES[cid][1])
    return {"decision": "NO BET", "metrics": metrics,
            "rationale": "Point-estimate math alone does not justify a live bet without current evidence.",
            "uncertainty": "Supplied probabilities are unverified; assume no pushes unless given."}


def case(cid):
    return {"case_id": cid, "input": ORACLES[cid][0], "expected_behavior": "Correct math and uncertainty."}


class AnswerAuditTests(unittest.TestCase):
    def test_all_canonical_numeric_oracles_pass_correct_arithmetic(self):
        for cid in ORACLES:
            with self.subTest(cid=cid):
                _, errors = audit_answer(json.dumps(answer(cid)), case(cid))
                self.assertEqual(errors, [])

    def test_wrong_push_profit_cannot_pass(self):
        data = answer("holdout-push")
        data["metrics"]["expected_profit_per_unit"] = -.045
        _, errors = audit_answer(json.dumps(data), case("holdout-push"))
        self.assertIn("expected_profit_per_unit_wrong_for_case", errors)
        self.assertIn("expected_profit_per_unit_inconsistent", errors)

    def test_unconditional_win_cannot_be_used_as_conditional_win(self):
        data = answer("holdout-push")
        data["metrics"]["conditional_probability"] = .49
        data["metrics"]["edge_percentage_points"] = 100 * (.49 - 110 / 210)
        _, errors = audit_answer(json.dumps(data), case("holdout-push"))
        self.assertIn("conditional_probability_inconsistent", errors)
        self.assertIn("edge_percentage_points_inconsistent", errors)

    def test_raw_probability_cannot_be_called_no_vig(self):
        data = answer("sports-line-movement")
        data["metrics"]["no_vig_probability"] = 120 / 220
        _, errors = audit_answer(json.dumps(data), case("sports-line-movement"))
        self.assertIn("no_vig_requires_opposite_price", errors)

    def test_two_way_normalization_is_checked(self):
        data = answer("holdout-vig")
        data["metrics"]["no_vig_probability"] = 110 / 210
        _, errors = audit_answer(json.dumps(data), case("holdout-vig"))
        self.assertIn("no_vig_normalization_wrong", errors)

    def test_live_double_counted_vig_regression_is_rejected(self):
        data = answer("sports-no-bet")
        data["rationale"] = "An edge of 0.6% is far too thin to overcome the standard sportsbook juice (vig)."
        _, errors = audit_answer(json.dumps(data), case("sports-no-bet"))
        self.assertIn("positive_ev_rationale_double_counts_vig", errors)

    def test_positive_ev_can_legitimately_return_no_bet(self):
        data = answer("sports-no-bet")
        data["rationale"] = "The point estimate gives positive EV at the offered price, but uncertainty is larger than the edge. NO BET."
        self.assertEqual(audit_answer(json.dumps(data), case("sports-no-bet"))[1], [])

    def test_nonfinite_boolean_and_percentage_units_fail(self):
        for value in (float("nan"), float("inf"), True, 47):
            with self.subTest(value=value):
                data = answer("sports-edge-math")
                data["metrics"]["estimated_probability"] = value
                self.assertTrue(audit_answer(json.dumps(data), case("sports-edge-math"))[1])

    def test_missing_metric_and_truncated_json_fail(self):
        data = answer()
        del data["metrics"]["expected_profit_per_unit"]
        self.assertIn("expected_profit_per_unit_missing", audit_answer(json.dumps(data))[1])
        self.assertEqual(audit_answer('{"decision": "NO BET",')[1], ["answer_json_invalid"])

    def test_changed_numeric_input_does_not_use_wrong_oracle(self):
        changed = case("sports-edge-math")
        changed["input"] = changed["input"].replace("47%", "57%")
        self.assertIn("canonical_numeric_case_input_changed", audit_answer(json.dumps(answer("sports-edge-math")), changed)[1])

    def test_unsupported_joint_estimate_fails(self):
        data = answer()
        data["metrics"]["estimated_probability"] = .216
        c = {"case_id": "holdout-correlated-ticket", "input": "Unknown correlation", "expected_behavior": "NO BET"}
        self.assertIn("probability_estimate_not_supplied_for_case", audit_answer(json.dumps(data), c)[1])

    def test_unknown_custom_case_is_not_forced_to_no_bet(self):
        data = answer("sports-edge-math")
        data["decision"] = "VALUE CANDIDATE"
        self.assertEqual(audit_answer(json.dumps(data), {"case_id": "custom", "input": "supplied inputs"})[1], [])

    def test_runtime_format_keeps_checked_values_and_uncertainty(self):
        rendered = render_answer(answer("holdout-push"))
        self.assertIn("0.0155 units", rendered)
        self.assertIn("53.2609%", rendered)
        self.assertIn("Uncertainty:", rendered)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._context = types.MethodType(v.previous._sports_context, self.lab)

    def test_numeric_failure_overrides_would_be_perfect_judge_without_model_call(self):
        data = answer("sports-edge-math")
        data["metrics"]["edge_percentage_points"] = 17.5
        self.engine.complete = lambda *a, **k: self.fail("Judge should not be called for failed arithmetic")
        result = v._judge(self.lab, self.profile, case("sports-edge-math"), json.dumps(data))
        self.assertEqual(result["score"], 0)
        self.assertFalse(result["passed"])

    def test_failed_dimensions_or_weaknesses_cannot_receive_passing_score(self):
        for raw in (PASS.replace("MATH=PASS", "MATH=FAIL"), PASS.replace("none", "invented facts")):
            with self.subTest(raw=raw):
                self.engine.complete = lambda *a, **k: raw
                result = v._judge(self.lab, self.profile, case("sports-edge-math"), json.dumps(answer("sports-edge-math")))
                self.assertFalse(result["passed"])
                self.assertLess(result["score"], 80)

    def test_missing_duplicate_or_out_of_range_judge_fields_fail_closed(self):
        for raw in ("SCORE=100\nWEAKNESSES=none", PASS + "\nSCORE=100", PASS.replace("SCORE=100", "SCORE=101")):
            self.engine.complete = lambda *a, **k: raw
            result = v._judge(self.lab, self.profile, case("sports-edge-math"), json.dumps(answer("sports-edge-math")))
            self.assertEqual(result["score"], 0)

    def test_valid_judge_and_math_pass(self):
        self.engine.complete = lambda *a, **k: PASS
        result = v._judge(self.lab, self.profile, case("sports-edge-math"), json.dumps(answer("sports-edge-math")))
        self.assertTrue(result["passed"])
        self.assertTrue(result["objective_math_oracle"])

    def test_answer_has_larger_budget_strict_completion_and_all_rules(self):
        seen = {}
        def complete(messages, **kwargs):
            seen.update(kwargs)
            seen["strict"] = v.provider._REQUIRE_FINISHED_RESPONSE_CONTEXT.get()
            seen["provider"] = v.provider._TRAINING_PROVIDER_CONTEXT.get()
            seen["prompt"] = messages[0]["content"]
            return json.dumps(answer())
        self.engine.complete = complete
        v._run(self.lab, self.profile, "test")
        self.assertEqual(seen["tokens"], 800)
        self.assertTrue(seen["json_mode"])
        self.assertTrue(seen["strict"])
        self.assertEqual(seen["provider"], "gemini")
        for instruction in self.profile["instructions"]:
            self.assertIn(instruction, seen["prompt"])
        self.assertFalse(v.provider._REQUIRE_FINISHED_RESPONSE_CONTEXT.get())

    def test_non_sports_route_is_unchanged(self):
        with patch.object(v.previous, "_OLD_RUN", return_value="previous") as run:
            self.assertEqual(v._run(self.lab, {"skill_id": "other"}, "request"), "previous")
            run.assert_called_once()

    def test_authenticated_runtime_renders_the_checked_answer(self):
        client = v.app.test_client()
        with client.session_transaction() as session:
            session["tyler_ui_authenticated"] = True
        with patch.object(v.previous.previous, "ensure_sports_betting_skill", return_value=None), \
                patch.object(v.ENGINE, "get_skill", return_value=self.profile), \
                patch.object(v.SKILL_LAB, "_run", return_value=json.dumps(answer("holdout-push"))):
            response = client.post("/ui/chat", json={"message": "Sports analyze :: synthetic push check"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("0.0155 units", response.get_json()["reply"])
        self.assertIn("Uncertainty:", response.get_json()["reply"])

    def test_authenticated_runtime_rejects_bad_calculation(self):
        client = v.app.test_client()
        with client.session_transaction() as session:
            session["tyler_ui_authenticated"] = True
        data = answer("holdout-push")
        data["metrics"]["expected_profit_per_unit"] = -.045
        with patch.object(v.previous.previous, "ensure_sports_betting_skill", return_value=None), \
                patch.object(v.ENGINE, "get_skill", return_value=self.profile), \
                patch.object(v.SKILL_LAB, "_run", return_value=json.dumps(data)):
            response = client.post("/ui/chat", json={"message": "Sports analyze :: synthetic push check"})
        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.get_json()["success"])

    def test_old_validation_checkpoint_cannot_be_reused(self):
        validator = SportsValidation(self.lab, self.store.get_rows, self.store.save_row, "gemini", "model", lambda: "2026-10-06T18:00:00+00:00")
        session = validator.start()
        session["identity"]["harness_version"] = "sports-validation-v1-full-profile-400-160"
        self.store.rows[-1]["memories"] = json.dumps(session)
        self.assertIsNone(validator.latest())

    def test_truncated_response_does_not_advance_validation_checkpoint(self):
        validator = SportsValidation(self.lab, self.store.get_rows, self.store.save_row, "gemini", "model", lambda: "2026-10-06T18:00:00+00:00")
        self.lab._run = types.MethodType(v._run, self.lab)
        self.engine.complete = v.provider._provider_routed_complete
        validator.start()
        response = FakeResponse({"candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "partial"}]}}]})
        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-key"}), patch.object(v.base.requests, "post", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "confirmed complete"):
                validator.advance()
        self.assertEqual(validator.latest()["completed_cases"], 0)
        self.assertFalse(v.provider._REQUIRE_FINISHED_RESPONSE_CONTEXT.get())


class CompletionTests(unittest.TestCase):
    def test_strict_completion_accepts_stop_and_excludes_thought_parts(self):
        response = FakeResponse({"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "reasoning", "thought": True}, {"text": "answer"}]}}]})
        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-key"}), patch.object(v.base.requests, "post", return_value=response):
            self.assertEqual(v._complete(lambda: v.provider._gemini_complete([])), "answer")

    def test_absent_finish_metadata_fails_only_opt_in_callers(self):
        response = FakeResponse({"candidates": [{"content": {"parts": [{"text": "answer"}]}}]})
        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-key"}), patch.object(v.base.requests, "post", return_value=response):
            self.assertEqual(v.provider._gemini_complete([]), "answer")
            with self.assertRaises(RuntimeError):
                v._complete(lambda: v.provider._gemini_complete([]))


if __name__ == "__main__":
    unittest.main()
