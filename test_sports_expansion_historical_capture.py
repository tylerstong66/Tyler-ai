"""Historical NCAA/NBA provider retrieval: separate seasons, raw receipts, no bets."""
import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path

import sports_expansion_historical_capture as h
import sports_expansion_observer as o

CLOCK=datetime(2026,10,17,12,tzinfo=timezone.utc)
PLAN={x:{"train":["2024-10-22"],"validation":["2025-10-21"]}
      for x in h.ORDER}


def payload():
    event={
        "id":"401000123",
        "date":"2024-10-22T23:00:00Z",
        "season":{"type":2},
        "status":{"type":{"state":"post","completed":True}},
        "competitions":[{"neutralSite":False,"competitors":[
            {"homeAway":"home","team":{"id":"100","displayName":"Home"},
             "score":"74"},
            {"homeAway":"away","team":{"id":"200","displayName":"Away"},
             "score":"71"}]}],
    }
    return json.dumps({"events":[event],"count":1}).encode()


class HistoricalCaptureTests(unittest.TestCase):
    def test_full_historical_dates_explicit_two_nonoverlapping_seasons(self):
        dates=h.dates_by_league()
        self.assertEqual(set(dates),{"NBA","NCAAF_FBS","NCAAM_D1"})
        for league,splits in dates.items():
            train=splits["train"];validation=splits["validation"]
            self.assertTrue(train[0].startswith("2024"))
            self.assertTrue(validation[0].startswith("2025"))
            self.assertLess(train[-1],validation[0])
            self.assertEqual(len(train),len(set(train)))
            self.assertEqual(len(validation),len(set(validation)))
            self.assertGreater(len(train),100)
            self.assertGreater(len(validation),100)

    def test_retained_three_league_source_receipts_and_repeat_is_idempotent(self):
        calls=[]
        def fetch(url):
            calls.append(url)
            return payload()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            out=h.capture(fetch,base=root,now=CLOCK,per_league=1,date_plan=PLAN)
            self.assertEqual(len(calls),3)
            self.assertFalse(out["live_forecasts_allowed"])
            self.assertFalse(out["training_allowed"])
            self.assertTrue(out["NO_BET"])
            self.assertEqual(out["historical_backfilled_forecasts"],0)
            self.assertEqual(out["validation_start_season"],2025)
            for sport in h.ORDER:
                snap=out["sport_day_status"][sport]
                self.assertEqual((snap["expected_source_dates"],snap["archived_source_dates"]),(2,1))
                self.assertFalse(snap["all_declared_dates_retrieved"])
                f=root/h.ROOT/"sources"/sport/"train"/"2024-10-22.json.gz"
                r=root/h.ROOT/"sources"/sport/"train"/"2024-10-22.receipt.json"
                original=gzip.decompress(f.read_bytes())
                meta=json.loads(r.read_text())
                self.assertEqual(original,payload())
                self.assertEqual(hashlib.sha256(original).hexdigest(),meta["original_response_sha256"])
                self.assertFalse(meta["independently_verified_official_scores"])
                self.assertTrue(meta["historical_results_are_not_pregame_forecasts"])
            second=h.capture(fetch,base=root,now=CLOCK,per_league=1,date_plan=PLAN)
            self.assertEqual(len(calls),6)
            for sport in h.ORDER:
                self.assertTrue(second["sport_day_status"][sport]["all_declared_dates_retrieved"])
                self.assertEqual(second["sport_day_status"][sport]["remaining_source_dates"],0)
            third=h.capture(fetch,base=root,now=CLOCK,per_league=1,date_plan=PLAN)
            self.assertEqual(len(calls),6)
            self.assertEqual(second,third)

    def test_source_failure_prevents_any_partial_new_batch(self):
        num=0
        def fetch(url):
            nonlocal num
            num+=1
            return payload() if num==1 else b'{"events":null}'
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with self.assertRaisesRegex(ValueError,"Missing or potentially truncated"):
                h.capture(fetch,base=root,now=CLOCK,date_plan=PLAN)
            self.assertFalse((root/h.ROOT).exists())

    def test_retained_original_sha_tampering_blocks_new_writes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            h.capture(lambda _:payload(),base=root,now=CLOCK,
                      per_league=1,date_plan=PLAN)
            file=root/h.ROOT/"sources"/"NBA"/"train"/"2024-10-22.json.gz"
            file.write_bytes(gzip.compress(payload()+b" ",mtime=0))
            with self.assertRaisesRegex(ValueError,"no longer match"):
                h.capture(lambda _:payload(),base=root,now=CLOCK,
                          per_league=2,date_plan=PLAN)
            self.assertFalse((root/h.ROOT/"sources"/"NBA"/"validation").exists())

    def test_budget_future_and_wrong_splits_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            for budget in (0,31,True):
                with self.subTest(budget=budget),self.assertRaisesRegex(ValueError,"budget"):
                    h.capture(lambda _:payload(),base=td,now=CLOCK,
                              per_league=budget,date_plan=PLAN)
            with self.assertRaisesRegex(ValueError,"cannot change"):
                h.capture(lambda _:payload(),base=td,now=CLOCK,
                          date_plan={"NBA":PLAN["NBA"]})
            future={key:{"train":["2027-11-03"],"validation":["2027-12-01"]}
                    for key in h.ORDER}
            with self.assertRaisesRegex(ValueError,"future-dated"):
                h.capture(lambda _:payload(),base=td,now=CLOCK,date_plan=future)


if __name__=="__main__":
    unittest.main()
