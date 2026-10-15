"""Strict authenticated HTTP tests for v2.19.3.37 MLB research."""
import copy
import json
import unittest
from unittest.mock import patch

import app as core
import app_v2_19_3_37 as active

KEY="synthetic-test-only-key"
MSG='sports mlb full research by name :: {"date":"2026-10-15","hitter_name":"Synthetic Hitter","team_name":"Away Club"}'
OLD='sports mlb full research :: {"game_id":849831,"hitter_id":10001,"hitter_side":"away"}'


def resolved():
    return {
        "game_id":849831,"hitter_id":10001,"hitter_side":"away",
        "reliever_ids":[],"probable_starter_id":20001,
        "game_start":"2026-10-15T23:00:00+00:00",
        "team_name":"Away Club","opponent_name":"Home Club"}


def report():
    return {
        "game_id":"849831", "hitter":{"id":10001,"name":"Synthetic Hitter"},
        "probable_starter":{"id":20001,"name":"Synthetic Starter","status":"probable"},
        "summary":["Possible reliever usage is historical, not forecast."],
        "matchup_research":{"event_start":"2026-10-15T23:00:00+00:00",
            "reliever_matchups":[{"pitcher":{"id":30001,"name":"Synthetic Reliever","availability":"unknown"},
                                  "plate_appearances":None,"historical_batting_average":None}]},
        "recent_bullpen_research":{"candidates":[{
            "pitcher_id":30001,"recorded_appearances":1,
            "pitches_thrown_observed":16,"availability":"unknown"}]},
        "coverage":{"historical_pitcher_matchups":{"expected_pitchers":2,"pitchers_with_sourced_stats":1},
                    "recent_bullpen_records_complete":True},
        "auto_bullpen_discovery":{"historical_game_coverage_complete":True},
        "auto_bullpen_enabled":True,"reliever_ids_analyzed":[30001],
        "estimated_home_run_probability":None,"wager_executed":False,
        "decision":"RESEARCH ONLY - NO BET"}


class NamedAutoChatTests(unittest.TestCase):
    def setUp(self):
        self.client=active.app.test_client()

    def test_existing_named_command_defaults_to_auto_bullpen_and_displays_candidate(self):
        with patch.object(core, "TYLER_API_KEY", KEY), patch.object(
            active, "resolve_named_pregame", return_value=resolved()) as names, patch.object(
            active, "auto_bullpen_matchup", return_value=report()) as finder:
            out=self.client.post("/chat",json={"message":MSG},headers={"X-Tyler-Key":KEY})
        self.assertEqual(out.status_code,200,out.get_data(as_text=True)[:700])
        data=out.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["sports_mlb_auto_research"]["reliever_ids_analyzed"],[30001])
        self.assertIn("Synthetic Reliever",json.dumps(data))
        self.assertIn("NO BET",json.dumps(data))
        self.assertNotIn("FanDuel +",json.dumps(data))
        finder.assert_called_once()
        self.assertTrue(finder.call_args.kwargs["auto_select"])
        names.assert_called_once()

    def test_explicit_false_flag_preserves_manual_mode(self):
        msg='sports mlb full research by name :: {"date":"2026-10-15","hitter_name":"Synthetic Hitter","auto_bullpen":false}'
        parsed,flag=active.parse_auto_request(msg)
        self.assertFalse(flag)
        self.assertNotIn("auto_bullpen",parsed)

    def test_manual_relievers_default_to_manual_not_auto(self):
        msg='sports mlb full research by name :: {"date":"2026-10-15","hitter_name":"Synthetic Hitter","reliever_names":["Synthetic Reliever"]}'
        raw,flag=active.parse_auto_request(msg)
        self.assertFalse(flag)
        self.assertEqual(raw["reliever_names"],["Synthetic Reliever"])

    def test_double_instruction_and_duplicate_flag_are_rejected(self):
        bad=[
            '{"date":"2026-10-15","hitter_name":"Test","reliever_names":["X"],"auto_bullpen":true}',
            '{"date":"2026-10-15","hitter_name":"Test","auto_bullpen":true,"auto_bullpen":false}',
            '{"date":"2026-10-15","hitter_name":"Test","auto_bullpen":"yes"}',
            '{"date":"2026-10-15","hitter_name":"Test","mystery":true}',
            '{"date":"2026-10-15","hitter_name":"Test","auto_bullpen":NaN}',
        ]
        for item in bad:
            with self.subTest(item=item),self.assertRaises(ValueError):
                active.parse_auto_request(active.PREFIX+" "+item)

    def test_unauthed_does_not_fetch_public_data(self):
        with patch.object(core, "TYLER_API_KEY", KEY), patch.object(
            active, "resolve_named_pregame",side_effect=AssertionError("Unauthenticated fetch")) as fn:
            out=self.client.post("/chat",json={"message":MSG})
        self.assertEqual(out.status_code,401)
        fn.assert_not_called()

    def test_changed_starter_fails_closed(self):
        value=report()
        value["probable_starter"]["id"]=99999
        with patch.object(core, "TYLER_API_KEY", KEY), patch.object(
            active, "resolve_named_pregame",return_value=resolved()), patch.object(
            active, "auto_bullpen_matchup",return_value=value):
            out=self.client.post("/chat",json={"message":MSG},headers={"X-Tyler-Key":KEY})
        self.assertEqual(out.status_code,409)
        self.assertNotIn("sports_mlb_auto_research",out.get_json())
        self.assertFalse(out.get_json()["success"])

    def test_original_id_command_unchanged(self):
        with patch.object(active,"_OLD_HANDLE",return_value=({"legacy":True},200)) as old:
            self.assertEqual(active.handle_message(OLD),({"legacy":True},200))
        old.assert_called_once_with(OLD)

    def test_status_has_no_claims_of_probabilities_or_wagers(self):
        status=self.client.get("/status").get_json()
        self.assertTrue(status["sports_mlb_auto_bullpen_research_supported"])
        self.assertFalse(status["sports_mlb_auto_bullpen_probabilities_calibrated"])
        self.assertFalse(status["sports_mlb_auto_bullpen_wager_execution_enabled"])


if __name__=="__main__":
    unittest.main()
