import json
import os
import types
import unittest
from unittest.mock import patch

import app_v2_19_3_14 as v
from skill_lab import SkillPromotionLab
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore
from test_v2_19_3_3_gemini_training import FakeResponse
from test_v2_19_3_11_sports_audit import answer, case, PASS


def response(text, finish="STOP"):
    return FakeResponse({"candidates": [{"finishReason": finish, "content": {
        "parts": [{"thought": True, "text": "private thought"}, {"text": text}]}}]})


class FlashCompletionTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._context = types.MethodType(v.harness.previous._sports_context, self.lab)
        self.lab._run = types.MethodType(v.harness._run, self.lab)
        self.lab._judge = types.MethodType(v.harness._judge, self.lab)
        self.validator = SportsValidation(self.lab, self.store.get_rows, self.store.save_row,
                                         "gemini", "gemini-3.5-flash", lambda: "now")

    def test_answer_has_bounded_budget_and_low_thinking_request(self):
        seen = {}
        def post(url, **kwargs):
            seen.update(kwargs["json"])
            return response(json.dumps(answer("sports-edge-math")))
        self.engine.complete = v.provider._gemini_complete
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fixture-key"}), \
                patch.object(v.provider, "GEMINI_MODEL", "gemini-3.5-flash"), \
                patch.object(v.base.requests, "post", side_effect=post):
            result = self.lab._run(self.profile, case("sports-edge-math")["input"])
        self.assertEqual(json.loads(result)["metrics"]["expected_profit_per_unit"], .175)
        self.assertEqual(seen["generationConfig"]["maxOutputTokens"], 2400)
        self.assertEqual(seen["generationConfig"]["thinkingConfig"], {"thinkingLevel": "LOW"})
        self.assertEqual(seen["generationConfig"]["responseMimeType"], "application/json")
        self.assertNotIn("private thought", result)

    def test_judge_has_separate_bounded_budget_and_strict_contract(self):
        seen = {}
        def complete(messages, **kwargs):
            seen.update(kwargs)
            seen["thinking"] = v.provider._SPORTS_THINKING_CONTEXT.get()
            return PASS
        self.engine.complete = complete
        result = self.lab._judge(self.profile, case("sports-edge-math"), json.dumps(answer("sports-edge-math")))
        self.assertEqual(seen["tokens"], 1200)
        self.assertEqual(seen["thinking"], "LOW")
        self.assertEqual(result["score"], 100)

    def test_incomplete_answer_cannot_advance_saved_checkpoint(self):
        self.validator.start()
        self.engine.complete = v.provider._gemini_complete
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fixture-key"}), \
                patch.object(v.base.requests, "post", return_value=response("{}", "MAX_TOKENS")):
            with self.assertRaisesRegex(RuntimeError, "confirmed complete"):
                self.validator.advance()
        self.assertEqual(self.validator.latest()["completed_cases"], 0)

    def test_incomplete_judge_cannot_advance_after_complete_answer(self):
        self.validator.start()
        data = answer()
        data["metrics"] = dict.fromkeys(data["metrics"])
        self.engine.complete = v.provider._gemini_complete
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fixture-key"}), \
                patch.object(v.base.requests, "post", side_effect=[response(json.dumps(data)), response(PASS, "MAX_TOKENS")]):
            with self.assertRaisesRegex(RuntimeError, "confirmed complete"):
                self.validator.advance()
        self.assertEqual(self.validator.latest()["completed_cases"], 0)

    def test_missing_finish_metadata_remains_rejected(self):
        self.engine.complete = v.provider._gemini_complete
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fixture-key"}), \
                patch.object(v.base.requests, "post", return_value=FakeResponse({"candidates": [{"content": {"parts": [{"text": "{}"}]}}]})):
            with self.assertRaisesRegex(RuntimeError, "confirmed complete"):
                self.lab._run(self.profile, "exercise")

    def test_context_is_restored_after_success_and_failure(self):
        for fail in (False, True):
            token = v.provider._SPORTS_THINKING_CONTEXT.set("outer")
            try:
                def call():
                    self.assertEqual(v.provider._SPORTS_THINKING_CONTEXT.get(), "LOW")
                    self.assertTrue(v.provider._REQUIRE_FINISHED_RESPONSE_CONTEXT.get())
                    if fail:
                        raise RuntimeError("provider failure")
                    return "done"
                if fail:
                    with self.assertRaises(RuntimeError):
                        v._complete(call)
                else:
                    self.assertEqual(v._complete(call), "done")
                self.assertEqual(v.provider._SPORTS_THINKING_CONTEXT.get(), "outer")
                self.assertFalse(v.provider._REQUIRE_FINISHED_RESPONSE_CONTEXT.get())
            finally:
                v.provider._SPORTS_THINKING_CONTEXT.reset(token)

    def test_normal_adapter_requests_keep_existing_generation_settings(self):
        seen = {}
        def post(url, **kwargs):
            seen.update(kwargs["json"])
            return response("ordinary response")
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fixture-key"}), \
                patch.object(v.base.requests, "post", side_effect=post):
            v.provider._gemini_complete([{"role": "user", "content": "ordinary"}], tokens=123)
        self.assertNotIn("thinkingConfig", seen["generationConfig"])
        self.assertEqual(seen["generationConfig"]["maxOutputTokens"], 123)

    def test_unsupported_model_fails_before_external_call(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fixture-key"}), \
                patch.object(v.provider, "GEMINI_MODEL", "gemini-2.5-flash"), \
                patch.object(v.base.requests, "post") as post:
            with self.assertRaisesRegex(RuntimeError, "Gemini 3 model"):
                v._complete(lambda: v.provider._gemini_complete([]))
        post.assert_not_called()

    def test_wrong_math_still_scores_zero_without_calling_judge(self):
        data = answer("sports-edge-math")
        data["metrics"]["expected_profit_per_unit"] = 1.175
        self.engine.complete = lambda *a, **kw: self.fail("No judge call is allowed")
        result = self.lab._judge(self.profile, case("sports-edge-math"), json.dumps(data))
        self.assertEqual(result["score"], 0)
        self.assertFalse(result["passed"])

    def test_prior_harness_checkpoint_is_not_reused(self):
        _, _, identity = self.validator.identity()
        old = {"validation_id": "SV-OLD", "status": "running", "completed_cases": 0,
               "identity": dict(identity, harness_version="sports-validation-v3-input-grounding-800-320")}
        self.validator._save(old)
        self.assertIsNone(self.validator.latest())
        saved = self.validator.start()
        self.assertEqual(saved["identity"]["harness_version"], v.HARNESS_VERSION)
        self.assertNotEqual(saved["validation_id"], "SV-OLD")

    def test_start_is_model_free_and_does_not_change_active_profile(self):
        before = self.engine.get_skill(self.profile["skill_id"])
        self.engine.complete = lambda *a, **kw: self.fail("Start must not call a model")
        result = self.validator.start()
        self.assertEqual(result["identity"]["harness_version"], v.HARNESS_VERSION)
        self.assertEqual(self.engine.get_skill(self.profile["skill_id"]), before)

    def test_status_reports_limits_and_keeps_activation_disabled(self):
        with v.app.app_context():
            data = v.status().get_json()
        self.assertEqual(data["version"], v.VERSION)
        self.assertEqual(data["sports_thinking_level"], "LOW")
        self.assertEqual(data["sports_answer_output_tokens"], 2400)
        self.assertEqual(data["sports_judge_output_tokens"], 1200)
        self.assertFalse(data["automatic_skill_activation_enabled"])


if __name__ == "__main__":
    unittest.main()
