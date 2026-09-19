import os
import unittest
from unittest.mock import patch

from persistent_health_history import compact_snapshot
import app_v2_19_3_5 as v21935


class RuntimeFallbackReleaseTests(unittest.TestCase):
    def setUp(self):
        v21935.v210.DEPENDENCIES.reset()
        with v21935._FALLBACK_LOCK:
            v21935._FALLBACK_STATS.update({
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "last_reason": None,
            })

    def test_rate_limit_uses_one_gemini_fallback(self):
        messages = [{"role": "user", "content": "hello"}]
        with patch.object(
            v21935,
            "_PREVIOUS_NORMAL_GROQ",
            side_effect=RuntimeError("rate limit reached: tokens per day"),
        ) as primary, patch.object(
            v21935, "_gemini_runtime_configured", return_value=True
        ), patch.object(
            v21935, "_observed_gemini_runtime", return_value="fallback answer"
        ) as fallback:
            result = v21935.groq_with_gemini_runtime_fallback(
                messages, tokens=321, temperature=0.1, json_mode=True
            )

        self.assertEqual(result, "fallback answer")
        primary.assert_called_once()
        fallback.assert_called_once_with(
            messages, tokens=321, temperature=0.1, json_mode=True
        )
        self.assertEqual(v21935._FALLBACK_STATS["attempts"], 1)
        self.assertEqual(v21935._FALLBACK_STATS["successes"], 1)

    def test_retryable_provider_failures_are_classified(self):
        cases = {
            "request timed out": "timeout",
            "Groq returned 503: unavailable": "unavailable",
            "No accessible Groq fallback model completed the request": "model_access",
            "connection reset by peer": "unavailable",
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(
                    v21935._runtime_fallback_reason(RuntimeError(message)), expected
                )

    def test_auth_configuration_and_invalid_request_do_not_fallback(self):
        for message in [
            "401 unauthorized",
            "GROQ_API_KEY is not configured",
            "invalid request: context is too large",
        ]:
            with self.subTest(message=message), patch.object(
                v21935,
                "_PREVIOUS_NORMAL_GROQ",
                side_effect=RuntimeError(message),
            ), patch.object(
                v21935, "_observed_gemini_runtime"
            ) as fallback:
                with self.assertRaises(RuntimeError):
                    v21935.groq_with_gemini_runtime_fallback([])
                fallback.assert_not_called()

    def test_unconfigured_gemini_preserves_primary_error(self):
        with patch.object(
            v21935,
            "_PREVIOUS_NORMAL_GROQ",
            side_effect=RuntimeError("rate limit reached"),
        ), patch.object(
            v21935, "_gemini_runtime_configured", return_value=False
        ), patch.object(
            v21935, "_observed_gemini_runtime"
        ) as fallback:
            with self.assertRaisesRegex(RuntimeError, "rate limit reached"):
                v21935.groq_with_gemini_runtime_fallback([])
            fallback.assert_not_called()

    def test_failed_fallback_is_bounded_and_provider_neutral(self):
        with patch.object(
            v21935,
            "_PREVIOUS_NORMAL_GROQ",
            side_effect=RuntimeError("429 rate limit"),
        ) as primary, patch.object(
            v21935, "_gemini_runtime_configured", return_value=True
        ), patch.object(
            v21935,
            "_observed_gemini_runtime",
            side_effect=RuntimeError("Gemini runtime fallback timed out."),
        ) as fallback:
            with self.assertRaisesRegex(
                RuntimeError, "All configured text providers"
            ) as caught:
                v21935.groq_with_gemini_runtime_fallback([])

        primary.assert_called_once()
        fallback.assert_called_once()
        self.assertNotIn("api", str(caught.exception).lower())
        self.assertEqual(v21935._FALLBACK_STATS["attempts"], 1)
        self.assertEqual(v21935._FALLBACK_STATS["failures"], 1)

    def test_normal_skill_completion_falls_back_but_training_does_not(self):
        with patch.object(
            v21935,
            "_PREVIOUS_ENGINE_COMPLETE",
            side_effect=RuntimeError("provider returned 503"),
        ), patch.object(
            v21935, "_gemini_runtime_configured", return_value=True
        ), patch.object(
            v21935, "_observed_gemini_runtime", return_value="skill fallback"
        ) as fallback:
            self.assertEqual(
                v21935.engine_complete_with_runtime_fallback([]), "skill fallback"
            )
            fallback.assert_called_once()

            token = v21935.v21933._TRAINING_PROVIDER_CONTEXT.set("gemini")
            try:
                with self.assertRaisesRegex(RuntimeError, "503"):
                    v21935.engine_complete_with_runtime_fallback([])
            finally:
                v21935.v21933._TRAINING_PROVIDER_CONTEXT.reset(token)
            self.assertEqual(fallback.call_count, 1)

    def test_gemini_runtime_calls_are_observed_and_persistable(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "configured"}), patch.object(
            v21935, "_gemini_runtime_request", return_value="answer"
        ):
            self.assertEqual(v21935._observed_gemini_runtime([]), "answer")
            snapshot = v21935.v210.dependency_snapshot(include_errors=False)

        gemini = snapshot["services"]["gemini"]
        self.assertEqual(gemini["state"], "healthy")
        self.assertEqual(gemini["total_operations"], 1)
        record = compact_snapshot(snapshot, "v2.19.3.5")
        self.assertIn("gemini", record["services"])

    def test_status_and_source_grounding_expose_release(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "configured"}):
            response = v21935.app.test_client().get("/status")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["version_short"], "v2.19.3.5")
        self.assertEqual(
            data["normal_request_provider_policy"],
            "groq_primary_gemini_fallback",
        )
        self.assertTrue(data["runtime_provider_fallback"]["enabled"])
        self.assertEqual(
            data["runtime_provider_fallback"]["maximum_fallback_attempts_per_completion"],
            1,
        )
        self.assertIn("automatic_runtime_provider_fallback", data["capabilities"])
        self.assertIn("gemini", data["dependency_observability"]["services"])
        self.assertIn("app_v2_19_3_5.py", v21935.EXECUTOR.safe_source_files_fn())


if __name__ == "__main__":
    unittest.main()

