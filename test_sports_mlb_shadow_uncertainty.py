"""Game-cluster uncertainty thresholds and deterministic bootstrap tests."""
import math
import tempfile
import unittest
from pathlib import Path

from sports_mlb_shadow_uncertainty import (
    clustered_brier_difference, MIN_DISTINCT_GAMES, MIN_PLAYER_GAMES,
    BOOTSTRAP_REPLICATES
)
from sports_mlb_prop_prospective import freeze_pregame_hit_props, settle_frozen_hit_props, write_exclusive_json
from sports_mlb_prop_shadow_scoreboard import official_shadow_scoreboard
from test_sports_mlb_prop_prospective import OfficialReader, AFTER


class ClusterIntervals(unittest.TestCase):
    def test_seven_hitter_predictions_in_one_game_are_not_seven_independent_games(self):
        rows=[{"game_id":849810,"probability":0.59,"outcome":i%2} for i in range(7)]
        result=clustered_brier_difference(rows,reference_probability=0.60)
        self.assertEqual(result["eligible_player_games"],7)
        self.assertEqual(result["distinct_official_games_with_scored_players"],1)
        self.assertFalse(result["minimum_sample_gate_met"])
        self.assertIsNone(result["bootstrap_ci_lower"])
        self.assertEqual(result["bootstrap_replicates"],0)
        self.assertFalse(result["profitable_betting_edge_proven"])

    def test_at_least_30_games_and_150_player_games_produce_deterministic_interval(self):
        games=[]
        for game in range(40):
            for player in range(5):
                games.append({"game_id":800000+game,"probability":0.56+0.07*(player%3),
                              "outcome":int((game+player)%3!=0)})
        one=clustered_brier_difference(games,reference_probability=0.60)
        two=clustered_brier_difference(games,reference_probability=0.60)
        self.assertTrue(one["minimum_sample_gate_met"])
        self.assertEqual(one["eligible_player_games"],200)
        self.assertEqual(one["distinct_official_games_with_scored_players"],40)
        self.assertEqual(one["bootstrap_replicates"],BOOTSTRAP_REPLICATES)
        self.assertEqual(one["bootstrap_ci_lower"],two["bootstrap_ci_lower"])
        self.assertEqual(one["bootstrap_ci_upper"],two["bootstrap_ci_upper"])
        self.assertLessEqual(one["bootstrap_ci_lower"],one["bootstrap_ci_upper"])
        self.assertFalse(one["profitable_betting_edge_proven"])
        self.assertFalse(one["prospective_publication_attested"])

    def test_30_games_but_too_few_player_games_stays_descriptive(self):
        games=[{"game_id":100+i,"probability":0.09,"outcome":i%17==0}
               for i in range(MIN_DISTINCT_GAMES)]
        out=clustered_brier_difference(games,reference_probability=0.08)
        self.assertEqual(out["eligible_player_games"],MIN_DISTINCT_GAMES)
        self.assertFalse(out["minimum_sample_gate_met"])
        self.assertIsNone(out["interval_excludes_zero_in_model_favor"])

    def test_invalid_game_or_probability_rejected(self):
        for sample in (
            [{"game_id":0,"probability":0.3,"outcome":1}],
            [{"game_id":True,"probability":0.3,"outcome":1}],
            [{"game_id":100,"probability":1.0,"outcome":1}],
            [{"game_id":100,"probability":float("nan"),"outcome":1}],
            [{"game_id":100,"probability":0.3,"outcome":True}],
        ):
            with self.subTest(sample=sample),self.assertRaises(ValueError):
                clustered_brier_difference(sample,reference_probability=0.60)
        with self.assertRaises(ValueError):
            clustered_brier_difference([],reference_probability=-1)

    def test_actual_sealed_settlement_reports_sample_gate_and_one_game(self):
        with tempfile.TemporaryDirectory() as folder:
            reader=OfficialReader()
            frozen=freeze_pregame_hit_props(849810,683734,"away",reader=reader)
            write_exclusive_json(Path(folder)/"predictions"/"849810_683734.json",frozen)
            reader.now=AFTER
            reader.final=True
            official=settle_frozen_hit_props(frozen,reader=reader)
            write_exclusive_json(Path(folder)/"settlements"/"849810_683734.json",official)
            result=official_shadow_scoreboard(folder)
            uncertainty=result["metrics"]["hit"]["game_cluster_uncertainty"]
            self.assertEqual(uncertainty["distinct_official_games_with_scored_players"],1)
            self.assertEqual(uncertainty["eligible_player_games"],1)
            self.assertFalse(uncertainty["minimum_sample_gate_met"])
            self.assertIsNone(uncertainty["bootstrap_ci_lower"])
            self.assertFalse(result["proven_betting_edge"])


if __name__=="__main__":
    unittest.main()
