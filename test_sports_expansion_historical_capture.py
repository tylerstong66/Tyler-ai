"""Historical NCAA/NBA provider retrieval: separate seasons, raw receipts, no bets."""
import gzip
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
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
    def test_direct_receipt_scope_rejects_before_any_archive_access(self):
        invalid = [('NBA/..', 'train', '2024-10-22'), ('NFL', 'train', '2024-10-22'),
                   ('NBA', '../train', '2024-10-22'), ('NBA', 'test', '2024-10-22'),
                   ('NBA', 'train', '../2024-10-22'), ('NBA', 'train', '/2024-10-22'),
                   ('NBA', 'train', '20241022'), ('NBA', 'train', '2024-02-30'),
                   ('NBA', 'train', None)]
        for sport, split, day in invalid:
            with self.subTest(sport=sport, split=split, day=day), patch.object(h, 'archive_path') as access:
                with self.assertRaisesRegex(ValueError, 'scope'):
                    h.verify_existing('.', sport, split, day, as_of=CLOCK)
                access.assert_not_called()

    def test_direct_receipt_observation_cutoff_requires_aware_clock(self):
        for clock in (CLOCK.replace(tzinfo=None), CLOCK.isoformat()):
            with self.subTest(clock=clock), patch.object(h, 'archive_path') as access:
                with self.assertRaisesRegex(ValueError, 'Aware'):
                    h.verify_existing('.', 'NBA', 'train', '2024-10-22', as_of=clock)
                access.assert_not_called()

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

    def test_compressed_expansion_and_truncation_fail_before_fetch_or_writes(self):
        for mode in ('bomb', 'truncated'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                h.capture(lambda _: payload(), base=root, now=CLOCK,
                          per_league=1, date_plan=PLAN)
                path = root/h.ROOT/'sources'/'NBA'/'train'/'2024-10-22.json.gz'
                blob = (gzip.compress(b'x' * 8_000_001, mtime=0) if mode == 'bomb'
                        else path.read_bytes()[:-6])
                path.write_bytes(blob)
                def no_fetch(url):
                    self.fail('Invalid original archive must block outbound fetch')
                with self.assertRaisesRegex(ValueError, 'exceeds maximum|Corrupt or incomplete'):
                    h.capture(no_fetch, base=root, now=CLOCK, date_plan=PLAN)
                self.assertEqual(path.read_bytes(), blob)
                self.assertFalse((root/h.ROOT/'sources'/'NBA'/'validation').exists())

    def test_modified_historical_research_guards_fail_closed(self):
        for key, value in (('actual_wagers', 1), ('actual_wagers', False),
                           ('promotion_allowed', True),
                           ('independently_verified_official_scores', True)):
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                h.capture(lambda _: payload(), base=root, now=CLOCK,
                          per_league=1, date_plan=PLAN)
                path = root/h.ROOT/'sources'/'NBA'/'train'/'2024-10-22.receipt.json'
                obj = json.loads(path.read_bytes()); obj[key] = value
                path.write_text(json.dumps(obj))
                with self.assertRaisesRegex(ValueError, 'safety metadata'):
                    h.capture(lambda _: self.fail('No network allowed'),
                              base=root, now=CLOCK, date_plan=PLAN)

    def test_new_historical_provider_json_rejects_duplicate_keys_and_nonfinite(self):
        valid = payload()
        for name, raw in (
            ('duplicate_events', b'{"events":[],"events":' +
             json.dumps(json.loads(valid)['events']).encode() + b',"count":1}'),
            ('nonfinite_metadata', valid[:-1] + b',"unexpected":NaN}'),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                calls = []
                def fetch(url):
                    calls.append(url)
                    return raw
                with self.assertRaisesRegex(ValueError, 'Duplicate key|Non-finite'):
                    h.capture(fetch, base=td, now=CLOCK, date_plan=PLAN)
                self.assertEqual(len(calls), 1)
                self.assertFalse((Path(td) / h.ROOT).exists())

    def test_rehashed_ambiguous_historical_original_blocks_replay_and_append(self):
        valid = payload()
        forged = (b'{"events":[],"events":' +
                  json.dumps(json.loads(valid)['events']).encode() + b',"count":1}')
        for sport in h.ORDER:
            with self.subTest(sport=sport), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                h.capture(lambda _: valid, base=root, now=CLOCK,
                          per_league=1, date_plan=PLAN)
                folder = root / h.ROOT / 'sources' / sport / 'train'
                archive = folder / '2024-10-22.json.gz'
                receipt = folder / '2024-10-22.receipt.json'
                archive.write_bytes(gzip.compress(forged, mtime=0))
                saved = json.loads(receipt.read_bytes())
                saved['original_response_sha256'] = hashlib.sha256(forged).hexdigest()
                receipt.write_text(json.dumps(saved))
                with self.assertRaisesRegex(ValueError, 'Duplicate key'):
                    h.verify_existing(root, sport, 'train', '2024-10-22', as_of=CLOCK)
                calls = []
                with self.assertRaisesRegex(ValueError, 'Duplicate key'):
                    h.capture(lambda url: (calls.append(url), valid)[1],
                              base=root, now=CLOCK, date_plan=PLAN)
                self.assertEqual(calls, [])
                self.assertFalse((root / h.ROOT / 'sources' / sport /
                                  'validation').exists())

    def test_ambiguous_receipt_json_is_not_accepted_as_valid_archive(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            h.capture(lambda _: payload(), base=root, now=CLOCK,
                      per_league=1, date_plan=PLAN)
            receipt = (root / h.ROOT / 'sources' / 'NBA' / 'train' /
                       '2024-10-22.receipt.json')
            original = receipt.read_bytes()
            receipt.write_bytes(original[:-1] + b',"NO_BET":true}')
            with self.assertRaisesRegex(ValueError, 'Duplicate key'):
                h.verify_existing(root, 'NBA', 'train', '2024-10-22', as_of=CLOCK)

    def test_default_budget_is_20_new_source_days_per_league(self):
        # Synthetic plan keeps the network call count deterministic.
        dates=[f"2024-10-{day:02d}" for day in range(1,22)]
        synthetic={sport:{"train":dates,"validation":["2025-10-21"]}
                   for sport in h.ORDER}
        called=[]
        def source(url):
            called.append(url)
            return payload()
        with tempfile.TemporaryDirectory() as td:
            result=h.capture(source,base=td,now=CLOCK,date_plan=synthetic)
            self.assertEqual(len(called),60)
            for sport in h.ORDER:
                self.assertEqual(result["sport_day_status"][sport]["archived_source_dates"],20)
                self.assertEqual(result["sport_day_status"][sport]["remaining_source_dates"],2)
            self.assertFalse(result["training_allowed"])
            self.assertEqual(result["historical_backfilled_forecasts"],0)

    def test_rejects_unplanned_source_file_before_contacting_provider(self):
        for rogue in ("extra_source", "orphan", "misplaced", "unlisted_date"):
            with self.subTest(rogue=rogue),tempfile.TemporaryDirectory() as td:
                root=Path(td)
                h.capture(lambda _:payload(),base=root,now=CLOCK,
                          per_league=1,date_plan=PLAN)
                parent=root/h.ROOT/"sources"/"NBA"/"train"
                if rogue=="extra_source":
                    (parent/"unexpected.log").write_text("not sealed evidence")
                elif rogue=="orphan":
                    (parent/"2024-10-23.json.gz").write_bytes(b"orphan")
                elif rogue=="misplaced":
                    bogus=root/h.ROOT/"sources"/"NBA"/"unknown"
                    bogus.mkdir()
                    (bogus/"2024-10-22.json.gz").write_bytes(b"not planned")
                elif rogue=="unlisted_date":
                    (parent/"2024-10-25.receipt.json").write_text("{}")
                calls=[]
                with self.assertRaisesRegex(ValueError,"Unknown or misplaced"):
                    h.capture(lambda url:(calls.append(url),payload())[1],
                              base=root,now=CLOCK,date_plan=PLAN)
                self.assertEqual(calls,[])

    def test_existing_future_dated_source_receipt_blocks_append(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            h.capture(lambda _:payload(),base=root,now=CLOCK,
                      per_league=1,date_plan=PLAN)
            r=root/h.ROOT/"sources"/"NBA"/"train"/"2024-10-22.receipt.json"
            receipt=json.loads(r.read_text())
            receipt["recorded_at_utc"]="2026-10-18T14:00:00+00:00"
            r.write_text(json.dumps(receipt))
            attempts=[]
            with self.assertRaisesRegex(ValueError,"future observation timestamp"):
                h.capture(lambda url:(attempts.append(url),payload())[1],
                          base=root,now=CLOCK,date_plan=PLAN)
            self.assertEqual(attempts,[])

    def test_rejects_overlapping_or_unsorted_source_season_dates(self):
        for kind in ("duplicate", "overlap", "reverse", "empty"):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                plan={league:{split:list(dates) for split,dates in PLAN[league].items()}
                      for league in h.ORDER}
                if kind=="duplicate":
                    plan["NBA"]["train"]*=2
                elif kind=="overlap":
                    plan["NBA"]["validation"]=["2024-10-22"]
                elif kind=="reverse":
                    plan["NBA"]["train"]=["2024-10-23","2024-10-22"]
                else:
                    plan["NBA"]["train"]=[]
                with self.assertRaises(ValueError):
                    h.capture(lambda _:payload(),base=td,now=CLOCK,date_plan=plan)
                self.assertFalse((Path(td)/h.ROOT).exists())

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
