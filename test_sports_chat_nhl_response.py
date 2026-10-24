import unittest
from unittest.mock import patch

import app
from sports_chat_nhl_response import nhl_chat_evidence_response


class NhlChatEvidenceResponseTests(unittest.TestCase):
    def test_missing_evidence_never_leaks_model_numbers(self):
        response = app.reason_with_verified_nhl_evidence({}, ".")
        self.assertIn("unavailable", response)
        self.assertIn("NO_BET=true", response)
        self.assertNotIn("EV/unit", response)

    def test_explicit_verified_evidence_uses_deterministic_formatter(self):
        sample = {
            "status": "hypothetical_only", "NO_BET": True,
            "game_id": "synthetic", "model_sha256": "sha",
            "book": "draftkings", "market": "nhl_moneyline",
            "outcomes": {
                "home": {"model_probability": .6, "american_odds": -110,
                         "hypothetical_ev_per_unit": .1454},
                "away": {"model_probability": .4, "american_odds": 110,
                         "hypothetical_ev_per_unit": -.16}},
            "caveat": "Original bytes do not certify provider truth."
        }
        with patch("sports_chat_nhl_response.compare_nhl_manifest", return_value=sample):
            response = nhl_chat_evidence_response(
                {"prediction": "pred.json", "entry_quote": "quote.json"}, ".")
        self.assertIn("hypothetical", response)
        self.assertIn("home: model probability 0.6000", response)
        self.assertIn("NO_BET=true", response)

    def test_non_verified_status_fails_closed(self):
        with patch("sports_chat_nhl_response.compare_nhl_manifest",
                   return_value={"status": "unavailable", "NO_BET": True}):
            response = nhl_chat_evidence_response({}, ".")
        self.assertNotIn("model probability 0.", response)


if __name__ == "__main__":
    unittest.main()
