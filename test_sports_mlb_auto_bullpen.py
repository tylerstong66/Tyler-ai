"""Independent test of auto-selection followed by full MLB matchup research."""
import unittest
from unittest.mock import patch

from sports_mlb_auto_bullpen import auto_bullpen_matchup
from test_sports_mlb_reliever_candidates import fixture


class AutoResearchTests(unittest.TestCase):
    def test_auto_shortlist_passes_verified_reliever_into_h2h_and_workload(self):
        result = auto_bullpen_matchup(849831, 10001, "away", reader=fixture())
        self.assertTrue(result["auto_bullpen_enabled"])
        self.assertEqual(result["reliever_ids_analyzed"], [30001])
        self.assertEqual(result["auto_bullpen_discovery"]["selection"][0]["pitcher_id"], 30001)
        self.assertEqual(result["recent_bullpen_research"]["candidates"][0]["pitches_thrown_observed"], 16)
        self.assertEqual(result["decision"], "RESEARCH ONLY - NO BET")
        self.assertTrue(any("not a statistical model" in t for t in result["summary"]))
        self.assertIsNone(result["estimated_home_run_probability"])
        self.assertIsNone(result["estimated_relief_appearance_probability"])
        self.assertIsNone(result["expected_value"])
        self.assertFalse(result["wager_executed"])

    def test_explicit_manual_candidates_preserve_existing_behavior(self):
        result = auto_bullpen_matchup(849831, 10001, "away", manual_reliever_ids=[30001],
                                     auto_select=False, reader=fixture())
        self.assertFalse(result["auto_bullpen_enabled"])
        self.assertIsNone(result["auto_bullpen_discovery"])
        self.assertEqual(result["reliever_ids_analyzed"], [30001])

    def test_no_recent_verified_relief_history_does_not_invent_candidates(self):
        r=fixture()
        r.rows["schedule"]={"dates":[]}
        result=auto_bullpen_matchup(849831, 10001, "away", reader=r)
        self.assertEqual(result["reliever_ids_analyzed"], [])
        self.assertTrue(any("could be verified" in t for t in result["summary"]))

    def test_manual_and_auto_cannot_be_mixed(self):
        with self.assertRaisesRegex(ValueError, "not both"):
            auto_bullpen_matchup(849831, 10001, "away",
                                manual_reliever_ids=[30001], auto_select=True, reader=fixture())

    def test_changed_starter_or_start_time_rejected_without_report(self):
        import sports_mlb_auto_bullpen as module
        actual = module.collect_recent_relief_candidates
        def altered(*args, **kwargs):
            r=actual(*args, **kwargs)
            r["probable_starter_id"]=99999
            return r
        with patch.object(module, "collect_recent_relief_candidates", side_effect=altered):
            with self.assertRaisesRegex(ValueError,"changed"):
                auto_bullpen_matchup(849831, 10001, "away", reader=fixture())


if __name__=="__main__":
    unittest.main()
