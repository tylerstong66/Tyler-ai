"""Replayed NBA schedule receipts must remain research-only."""
import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
import sports_expansion_observer as observer
import sports_nba_official_schedule_audit as nba
import sports_nba_schedule_receipts as receipts
from test_sports_nba_official_schedule_audit import official_games,espn_event

class ReceiptReplayTests(unittest.TestCase):
    def seed(self,root):
        def fetch(url):
            if "basketball/nba" in url and "dates=20261020" in url:
                return json.dumps({"events":[espn_event()],"count":1}).encode()
            return b'{"events":[],"count":0}'
        observer.capture(fetch,base=root,now=datetime(2026,10,17,12,tzinfo=timezone.utc),days_ahead=3)
        nba.run(lambda _:official_games(),base=root,now=datetime(2026,10,17,13,tzinfo=timezone.utc))
        return "20261017T130000000000Z"

    def test_replay_never_authorizes_grading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stamp=self.seed(root)
            out=receipts.verify(root,stamp)
            self.assertTrue(out["schedule_crosswalk_replayed"])
            self.assertEqual(out["strict_schedule_correlated"],1)
            self.assertFalse(out["independent_official_final_verified"])
            self.assertFalse(out["eligible_for_historical_evaluation"])

    def test_modified_official_schedule_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stamp=self.seed(root)
            target=root/nba.ROOT/"captures"/stamp/"nba_schedule.json.gz"
            target.write_bytes(b"corrupt")
            with self.assertRaises((ValueError,EOFError,OSError)):
                receipts.verify(root,stamp)

    def test_forged_crosswalk_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);stamp=self.seed(root)
            target=root/nba.ROOT/"captures"/stamp/"manifest.json"
            obj=json.loads(target.read_text())
            obj["report"]["strict_schedule_correlated"]=999
            target.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"differs"):
                receipts.verify(root,stamp)

    def test_invalid_capture_name_rejected(self):
        with self.assertRaisesRegex(ValueError,"identifier"):
            receipts.verify(".", "../escape")

if __name__=="__main__":
    unittest.main()
