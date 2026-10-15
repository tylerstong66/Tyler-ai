"""Test combined source-checked MLB matchup and workload evidence."""
import copy
import unittest
from unittest.mock import patch

import sports_mlb_combined as combined
from test_sports_mlb_bullpen_usage import setup


class CombinedResearchTests(unittest.TestCase):
    def test_unified_starter_and_relief_research_remains_no_bet(self):
        result = combined.complete_matchup_research(849831, 10001, "away", [30001], reader=setup())
        self.assertEqual(result["game_id"], "849831")
        self.assertEqual(result["decision"], "RESEARCH ONLY - NO BET")
        self.assertEqual(result["probable_starter"]["id"], 20001)
        self.assertEqual(result["recent_bullpen_research"]["candidates"][0]["pitches_thrown_observed"], 16)
        self.assertTrue(result["coverage"]["recent_bullpen_records_complete"])
        self.assertTrue(any("small sample" in note for note in result["summary"]))
        self.assertIsNone(result["estimated_home_run_probability"])
        self.assertIsNone(result["estimated_relief_appearance_probability"])
        self.assertIsNone(result["parlay_joint_probability"])
        self.assertFalse(result["wager_executed"])

    def test_missing_historical_reliever_stats_stay_unknown(self):
        result = combined.complete_matchup_research(849831, 10001, "away", [30001], reader=setup())
        self.assertIsNone(result["matchup_research"]["reliever_matchups"][0]["plate_appearances"])
        self.assertTrue(any("no verified head-to-head count" in note for note in result["summary"]))

    def test_no_nominated_relief_candidates_does_not_invent_them(self):
        result = combined.complete_matchup_research(849831, 10001, "away", [], reader=setup())
        self.assertEqual(result["matchup_research"]["reliever_matchups"], [])
        self.assertEqual(result["recent_bullpen_research"]["candidates"], [])
        self.assertTrue(any("No prospective relievers" in note for note in result["summary"]))

    def test_conflicting_game_start_fails_closed(self):
        with patch.object(combined, "recent_pitcher_usage",
                          wraps=combined.recent_pitcher_usage) as real:
            original = real
            def changed(*args, **kwargs):
                result = original(*args, **kwargs)
                result["upcoming_first_pitch"] = "2026-10-15T23:01:00+00:00"
                return result
            with patch.object(combined, "recent_pitcher_usage", side_effect=changed):
                with self.assertRaisesRegex(ValueError, "starting times"):
                    combined.complete_matchup_research(849831, 10001, "away", [30001], reader=setup())

    def test_wrong_side_and_invalid_candidate_do_not_produce_a_report(self):
        with self.assertRaisesRegex(ValueError, "hitter_side"):
            combined.complete_matchup_research(849831, 10001, "none", reader=setup())
        with self.assertRaisesRegex(ValueError, "active pitcher"):
            combined.complete_matchup_research(849831, 10001, "away", [99999], reader=setup())


if __name__ == "__main__":
    unittest.main()
