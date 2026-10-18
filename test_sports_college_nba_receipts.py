"""Original ESPN source receipt replay and tamper regression tests."""
import gzip
import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
import sports_expansion_observer as obs
import sports_college_nba_receipts as receipts

class SourceReceiptTests(unittest.TestCase):
    def seed(self,root):
        def fetch(url):
            if "football/college-football" not in url:
                return b'{"count":0,"events":[]}'
            return json.dumps({"count":1,"events":[{
                "id":"401234567","date":"2026-10-18T19:00:00Z",
                "season":{"type":2},
                "status":{"type":{"state":"pre","completed":False}},
                "competitions":[{"neutralSite":False,"competitors":[
                    {"homeAway":"home","team":{"id":"1","displayName":"Home"}},
                    {"homeAway":"away","team":{"id":"2","displayName":"Away"}}
                ]}]
            }]}).encode()
        obs.capture(fetch,base=root,now=datetime(2026,10,18,12,tzinfo=timezone.utc),days_ahead=0)
        return next((root/obs.ROOT/"captures").iterdir())

    def test_replayed_provider_receipt_never_claims_independent_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=self.seed(Path(tmp))
            r=receipts.verify_espn_receipt(folder,"NCAAF_FBS","401234567")
            self.assertTrue(r["source_archive_sha256_verified"])
            self.assertFalse(r["independent_official_final_verified"])
            self.assertFalse(r["eligible_for_historical_evaluation"])

    def test_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=self.seed(Path(tmp))
            archive=folder/"NCAAF_FBS_2026-10-18.json.gz"
            archive.write_bytes(gzip.compress(b'{"events":[]}',mtime=0))
            with self.assertRaisesRegex(ValueError,"digest mismatch"):
                receipts.verify_espn_receipt(folder,"NCAAF_FBS","401234567")

    def test_expansion_bomb_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=self.seed(Path(tmp))
            archive=folder/"NCAAF_FBS_2026-10-18.json.gz"
            archive.write_bytes(gzip.compress(b'x'*8_000_001,mtime=0))
            with self.assertRaisesRegex(ValueError,"exceeds maximum"):
                receipts.verify_espn_receipt(folder,"NCAAF_FBS","401234567")

    def test_missing_game_and_unsupported_league(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=self.seed(Path(tmp))
            with self.assertRaisesRegex(ValueError,"absent"):
                receipts.verify_espn_receipt(folder,"NCAAF_FBS","999")
            with self.assertRaisesRegex(ValueError,"Unsupported"):
                receipts.verify_espn_receipt(folder,"NFL","401234567")

if __name__=="__main__":
    unittest.main()
