import unittest
from unittest.mock import patch

import app_v2_19_3_6 as v21936


class ProviderReceiptFallbackDrillTests(unittest.TestCase):
    def setUp(self):
        with v21936._DRILL_LOCK:
            v21936._DRILL_STATS.update({
                "runs": 0,
                "passes": 0,
                "failures": 0,
                "last_result": None,
            })

    def test_drill_command_is_exact_and_bounded(self):
        self.assertTrue(v21936.fallback_drill_request("Run runtime fallback drill"))
        self.assertTrue(v21936.fallback_drill_request("Run Gemini fallback drill"))
        self.assertFalse(v21936.fallback_drill_request("Run every drill"))

    def test_drill_passes_with_one_gemini_call_and_no_business_side_effect(self):
        with patch.object(
            v21936.v21935, "_gemini_runtime_configured", return_value=True
        ), patch.object(
            v21936,
            "_ORIGINAL_TRY_RUNTIME_FALLBACK",
            return_value="TYLER_FALLBACK_OK",
        ) as fallback, patch.object(
            v21936.base, "send_email_via_n8n"
        ) as email, patch.object(
            v21936.base, "save_memory"
        ) as memory:
            token = v21936._PROVIDER_ROUTING.set(None)
            try:
                payload, status = v21936._run_runtime_fallback_drill()
            finally:
                v21936._PROVIDER_ROUTING.reset(token)

        self.assertEqual(status, 200)
        self.assertTrue(payload["success"])
        result = payload["runtime_fallback_drill"]
        self.assertTrue(result["passed"])
        self.assertEqual(result["real_provider_calls"], {"groq": 0, "gemini": 1})
        self.assertFalse(result["business_side_effects_attempted"])
        self.assertEqual(result["provider_routing"]["provider"], "gemini")
        self.assertEqual(result["provider_routing"]["reason"], "rate_limit")
        self.assertEqual(fallback.call_count, 1)
        email.assert_not_called()
        memory.assert_not_called()

    def test_drill_failure_exposes_only_safe_category(self):
        with patch.object(
            v21936.v21935, "_gemini_runtime_configured", return_value=True
        ), patch.object(
            v21936,
            "_ORIGINAL_TRY_RUNTIME_FALLBACK",
            side_effect=RuntimeError("Gemini runtime fallback timed out."),
        ):
            payload, status = v21936._run_runtime_fallback_drill()
        self.assertEqual(status, 200)
        self.assertFalse(payload["success"])
        self.assertEqual(
            payload["runtime_fallback_drill"]["failure_category"], "timeout"
        )
        self.assertNotIn("exception", payload["reply"].lower())

    def test_unconfigured_drill_sends_no_provider_request(self):
        with patch.object(
            v21936.v21935, "_gemini_runtime_configured", return_value=False
        ), patch.object(
            v21936, "_ORIGINAL_TRY_RUNTIME_FALLBACK"
        ) as fallback:
            payload, _ = v21936._run_runtime_fallback_drill()
        self.assertFalse(payload["success"])
        self.assertEqual(
            payload["runtime_fallback_drill"]["real_provider_calls"],
            {"groq": 0, "gemini": 0},
        )
        fallback.assert_not_called()

    def test_normal_response_gets_primary_provider_receipt(self):
        def fake_handle(_message):
            answer = v21936.base.groq([{"role": "user", "content": "hello"}])
            return v21936.base.base_payload("answer", answer), 200

        with patch.object(
            v21936, "_PREVIOUS_NORMAL_ROUTER", return_value="primary answer"
        ), patch.object(
            v21936, "_PREVIOUS_HANDLE_MESSAGE", side_effect=fake_handle
        ):
            payload, status = v21936.handle_message_v21936("hello")
        self.assertEqual(status, 200)
        self.assertEqual(payload["provider_routing"]["provider"], "groq")
        self.assertEqual(payload["provider_routing"]["mode"], "primary")

    def test_fallback_receipt_contains_safe_reason(self):
        with patch.object(
            v21936,
            "_ORIGINAL_TRY_RUNTIME_FALLBACK",
            return_value="fallback answer",
        ):
            token = v21936._PROVIDER_ROUTING.set(None)
            try:
                result = v21936._try_runtime_fallback_with_receipt(
                    RuntimeError("429 rate limit"), [], 100, 0, False
                )
                receipt = v21936._PROVIDER_ROUTING.get()
            finally:
                v21936._PROVIDER_ROUTING.reset(token)
        self.assertEqual(result, "fallback answer")
        self.assertEqual(receipt, {
            "provider": "gemini",
            "mode": "runtime_fallback",
            "verified": True,
            "reason": "rate_limit",
        })

    def test_drill_api_requires_authentication(self):
        response = v21936.app.test_client().post(
            "/diagnostics/runtime-fallback/drill"
        )
        self.assertEqual(response.status_code, 401)

    def test_authorized_drill_api_returns_structured_receipt(self):
        with patch.object(v21936.base, "TYLER_API_KEY", "test-key"), patch.object(
            v21936.v21935, "_gemini_runtime_configured", return_value=True
        ), patch.object(
            v21936,
            "_ORIGINAL_TRY_RUNTIME_FALLBACK",
            return_value="TYLER_FALLBACK_OK",
        ):
            response = v21936.app.test_client().post(
                "/diagnostics/runtime-fallback/drill",
                headers={"X-Tyler-Key": "test-key"},
            )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["runtime_fallback_drill"]["passed"])
        self.assertEqual(data["provider_routing"]["provider"], "gemini")

    def test_ui_and_status_expose_receipts_without_unsafe_html(self):
        template = v21936.base.CHAT_HTML
        self.assertIn("meta.provider_routing", template)
        self.assertIn('"Gemini fallback"', template)
        self.assertNotIn("providerReceipt.innerHTML", template)

        response = v21936.app.test_client().get("/status")
        data = response.get_json()
        self.assertEqual(data["version_short"], "v2.19.3.6")
        self.assertTrue(data["runtime_fallback_drill"]["authentication_required"])
        self.assertEqual(data["runtime_fallback_drill"]["real_groq_calls_per_run"], 0)
        self.assertFalse(data["runtime_fallback_drill"]["business_side_effects_enabled"])
        self.assertIn("provider_routing_receipts", data["capabilities"])
        self.assertIn("app_v2_19_3_6.py", v21936.EXECUTOR.safe_source_files_fn())


if __name__ == "__main__":
    unittest.main()

