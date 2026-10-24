"""Replayed NBA schedule receipts must remain research-only."""
import json
import hashlib
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

    def test_direct_replay_rejects_impossible_receipt_chronology(self):
        for fault in ('nba_clock', 'espn_clock', 'espn_after_nba'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as td:
                root=Path(td); stamp=self.seed(root)
                folder=root/nba.ROOT/'captures'/stamp
                path=folder/'manifest.json'; saved=json.loads(path.read_bytes())
                if fault=='espn_clock':
                    linked=root/observer.ROOT/'captures'/saved['espn_capture']/'manifest.json'
                    manifest=json.loads(linked.read_bytes())
                    manifest['recorded_at_utc']='2000-01-01T00:00:00Z'
                    linked.write_text(json.dumps(manifest))
                    saved['espn_manifest_sha256']=hashlib.sha256(linked.read_bytes()).hexdigest()
                elif fault=='espn_after_nba':
                    stamp='20261017T110000000000Z'
                    moved=folder.parent/stamp;folder.rename(moved)
                    path=moved/'manifest.json';saved['created_at_utc']='2026-10-17T11:00:00Z'
                else:
                    saved['created_at_utc']='2000-01-01T00:00:00Z'
                path.write_text(json.dumps(saved))
                with self.assertRaises(ValueError):
                    receipts.verify(root,stamp)

    def test_receipt_json_and_no_bet_guards_cannot_be_forged(self):
        for location in ('nba', 'espn'):
            for fault in ('duplicate_guard', 'nonfinite', 'boolean_wager', 'float_wager'):
                with self.subTest(location=location, fault=fault), tempfile.TemporaryDirectory() as td:
                    root=Path(td); stamp=self.seed(root)
                    path=root/nba.ROOT/'captures'/stamp/'manifest.json'
                    saved=json.loads(path.read_bytes())
                    target=(path if location=='nba' else
                            root/observer.ROOT/'captures'/saved['espn_capture']/'manifest.json')
                    raw=target.read_bytes(); data=json.loads(raw)
                    if fault=='duplicate_guard': mutated=b'{"NO_BET":false,'+raw[1:]
                    elif fault=='nonfinite': mutated=b'{"extra":NaN,'+raw[1:]
                    else:
                        data['actual_wagers']=False if fault=='boolean_wager' else 0.0
                        mutated=json.dumps(data).encode()
                    target.write_bytes(mutated)
                    if location=='espn':
                        saved['espn_manifest_sha256']=hashlib.sha256(mutated).hexdigest()
                        path.write_text(json.dumps(saved))
                    with self.assertRaises(ValueError): receipts.verify(root,stamp)

    def test_nba_v1_receipt_cannot_assert_promotion_or_foreign_endpoint(self):
        for field, value in (('promotion_allowed', True),
                             ('nba_official_source_url', 'https://example.org/fake')):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                root=Path(td); stamp=self.seed(root)
                path=root/nba.ROOT/'captures'/stamp/'manifest.json'
                saved=json.loads(path.read_bytes());saved[field]=value
                path.write_text(json.dumps(saved))
                with self.assertRaises(ValueError): receipts.verify(root,stamp)

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
