"""Transparent weighted-cohort diagnostics and identity constraints."""
import copy
import unittest
from sports_mlb_prop_cohort import summarize_hitter_cohort
from test_sports_mlb_hit_prop_shadow import sample


class CohortTests(unittest.TestCase):
    def test_weighted_hitter_games_and_no_proven_edge(self):
        one=sample()
        two=copy.deepcopy(sample())
        for row in two:
            row["hitter_id"]=99999
            row["game_id"]+=400000
        report=summarize_hitter_cohort([
            {"hitter_id":683734,"hitter_name":"Test Hitter A","game_logs":one},
            {"hitter_id":99999,"hitter_name":"Test Hitter B","game_logs":two},
        ],season=2026)
        self.assertEqual(report["hitter_count"],2)
        self.assertEqual(report["pooled"]["hit"]["eligible_player_games"],36)
        self.assertEqual(report["pooled"]["hr"]["eligible_player_games"],36)
        self.assertFalse(report["independently_frozen_prospective"])
        self.assertFalse(report["model_approved_for_sportsbook_value"])
        self.assertFalse(report["wager_execution"])
        self.assertFalse(report["pooled"]["hit"]["improvement_proven"])

    def test_invalid_repeated_foreign_identity_and_empty_cohort_rejected(self):
        records=[{"hitter_id":683734,"hitter_name":"A","game_logs":sample()}]
        with self.assertRaisesRegex(ValueError,"preregistered"):
            summarize_hitter_cohort([],season=2026)
        with self.assertRaisesRegex(ValueError,"repeated"):
            summarize_hitter_cohort(records+records,season=2026)
        with self.assertRaisesRegex(ValueError,"foreign"):
            summarize_hitter_cohort([{"hitter_id":88888,"hitter_name":"Unknown","game_logs":sample()}],season=2026)

    def test_missing_game_history_does_not_fabricate_scores(self):
        out=summarize_hitter_cohort([{"hitter_id":1001,"hitter_name":"No Past Games","game_logs":[]}],season=2026)
        self.assertIsNone(out["pooled"]["hit"]["model_brier"])
        self.assertEqual(out["pooled"]["hit"]["eligible_player_games"],0)


if __name__=="__main__":
    unittest.main()
