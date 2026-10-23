import unittest
from unittest.mock import patch

import sports_chat_nhl_verified_adapter as adapter


class NhlVerifiedChatAdapterTests(unittest.TestCase):
    def setUp(self):
        self.prediction = {
            "game_id": "synthetic", "kickoff": "2026-10-25T00:00:00Z",
            "recorded_at": "2026-10-24T18:00:00Z", "sha256": "synthetic-pred",
            "probabilities": {"home": 0.6, "away": 0.4},
        }
        self.quote = {"recorded_at": "2026-10-24T18:00:00Z", "sha256": "synthetic-quote"}
        self.now = "2026-10-24T18:03:00Z"

    def test_missing_archived_evidence_is_not_eligible(self):
        result = adapter.nhl_verified_chat_comparison({}, {}, "/not-real", self.now)
        self.assertEqual(result["status"], "unavailable")
        self.assertTrue(result["NO_BET"])

    def test_reuses_strict_original_source_verifiers(self):
        with patch.object(adapter, "check_prediction") as check_prediction, \
             patch.object(adapter, "verify_original_prediction") as verify_original, \
             patch.object(adapter, "check_quote", return_value={"home": 150, "away": -150}) as check_quote:
            result = adapter.nhl_verified_chat_comparison(
                self.prediction, self.quote, "/synthetic", self.now)
        self.assertEqual(result["status"], "hypothetical_only")
        self.assertAlmostEqual(result["outcomes"]["home"]["hypothetical_ev_per_unit"], 0.5)
        self.assertTrue(result["NO_BET"])
        check_prediction.assert_called_once_with(self.prediction)
        verify_original.assert_called_once_with(self.prediction, "/synthetic")
        check_quote.assert_called_once_with(self.quote, self.prediction, "/synthetic", "entry")

    def test_rejects_unverified_quote(self):
        with patch.object(adapter, "check_prediction"), \
             patch.object(adapter, "verify_original_prediction"), \
             patch.object(adapter, "check_quote", side_effect=ValueError("unverified original bytes")):
            result = adapter.nhl_verified_chat_comparison(
                self.prediction, self.quote, "/synthetic", self.now)
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_stale_entry_price(self):
        with patch.object(adapter, "check_prediction"), \
             patch.object(adapter, "verify_original_prediction"), \
             patch.object(adapter, "check_quote", return_value={"home": 150, "away": -150}):
            result = adapter.nhl_verified_chat_comparison(
                self.prediction, self.quote, "/synthetic", "2026-10-24T20:00:00Z")
        self.assertEqual(result["status"], "unavailable")

    def test_rejects_started_event(self):
        with patch.object(adapter, "check_prediction"), \
             patch.object(adapter, "verify_original_prediction"), \
             patch.object(adapter, "check_quote", return_value={"home": 150, "away": -150}):
            result = adapter.nhl_verified_chat_comparison(
                self.prediction, self.quote, "/synthetic", "2026-10-25T01:00:00Z")
        self.assertEqual(result["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
