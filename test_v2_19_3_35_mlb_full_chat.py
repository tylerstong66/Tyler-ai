"""Versioned MLB composite chat: strict schema, no wager actions, old chat intact."""
import json
import unittest
from unittest.mock import patch

import app_v2_19_3_35 as app35


def request():
    return 'sports mlb full research :: {"game_id":849831,"hitter_id":10001,"hitter_side":"away","reliever_ids":[30001]}'


def complete():
    return {"game_id": "849831", "hitter": {"id": 10001, "name": "Synthetic Hitter"},
            "probable_starter": {"id": 20001, "name": "Synthetic Starter", "status": "probable"},
            "summary": ["Starter H2H sample: 10 PA.", "Possible reliever usage, not confirmed."],
            "coverage": {"recent_bullpen_records_complete": True},
            "decision": "RESEARCH ONLY - NO BET", "wager_executed": False,
            "estimated_hit_probability": None, "estimated_home_run_probability": None,
            "estimated_relief_appearance_probability": None, "parlay_joint_probability": None,
            "expected_value": None, "matchup_research": {}, "recent_bullpen_research": {}}


class FullCommandTests(unittest.TestCase):
    def test_success_is_research_only_and_does_not_execute_wager(self):
        with patch.object(app35, "complete_matchup_research", return_value=complete()) as call:
            result, code = app35.handle_message(request())
        self.assertEqual(code, 200)
        self.assertEqual(result["sports_mlb_full_research"]["decision"], "RESEARCH ONLY - NO BET")
        self.assertIn("NO BET", json.dumps(result))
        call.assert_called_once_with(849831, 10001, "away", [30001])

    def test_source_failure_never_produces_bet_or_fake_analysis(self):
        with patch.object(app35, "complete_matchup_research", side_effect=RuntimeError("Unavailable official feed")):
            result, code = app35.handle_message(request())
        self.assertEqual(code, 409)
        self.assertNotIn("sports_mlb_full_research", result)
        self.assertIn("unavailable", json.dumps(result).lower())

    def test_ambiguous_json_and_unknown_keys_rejected(self):
        for text in [
            'sports mlb full research :: {"game_id":849831,"game_id":1,"hitter_id":2,"hitter_side":"away"}',
            'sports mlb full research :: {"game_id":849831,"hitter_id":2,"hitter_side":"away","bet":true}',
            'sports mlb full research :: []',
            'sports mlb full research :: null',
        ]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                app35.parse_full_request(text)

    def test_other_commands_pass_to_previous_handler(self):
        with patch.object(app35, "_OLD_HANDLE", return_value=({"older": True}, 200)) as old:
            result = app35.handle_message("show evidence paper trials")
        self.assertEqual(result, ({"older": True}, 200))
        old.assert_called_once_with("show evidence paper trials")

    def test_new_module_reports_no_proven_probability(self):
        with app35.app.app_context():
            data = app35.status().get_json()
        self.assertTrue(data["sports_mlb_full_research_command_supported"])
        self.assertFalse(data["sports_mlb_full_research_live_api_verified"])
        self.assertFalse(data["sports_mlb_full_research_probabilities_validated"])
        self.assertFalse(data["sports_mlb_full_research_betting_enabled"])


if __name__ == "__main__":
    unittest.main()
