"""No-network scoreboard verification for official frozen MLB hitter shadows."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from sports_mlb_prop_shadow_scoreboard import official_shadow_scoreboard
from sports_mlb_prop_prospective import (
    _seal, freeze_pregame_hit_props, settle_frozen_hit_props, write_exclusive_json
)
from test_sports_mlb_prop_prospective import OfficialReader, AFTER


class ScoreboardTests(unittest.TestCase):
    def capture(self, root):
        reader=OfficialReader()
        frozen=freeze_pregame_hit_props(849810,683734,"away",reader=reader)
        path=Path(root)/"predictions"/"849810_683734.json"
        write_exclusive_json(path,frozen)
        return reader,frozen,path

    def test_pending_does_not_claim_loss_or_edge(self):
        with tempfile.TemporaryDirectory() as d:
            reader,record,_=self.capture(d)
            result=official_shadow_scoreboard(d)
            self.assertEqual(result["status"],"PROSPECTIVE_FREEZE_SCORING_DIAGNOSTIC_NO_BET")
            self.assertEqual(result["pending"],1)
            self.assertEqual(result["scored"],0)
            self.assertEqual(result["distinct_official_game_ids"],1)
            self.assertIsNone(result["metrics"]["hit"]["brier"])
            self.assertFalse(result["proven_betting_edge"])
            self.assertTrue(result["no_wagers"])

    def test_final_report_grades_same_frozen_probabilities(self):
        with tempfile.TemporaryDirectory() as d:
            reader,record,_=self.capture(d)
            reader.now=AFTER
            reader.final=True
            official=settle_frozen_hit_props(record,reader=reader)
            write_exclusive_json(Path(d)/"settlements"/"849810_683734.json",official)
            report=official_shadow_scoreboard(d)
            self.assertEqual(report["scored"],1)
            self.assertEqual(report["pending"],0)
            self.assertEqual(report["distinct_official_game_ids_with_eligible_settlements"],1)
            self.assertEqual(report["metrics"]["hit"]["eligible_player_games"],1)
            self.assertIsNotNone(report["metrics"]["hit"]["brier"])
            self.assertFalse(report["metrics"]["hit"]["predictive_edge_established"])
            self.assertFalse(report["market_odds_available"])

    def test_zero_ab_final_ineligible_does_not_degrade_model(self):
        with tempfile.TemporaryDirectory() as d:
            reader,record,_=self.capture(d)
            reader.now=AFTER
            reader.final=True
            reader.at_bats=0
            settlement=settle_frozen_hit_props(record,reader=reader)
            write_exclusive_json(Path(d)/"settlements"/"849810_683734.json",settlement)
            result=official_shadow_scoreboard(d)
            self.assertEqual(result["ineligible"],1)
            self.assertEqual(result["scored"],0)
            self.assertEqual(result["pending"],0)
            self.assertIsNone(result["metrics"]["hr"]["model_improved_over_fixed_reference"])

    def test_tampered_prediction_and_mismatched_final_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            reader,record,path=self.capture(d)
            bad=json.loads(path.read_text())
            bad["conditional_at_bat_probabilities"]["hit"]=0.99
            path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,"digest"):
                official_shadow_scoreboard(d)
        with tempfile.TemporaryDirectory() as d:
            reader,record,_=self.capture(d)
            reader.now=AFTER
            reader.final=True
            actual=settle_frozen_hit_props(record,reader=reader)
            bad=dict(actual)
            bad.pop("record_digest_sha256")
            bad["prediction_digest_sha256"]="0"*64
            write_exclusive_json(Path(d)/"settlements"/"849810_683734.json",_seal(bad))
            with self.assertRaisesRegex(ValueError,"digest"):
                official_shadow_scoreboard(d)

    def test_multiple_player_forecasts_one_distinct_event(self):
        with tempfile.TemporaryDirectory() as d:
            reader,one,path=self.capture(d)
            core=dict(one);core.pop("record_digest_sha256")
            core["hitter_id"]=123456
            core["hitter_name"]="Another synthetic hitter"
            second=_seal(core)
            write_exclusive_json(Path(d)/"predictions"/"849810_123456.json",second)
            report=official_shadow_scoreboard(d)
            self.assertEqual(report["frozen_player_game_forecasts"],2)
            self.assertEqual(report["distinct_official_game_ids"],1)
            self.assertEqual(report["pending"],2)

    def test_empty_directory_reports_no_enrolled_games(self):
        with tempfile.TemporaryDirectory() as d:
            report=official_shadow_scoreboard(d)
            self.assertEqual(report["frozen_player_game_forecasts"],0)
            self.assertTrue(report["no_wagers"])


if __name__=="__main__":
    unittest.main()
