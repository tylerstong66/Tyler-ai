import unittest
from unittest.mock import patch

import app
from sports_chat_nhl_response import nhl_chat_evidence_response
from sports_profitability_v1 import MODEL_SHA, MARKET


class NhlChatEvidenceResponseTests(unittest.TestCase):
    def test_missing_evidence_never_leaks_model_numbers(self):
        response = app.reason_with_verified_nhl_evidence({}, ".")
        self.assertIn("unavailable", response)
        self.assertIn("NO_BET=true", response)
        self.assertNotIn("EV/unit", response)

    def test_explicit_verified_evidence_uses_deterministic_formatter(self):
        sample = {
            "status": "hypothetical_only", "NO_BET": True,
            "game_id": "synthetic", "model_sha256": MODEL_SHA,
            "book": "draftkings", "market": MARKET,
            "outcomes": {
                "home": {"model_probability": .6, "american_odds": -110,
                         "hypothetical_ev_per_unit": .6 * (1 + 100 / 110) - 1},
                "away": {"model_probability": .4, "american_odds": 110,
                         "hypothetical_ev_per_unit": .4 * 2.1 - 1}},
            "caveat": "Original bytes do not certify provider truth."
        }
        with patch("sports_chat_nhl_response.compare_nhl_manifest", return_value=sample):
            response = nhl_chat_evidence_response(
                {"prediction": "pred.json", "entry_quote": "quote.json"}, ".")
        self.assertIn("hypothetical", response)
        self.assertIn("home: model probability 0.6000", response)
        self.assertIn("NO_BET=true", response)

    def test_inconsistent_ev_is_rejected(self):
        sample = {"status": "hypothetical_only", "NO_BET": True,
                  "game_id": "synthetic", "model_sha256": MODEL_SHA,
                  "book": "draftkings", "market": MARKET, "caveat": "Not executable",
                  "outcomes": {
                      "home": {"model_probability": .6, "american_odds": -110,
                               "hypothetical_ev_per_unit": 999},
                      "away": {"model_probability": .4, "american_odds": 110,
                               "hypothetical_ev_per_unit": -.16}}}
        with patch("sports_chat_nhl_response.compare_nhl_manifest", return_value=sample):
            response = nhl_chat_evidence_response({}, ".")
        self.assertIn("unavailable", response)
        self.assertNotIn("999", response)

    def test_non_verified_status_fails_closed(self):
        with patch("sports_chat_nhl_response.compare_nhl_manifest",
                   return_value={"status": "unavailable", "NO_BET": True}):
            response = nhl_chat_evidence_response({}, ".")
        self.assertNotIn("model probability 0.", response)


if __name__ == "__main__":
    unittest.main()
