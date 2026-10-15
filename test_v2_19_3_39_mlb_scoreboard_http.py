"""Read-only authenticated Tyler MLB shadow scoreboard route, no live sports bets."""
import json
import unittest
from unittest.mock import patch

import app as core
import app_v2_19_3_39 as latest

KEY="temporary-test-only-secret"
COMMAND="sports mlb shadow scoreboard"


def snapshot():
    return {
        "source":"https://raw.githubusercontent.com/tylerstong66/Tyler-ai/main/benchmarks/mlb_hitter_props_shadow_v1/scoreboard.latest.json",
        "published_at_utc":"2026-10-15T20:00:00+00:00",
        "snapshot_age_hours":0.5,
        "may_be_stale":False,
        "last_source_commit":"a"*40,
        "frozen_player_game_forecasts":7,
        "distinct_official_games":1,
        "pending":7,"scored":0,"ineligible":0,
        "metrics":{"hit":{"brier":None},"hr":{"brier":None}},
        "per_game":{"849810":{"predictions":7,"pending":7,"scored":0,"ineligible":0}},
        "no_wagers":True,
        "proven_betting_edge":False,
        "probabilities_condition":"at_least_one_official_at_bat",
        "limitations":["Research only, no sportsbook quotes."]
    }


class LiveScoreboardRouteTests(unittest.TestCase):
    def setUp(self):
        self.client=latest.app.test_client()

    def test_authenticated_readonly_scoreboard(self):
        with patch.object(core,"TYLER_API_KEY",KEY),patch.object(
            latest,"load_published_shadow_scoreboard",return_value=snapshot()) as getter:
            result=self.client.post("/chat",json={"message":COMMAND},
                       headers={"X-Tyler-Key":KEY})
        self.assertEqual(result.status_code,200,result.get_data(as_text=True)[:300])
        data=result.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["sports_mlb_shadow_scoreboard"]["distinct_official_games"],1)
        self.assertEqual(data["sports_mlb_shadow_scoreboard"]["pending"],7)
        self.assertIsNone(data["sports_mlb_shadow_scoreboard"]["metrics"]["hit"]["brier"])
        self.assertIn("NO BET",json.dumps(data))
        getter.assert_called_once_with()

    def test_unauthorized_must_not_query_public_github(self):
        with patch.object(core,"TYLER_API_KEY",KEY),patch.object(
            latest,"load_published_shadow_scoreboard",
            side_effect=AssertionError("Unauthorized fetch")) as getter:
            result=self.client.post("/chat",json={"message":COMMAND})
        self.assertEqual(result.status_code,401)
        getter.assert_not_called()

    def test_invalid_remote_feed_is_explicit_not_fake_scored_result(self):
        with patch.object(core,"TYLER_API_KEY",KEY),patch.object(
            latest,"load_published_shadow_scoreboard",
            side_effect=RuntimeError("Published report missing")):
            result=self.client.post("/chat",json={"message":COMMAND},
                        headers={"X-Tyler-Key":KEY})
        self.assertEqual(result.status_code,503)
        self.assertFalse(result.get_json()["success"])
        self.assertNotIn("sports_mlb_shadow_scoreboard",result.get_json())

    def test_nonmatching_commands_delegate_unchanged(self):
        with patch.object(latest,"_OLD_HANDLE",return_value=({"old":True},200)) as old:
            response=latest.handle_message("sports mlb full research by name :: {}")
        self.assertEqual(response,({"old":True},200))
        old.assert_called_once()

    def test_status_discloses_new_feature_but_no_wagers(self):
        status=self.client.get("/status").get_json()
        self.assertTrue(status["sports_mlb_shadow_scoreboard_command_supported"])
        self.assertTrue(status["sports_mlb_shadow_scoreboard_automated_snapshot_not_guaranteed_instant"])
        self.assertFalse(status["sports_mlb_shadow_scoreboard_wager_execution_enabled"])


if __name__=="__main__":
    unittest.main()
