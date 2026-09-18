import os
import runpy
import unittest
from unittest.mock import patch

import app_v2_19_3_3 as v21933


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300

    def json(self):
        return self.payload


class GeminiTrainingTests(unittest.TestCase):
    def test_gemini_adapter_uses_header_and_maps_messages(self):
        seen = {}

        def post(url, **kwargs):
            seen.update({"url": url, **kwargs})
            return FakeResponse({
                "candidates": [{"content": {"parts": [{"text": "done"}]}}]
            })

        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-key"}), patch.object(
            v21933.base.requests, "post", side_effect=post
        ):
            result = v21933._gemini_complete(
                [
                    {"role": "system", "content": "Follow the rubric."},
                    {"role": "user", "content": "Evaluate this."},
                ],
                tokens=123,
                temperature=0.1,
                json_mode=True,
            )

        self.assertEqual(result, "done")
        self.assertNotIn("private-test-key", seen["url"])
        self.assertEqual(seen["headers"]["x-goog-api-key"], "private-test-key")
        self.assertEqual(seen["json"]["generationConfig"]["maxOutputTokens"], 123)
        self.assertEqual(
            seen["json"]["generationConfig"]["responseMimeType"], "application/json"
        )
        self.assertEqual(
            seen["json"]["system_instruction"]["parts"][0]["text"],
            "Follow the rubric.",
        )

    def test_gemini_quota_error_is_safe_and_preserves_round(self):
        response = FakeResponse({
            "error": {
                "status": "RESOURCE_EXHAUSTED",
                "message": "quota exhausted for a private project",
            }
        }, 429)
        with patch.dict(os.environ, {"GEMINI_API_KEY": "private-test-key"}), patch.object(
            v21933.base.requests, "post", return_value=response
        ):
            with self.assertRaises(RuntimeError) as caught:
                v21933._gemini_complete([{"role": "user", "content": "x"}])
        message = str(caught.exception)
        self.assertIn("No training round was consumed", message)
        self.assertNotIn("private-test-key", message)
        self.assertNotIn("private project", message)

    def test_provider_router_keeps_normal_requests_on_previous_provider(self):
        old_gemini = v21933._gemini_complete
        old_previous = v21933._PREVIOUS_ENGINE_COMPLETE
        try:
            v21933._gemini_complete = lambda *args, **kwargs: "gemini"
            v21933._PREVIOUS_ENGINE_COMPLETE = lambda *args, **kwargs: "groq"
            self.assertEqual(v21933._provider_routed_complete([]), "groq")
            token = v21933._TRAINING_PROVIDER_CONTEXT.set("gemini")
            try:
                self.assertEqual(v21933._provider_routed_complete([]), "gemini")
            finally:
                v21933._TRAINING_PROVIDER_CONTEXT.reset(token)
        finally:
            v21933._gemini_complete = old_gemini
            v21933._PREVIOUS_ENGINE_COMPLETE = old_previous

    def test_benchmark_records_are_provider_annotated(self):
        original = v21933._ORIGINAL_LAB_SAVE
        try:
            v21933._ORIGINAL_LAB_SAVE = lambda category, payload, importance: payload
            token = v21933._TRAINING_PROVIDER_CONTEXT.set("gemini")
            try:
                saved = v21933._provider_annotated_lab_save(
                    object(), "skill_benchmark_run", {"run_id": "EVL-1"}, 7
                )
            finally:
                v21933._TRAINING_PROVIDER_CONTEXT.reset(token)
        finally:
            v21933._ORIGINAL_LAB_SAVE = original
        self.assertEqual(saved["evaluation_provider"], "gemini")
        self.assertEqual(saved["evaluation_model"], v21933.GEMINI_MODEL)
        self.assertTrue(saved["provider_consistent"])

    def test_provider_valid_eval_does_not_mix_groq_and_gemini(self):
        class FakeLab:
            def _suite_hash(self, skill_id):
                return "suite"

            def _profile_fingerprint(self, profile):
                return "fingerprint"

            def evaluations(self, skill_id, target_kind, limit):
                shared = {
                    "suite_hash": "suite",
                    "profile_fingerprint": "fingerprint",
                    "target_kind": target_kind,
                }
                return [
                    {**shared, "run_id": "groq", "evaluation_provider": "groq"},
                    {
                        **shared,
                        "run_id": "gemini",
                        "evaluation_provider": "gemini",
                        "evaluation_model": v21933.GEMINI_MODEL,
                    },
                ]

        token = v21933._TRAINING_PROVIDER_CONTEXT.set("gemini")
        try:
            run = v21933._provider_valid_eval(
                FakeLab(), {"skill_id": "skill"}, "active"
            )
        finally:
            v21933._TRAINING_PROVIDER_CONTEXT.reset(token)
        self.assertEqual(run["run_id"], "gemini")

    def test_old_unpinned_session_requires_restart(self):
        class FakeEngine:
            def get_skill(self, name):
                return {"skill_id": "tyler-ai-developer"}

        class FakeLab:
            engine = FakeEngine()

        class FakeTrainer:
            lab = FakeLab()
            TERMINAL = {"exhausted"}

            def latest_session(self, skill_id):
                return {"status": "needs_next_round"}

        with patch.dict(os.environ, {"GEMINI_API_KEY": "configured"}):
            with self.assertRaisesRegex(ValueError, "Restart champion training"):
                v21933._gemini_training_start(
                    FakeTrainer(), "tyler-ai-developer", restart=False
                )

    def test_gemini_session_skips_cross_provider_historical_seed(self):
        original = v21933._ORIGINAL_SEED_CHAMPION_STATE
        try:
            v21933._ORIGINAL_SEED_CHAMPION_STATE = lambda session: self.fail(
                "historical seed should not run"
            )
            token = v21933._TRAINING_PROVIDER_CONTEXT.set("gemini")
            try:
                session = v21933._provider_seed_champion_state(
                    object(), {"session_id": "TRN-1"}
                )
            finally:
                v21933._TRAINING_PROVIDER_CONTEXT.reset(token)
        finally:
            v21933._ORIGINAL_SEED_CHAMPION_STATE = original
        self.assertEqual(session, {"session_id": "TRN-1"})

    def test_failed_restart_reuses_saved_gemini_baseline(self):
        class FakeEngine:
            def get_skill(self, name):
                return {"skill_id": "tyler-ai-developer"}

        class FakeLab:
            engine = FakeEngine()

            def __init__(self):
                self.evaluations = 0

            def _valid_eval(self, active, target_kind):
                return {"run_id": "EVL-GEMINI"}

            def evaluate(self, skill_id, target_kind):
                self.evaluations += 1

        class FakeTrainer:
            lab = FakeLab()
            TERMINAL = {"exhausted"}

            def latest_session(self, skill_id):
                return {"status": "needs_next_round"}

        original = v21933._ORIGINAL_TRAINER_START
        try:
            v21933._ORIGINAL_TRAINER_START = lambda skill_name, restart: {
                "session_id": "TRN-NEW"
            }
            with patch.dict(os.environ, {"GEMINI_API_KEY": "configured"}):
                result = v21933._gemini_training_start(
                    FakeTrainer(), "tyler-ai-developer", restart=True
                )
        finally:
            v21933._ORIGINAL_TRAINER_START = original
        self.assertEqual(result["session_id"], "TRN-NEW")
        self.assertEqual(FakeTrainer.lab.evaluations, 0)

    def test_status_and_source_inventory_expose_safe_configuration_only(self):
        self.assertEqual(v21933.VERSION_SHORT, "v2.19.3.3")
        self.assertEqual(v21933.GEMINI_MODEL, "gemini-3.5-flash-lite")
        self.assertIn("app_v2_19_3_3.py", v21933.EXECUTOR.safe_source_files_fn())
        self.assertIn("gunicorn.conf.py", v21933.EXECUTOR.safe_source_files_fn())
        with v21933.app.app_context():
            status = v21933.status_v21933().get_json()
        self.assertEqual(status["training_provider"], "gemini")
        self.assertTrue(status["provider_pinned_training_enabled"])
        self.assertNotIn("gemini_api_key", status)
        trainer_status = v21933.TRAINER.status()
        self.assertFalse(trainer_status["automatic_activation"])
        self.assertTrue(trainer_status["human_promotion_required"])

    def test_gunicorn_allows_atomic_training_request_to_finish(self):
        config = runpy.run_path("gunicorn.conf.py")
        self.assertEqual(config["timeout"], 120)
        self.assertEqual(config["graceful_timeout"], 30)


if __name__ == "__main__":
    unittest.main()
