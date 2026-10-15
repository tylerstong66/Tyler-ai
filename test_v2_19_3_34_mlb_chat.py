"""Chat adapter contract tests; remote MLB network disabled by mocks."""
import json
import unittest
from unittest.mock import patch

import app_v2_19_3_34 as app34


def research():
    starter = {
        "pitcher": {"id": 20001, "name": "Synthetic Starter", "status": "probable"},
        "plate_appearances": 8, "at_bats": 7, "hits": 2,
        "home_runs": None, "historical_batting_average": .2857,
        "historical_hr_per_pa": None, "small_sample_under_25_pa": True,
        "source": None}
    return {
        "game_id": "849831", "hitter": {"id": 10001, "name": "Synthetic Hitter"},
        "starter_matchup": starter, "reliever_matchups": [],
        "coverage": {"expected_pitchers": 1, "pitchers_with_sourced_stats": 0},
        "decision": "RESEARCH ONLY - NO BET",
        "estimated_hit_probability": None, "estimated_home_run_probability": None,
        "joint_parlay_probability": None, "expected_value": None,
        "limitations": ["No calibrated prop probabilities.", "Possible relievers unconfirmed."],
        "official_data": {"capture_receipts": []}}


def command(**changes):
    data = {"game_id": 849831, "hitter_id": 10001, "hitter_side": "away", "reliever_ids": []}
    data.update(changes)
    return "sports mlb matchup research :: " + json.dumps(data)


class ParseTests(unittest.TestCase):
    def test_strict_request_accepts_optional_relief_ids(self):
        self.assertEqual(app34.parse_research_request(command(reliever_ids=[30001])),
                         (849831, 10001, "away", [30001]))

    def test_duplicate_unknown_and_missing_fields_are_refused(self):
        cases = [
            'sports mlb matchup research :: {"game_id":2,"game_id":3,"hitter_id":1,"hitter_side":"away"}',
            command(foo=1),
            'sports mlb matchup research :: {"game_id":123,"hitter_id":123}',
            command(reliever_ids="30001"),
            "sports mlb matchup research :: [1, 2]",
            "sports mlb matchup research :: garbage",
        ]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                app34.parse_research_request(case)

    def test_invalid_numeric_input_reaches_guarded_source_not_live_fetch(self):
        with patch.object(app34, "pregame_research", side_effect=ValueError("Invalid MLB ID")) as call:
            payload, code = app34.handle_message(command(game_id=True))
        self.assertEqual(code, 409)
        self.assertTrue(call.called)
        self.assertNotIn("sports_mlb_research", payload)


class ChatTests(unittest.TestCase):
    def test_explicit_command_is_read_only_and_includes_coverage(self):
        with patch.object(app34, "pregame_research", return_value=research()) as call:
            payload, status = app34.handle_message(command(reliever_ids=[30001]))
        self.assertEqual(status, 200)
        call.assert_called_once_with(849831, 10001, "away", [30001])
        self.assertEqual(payload["sports_mlb_research"]["decision"], "RESEARCH ONLY - NO BET")
        self.assertIn("NO BET", json.dumps(payload))
        self.assertNotIn("VALUE CANDIDATE", json.dumps(payload))

    def test_remote_errors_fail_closed_not_fake_recommendations(self):
        with patch.object(app34, "pregame_research", side_effect=RuntimeError("Upstream 503")):
            payload, status = app34.handle_message(command())
        self.assertEqual(status, 409)
        self.assertNotIn("sports_mlb_research", payload)
        self.assertIn("unavailable", json.dumps(payload).lower())

    def test_unrelated_chat_delegates_to_existing_skill(self):
        with patch.object(app34, "_OLD_HANDLE", return_value=({"original": True}, 200)) as prior:
            reply = app34.handle_message("show evidence paper trials")
        self.assertEqual(reply, ({"original": True}, 200))
        prior.assert_called_once_with("show evidence paper trials")

    def test_status_reports_not_deployed_probability_model(self):
        result = app34.status()
        data = result.get_json()
        self.assertTrue(data["sports_mlb_research_command_supported"])
        self.assertFalse(data["sports_mlb_research_official_data_live_schema_verified"])
        self.assertFalse(data["sports_mlb_player_prop_probabilities_calibrated"])
        self.assertFalse(data["sports_mlb_betting_enabled"])


if __name__ == "__main__":
    unittest.main()
