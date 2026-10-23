import unittest
from unittest.mock import patch
import app
from sports_chat_model_evidence import verified_model_selection, chat_model_status

NOW = "2026-10-23T20:00:00Z"
EVIDENCE = {
    "model_id": "synthetic", "model_version": "test-only", "market": "moneyline",
    "event_id": "synthetic-game", "event_start": "2026-10-24T01:00:00Z",
    "prediction_recorded_at": "2026-10-23T18:00:00Z",
    "quote_recorded_at": "2026-10-23T19:00:00Z",
    "quote_verified": True, "prediction_verified": True,
    "source_url": "https://example.org/test-only", "american_odds": 150,
    "probability": 0.5,
}

class ModelChatEvidenceTests(unittest.TestCase):
    def test_no_model_evidence_fails_closed(self):
        self.assertEqual(verified_model_selection(None, NOW)["status"], "unavailable")

    def test_synthetic_hypothetical_math(self):
        result = verified_model_selection(EVIDENCE, NOW)
        self.assertEqual(result["status"], "hypothetical_only")
        self.assertAlmostEqual(result["expected_return_per_unit"], 0.25)
        self.assertTrue(result["NO_BET"])

    def test_rejects_unverified_or_late_or_invalid(self):
        for changes in ({"quote_verified": False},
                        {"prediction_recorded_at": "2026-10-24T02:00:00Z"},
                        {"event_start": "2026-10-23T19:00:00Z"},
                        {"probability": float("nan")},
                        {"american_odds": -50},
                        {"source_url": "http://example.org"}):
            with self.subTest(changes=changes):
                item = dict(EVIDENCE, **changes)
                self.assertEqual(verified_model_selection(item, NOW)["status"], "unavailable")

    def test_sports_chat_explicitly_disclaims_model_output(self):
        with patch.object(app, "feedback_context", return_value=""), \\
             patch.object(app, "groq", return_value="No verified model predictions") as model:
            app.reason_with_context("Research NBA odds tonight", research_context="Search excerpt")
        self.assertIn(chat_model_status(), model.call_args.args[0][1]["content"])

    def test_normal_chat_unaffected(self):
        with patch.object(app, "feedback_context", return_value=""), \\
             patch.object(app, "groq", return_value="hello") as model:
            app.reason_with_context("Hello")
        self.assertNotIn("SPORTS MODEL EVIDENCE STATUS", model.call_args.args[0][1]["content"])

if __name__ == "__main__":
    unittest.main()
