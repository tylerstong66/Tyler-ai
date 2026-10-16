"""Scheduled no-wager settlement test: no updates to original frozen predictions."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from sports_mlb_prop_settlement_job import settle_ready_records
from sports_mlb_prop_prospective import freeze_pregame_hit_props, write_exclusive_json
from test_sports_mlb_prop_prospective import OfficialReader, AFTER


class SettlementScheduleTests(unittest.TestCase):
    def prepare(self,root):
        reader=OfficialReader()
        record=freeze_pregame_hit_props(849810,683734,"away",reader=reader)
        path=Path(root)/"predictions"/"849810_683734.json"
        write_exclusive_json(path,record)
        return reader,record,path

    def test_pending_uses_no_result_file_and_untouched_prediction(self):
        with tempfile.TemporaryDirectory() as d:
            reader,original,path=self.prepare(d)
            report=settle_ready_records(d,reader=reader)
            self.assertEqual(report["discovered"],1)
            self.assertEqual(report["pending"],1)
            self.assertEqual(report["settled"],0)
            self.assertFalse((Path(d)/"settlements"/path.name).exists())
            self.assertEqual(json.loads(path.read_text()),original)

    def test_postfirstpitch_not_final_stays_pending(self):
        with tempfile.TemporaryDirectory() as d:
            reader,original,path=self.prepare(d)
            reader.now=AFTER
            report=settle_ready_records(d,reader=reader)
            self.assertEqual((report["pending"],report["settled"]),(1,0))
            self.assertEqual(json.loads(path.read_text()),original)

    def test_verified_final_creates_separate_settlement_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            reader,original,path=self.prepare(d)
            reader.now=AFTER
            reader.final=True
            outcome=settle_ready_records(d,reader=reader)
            self.assertEqual(outcome["settled"],1)
            target=Path(d)/"settlements"/"849810_683734.json"
            saved=json.loads(target.read_text())
            self.assertEqual(saved["prediction_digest_sha256"],
                             original["record_digest_sha256"])
            self.assertEqual(saved["status"],"SETTLED_CONDITIONAL")
            self.assertEqual(json.loads(path.read_text()),original)
            again=settle_ready_records(d,reader=reader)
            self.assertEqual((again["settled"],again["already_settled"]),(0,1))
            self.assertEqual(json.loads(target.read_text()),saved)

    def test_missing_official_at_bats_remains_unsettled_and_retryable(self):
        with tempfile.TemporaryDirectory() as d:
            reader,original,path=self.prepare(d)
            reader.now=AFTER
            reader.final=True
            reader.omit_at_bats=True
            report=settle_ready_records(d,reader=reader)
            self.assertEqual((report["discovered"],report["settled"],
                              report["unresolved"]),(1,0,1))
            self.assertEqual(report["unresolved_files"][0]["hitter_id"],683734)
            self.assertFalse((Path(d)/"settlements"/path.name).exists())
            self.assertEqual(json.loads(path.read_text()),original)
            reader.omit_at_bats=False
            second=settle_ready_records(d,reader=reader)
            self.assertEqual((second["settled"],second["unresolved"]),(1,0))
            self.assertTrue((Path(d)/"settlements"/path.name).exists())
            self.assertEqual(json.loads(path.read_text()),original)

    def test_malformed_official_at_bats_still_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            reader,original,path=self.prepare(d)
            reader.now=AFTER
            reader.final=True
            reader.at_bats="4"
            with self.assertRaisesRegex(ValueError,"missing or invalid"):
                settle_ready_records(d,reader=reader)
            self.assertFalse((Path(d)/"settlements"/path.name).exists())

    def test_workflow_refreshes_only_readonly_scoreboard_after_final_commit(self):
        yaml=(Path(__file__).parent/".github/workflows/mlb_hit_shadow_auto_settlement.yml").read_text()
        first=yaml.index("Commit only newly created official final settlement files")
        refresh=yaml.index("Refresh read-only scoreboard after final-settlement commit")
        self.assertLess(first,refresh)
        self.assertIn("python sports_mlb_prop_scoreboard_feed.py",yaml)
        self.assertIn("PUBLIC_SCOREBOARD_ONLY_NO_WAGERS",yaml)
        self.assertIn("benchmarks/mlb_hitter_props_shadow_v1/scoreboard.latest.json",yaml)

    def test_renamed_or_corrupted_frozen_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            reader,original,path=self.prepare(d)
            data=json.loads(path.read_text())
            data["conditional_at_bat_probabilities"]["hit"]=0.999
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"digest"):
                settle_ready_records(d,reader=reader)
        with tempfile.TemporaryDirectory() as d:
            reader,original,path=self.prepare(d)
            path.rename(path.with_name("malformed.json"))
            with self.assertRaisesRegex(ValueError,"naming"):
                settle_ready_records(d,reader=reader)

    def test_no_prediction_directory_has_no_side_effect(self):
        with tempfile.TemporaryDirectory() as d:
            outcome=settle_ready_records(d,reader=OfficialReader())
            self.assertEqual(outcome["discovered"],0)
            self.assertEqual(outcome["settled"],0)
            self.assertFalse((Path(d)/"settlements").exists())


if __name__=="__main__":
    unittest.main()
