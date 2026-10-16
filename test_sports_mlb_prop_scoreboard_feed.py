"""Offline public scoreboard publishing/reader safeguards without network or wagers."""
import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sports_mlb_prop_scoreboard_feed as feed
import sports_mlb_prop_scoreboard_reader as reader

CLOCK="2026-10-15T20:00:00+00:00"


def benchmark():
    return {
        "status":"PROSPECTIVE_FREEZE_SCORING_DIAGNOSTIC_NO_BET",
        "report_created_utc":CLOCK,
        "frozen_player_game_forecasts":7,
        "distinct_official_game_ids":1,
        "pending":7,"scored":0,"ineligible":0,
        "metrics":{"hit":{"brier":None},"hr":{"brier":None}},
        "per_game":{"849810":{"predictions":7,"pending":7,"scored":0,"ineligible":0}},
        "no_wagers":True,
        "proven_betting_edge":False,
        "model_is_calibrated":False,
        "market_odds_available":False,
    }


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        subprocess.run(["git","init","-q"],cwd=self.root,check=True)
        subprocess.run(["git","-c","user.name=Test","-c","user.email=test@example.com",
                        "commit","--allow-empty","-qm","synthetic repository"],
                       cwd=self.root,check=True)

    def test_publish_readonly_then_unchanged_is_idempotent(self):
        with patch.object(feed,"official_shadow_scoreboard",return_value=benchmark()):
            r=feed.publish_readonly_shadow_feed(repository=self.root,
                                                now=CLOCK)
        self.assertEqual(r["status"],"CREATED_OR_UPDATED")
        target=self.root/feed.FEED_RELATIVE
        content=target.read_bytes()
        saved=json.loads(content)
        self.assertEqual(saved["benchmark"]["pending"],7)
        self.assertTrue(saved["no_wagers"])
        with patch.object(feed,"official_shadow_scoreboard",return_value=benchmark()):
            second=feed.publish_readonly_shadow_feed(repository=self.root,
                now="2026-10-15T21:00:00Z")
        self.assertEqual(second["status"],"UNCHANGED")
        self.assertEqual(target.read_bytes(),content)

    def test_unchanged_saved_data_refreshes_only_feed_heartbeat_after_two_hours(self):
        with patch.object(feed,"official_shadow_scoreboard",return_value=benchmark()):
            original=feed.publish_readonly_shadow_feed(repository=self.root,now=CLOCK)
        target=self.root/feed.FEED_RELATIVE
        before=json.loads(target.read_text())
        with patch.object(feed,"official_shadow_scoreboard",return_value=benchmark()):
            refreshed=feed.publish_readonly_shadow_feed(
                repository=self.root,now="2026-10-15T23:00:00Z")
        after=json.loads(target.read_text())
        self.assertEqual(refreshed["status"],"HEARTBEAT_REFRESHED")
        self.assertEqual(after["benchmark_sha256"],before["benchmark_sha256"])
        self.assertEqual(after["benchmark"],before["benchmark"])
        self.assertEqual(after["benchmark_last_changed_at_utc"],CLOCK)
        self.assertEqual(after["published_at_utc"],"2026-10-15T23:00:00+00:00")
        self.assertEqual(after["source_refresh_kind"],"unchanged_saved_evidence_heartbeat")
        self.assertTrue(any("not a fresh official MLB API check" in line
                            for line in after["limitations"]))
        heartbeat_bytes=target.read_bytes()
        with patch.object(feed,"official_shadow_scoreboard",return_value=benchmark()):
            again=feed.publish_readonly_shadow_feed(
                repository=self.root,now="2026-10-15T23:10:00Z")
        self.assertEqual(again["status"],"UNCHANGED")
        self.assertEqual(target.read_bytes(),heartbeat_bytes)

    def test_rejects_backwards_clock_even_with_identical_report(self):
        with patch.object(feed,"official_shadow_scoreboard",return_value=benchmark()):
            feed.publish_readonly_shadow_feed(repository=self.root,now=CLOCK)
        with patch.object(feed,"official_shadow_scoreboard",return_value=benchmark()):
            with self.assertRaisesRegex(ValueError,"in the future"):
                feed.publish_readonly_shadow_feed(
                    repository=self.root,now="2026-10-15T19:00:00Z")

    def test_update_after_settlement_makes_new_snapshot_not_forecast_change(self):
        report=benchmark()
        with patch.object(feed,"official_shadow_scoreboard",return_value=report):
            feed.publish_readonly_shadow_feed(repository=self.root,now=CLOCK)
        altered=copy.deepcopy(report)
        altered["pending"]=6
        altered["scored"]=1
        with patch.object(feed,"official_shadow_scoreboard",return_value=altered):
            result=feed.publish_readonly_shadow_feed(repository=self.root,
                    now="2026-10-15T21:00:00Z")
        self.assertEqual(result["status"],"CREATED_OR_UPDATED")
        new=json.loads((self.root/feed.FEED_RELATIVE).read_text())
        self.assertEqual((new["benchmark"]["pending"],new["benchmark"]["scored"]),(6,1))

    def test_no_wager_violation_blocks_publication(self):
        broken=benchmark()
        broken["no_wagers"]=False
        with patch.object(feed,"official_shadow_scoreboard",return_value=broken):
            with self.assertRaisesRegex(ValueError,"no-wager"):
                feed.publish_readonly_shadow_feed(repository=self.root,now=CLOCK)


class FakeResponse:
    status_code=200
    def __init__(self,payload):
        self.content=json.dumps(payload).encode("utf-8")
        self.url=reader.FEED_URL
    def json(self):
        return json.loads(self.content)


def make_snapshot():
    stable={k:v for k,v in benchmark().items() if k!="report_created_utc"}
    return {
        "schema":feed.FEED_SCHEMA,
        "published_at_utc":CLOCK,
        "source_git_revision":"0"*40,
        "source":"public_github_main_scheduled_snapshot",
        "benchmark_sha256":hashlib.sha256(feed._canonical(stable).encode()).hexdigest(),
        "benchmark":stable,
        "no_wagers":True,
        "limitations":["Not a wagering model."],
    }


class ReaderTests(unittest.TestCase):
    def test_read_valid_published_snapshot_with_age_and_zero_scores(self):
        snap=make_snapshot()
        seen=[]
        def remote(url,**kwargs):
            seen.append((url,kwargs))
            return FakeResponse(snap)
        result=reader.load_published_shadow_scoreboard(
            get=remote,clock=lambda:"2026-10-15T20:30:00Z")
        self.assertEqual(result["pending"],7)
        self.assertEqual(result["scored"],0)
        self.assertFalse(result["may_be_stale"])
        self.assertTrue(result["no_wagers"])
        self.assertEqual(result["source"],reader.FEED_URL)
        self.assertFalse(seen[0][1]["allow_redirects"])
        self.assertEqual(seen[0][1]["timeout"],12)

    def test_heartbeat_makes_feed_recent_without_claiming_new_benchmark_evidence(self):
        snap=make_snapshot()
        snap["published_at_utc"]="2026-10-16T03:00:00Z"
        snap["benchmark_last_changed_at_utc"]=CLOCK
        snap["source_refresh_kind"]="unchanged_saved_evidence_heartbeat"
        result=reader.load_published_shadow_scoreboard(
            get=lambda *args,**kwargs:FakeResponse(snap),
            clock=lambda:"2026-10-16T04:00:00Z")
        self.assertEqual(result["snapshot_age_hours"],1)
        self.assertEqual(result["benchmark_age_hours"],8)
        self.assertFalse(result["may_be_stale"])
        self.assertFalse(result["refresh_proves_new_official_MLB_data"])
        self.assertEqual(result["refresh_kind"],"unchanged_saved_evidence_heartbeat")
        snap["benchmark_last_changed_at_utc"]="2026-10-16T06:00:00Z"
        with self.assertRaisesRegex(ValueError,"change timestamp exceeds"):
            reader.load_published_shadow_scoreboard(
                get=lambda *args,**kwargs:FakeResponse(snap),
                clock=lambda:"2026-10-16T07:00:00Z")

    def test_wrong_hash_ignored_source_and_inconsistent_counts_refused(self):
        for change in ("hash","source","count","wagers"):
            snap=make_snapshot()
            if change=="hash":
                snap["benchmark_sha256"]="f"*64
            elif change=="source":
                snap["source"]="another_host"
            elif change=="count":
                snap["benchmark"]["pending"]=123
                snap["benchmark_sha256"]=hashlib.sha256(
                    feed._canonical(snap["benchmark"]).encode()).hexdigest()
            else:
                snap["no_wagers"]=False
            with self.subTest(change=change),self.assertRaises(ValueError):
                reader.load_published_shadow_scoreboard(
                    get=lambda *a,**kw:FakeResponse(snap),clock=lambda:CLOCK)

    def test_pending_hitter_identity_examples_and_truncation_validation(self):
        snap=make_snapshot()
        snap["benchmark"]["pending_player_game_examples"]=[
            {"game_id":"849810","hitter_id":"683734",
             "hitter_name":"Andrew Vaughn",
             "scheduled_first_pitch_utc":CLOCK,
             "status":"NO_SEALED_OFFICIAL_SETTLEMENT_YET"}
        ]
        snap["benchmark"]["pending_examples_truncated"]=True
        def refresh():
            snap["benchmark_sha256"]=hashlib.sha256(
                feed._canonical(snap["benchmark"]).encode()).hexdigest()
        refresh()
        out=reader.load_published_shadow_scoreboard(
            get=lambda *a,**kw:FakeResponse(snap),clock=lambda:CLOCK)
        self.assertTrue(out["pending_player_ids_available"])
        self.assertEqual(out["pending_player_game_examples"][0]["hitter_id"],"683734")
        self.assertTrue(out["pending_examples_truncated"])
        snap["benchmark"]["pending_examples_truncated"]=False
        refresh()
        with self.assertRaisesRegex(ValueError,"count is inconsistent"):
            reader.load_published_shadow_scoreboard(
                get=lambda *a,**kw:FakeResponse(snap),clock=lambda:CLOCK)
        snap["benchmark"]["pending_examples_truncated"]=True
        snap["benchmark"]["pending_player_game_examples"][0]["hitter_id"]="fake"
        refresh()
        with self.assertRaisesRegex(ValueError,"Invalid pending hitter identity"):
            reader.load_published_shadow_scoreboard(
                get=lambda *a,**kw:FakeResponse(snap),clock=lambda:CLOCK)

    def test_pending_saved_first_pitch_audit_separates_future_from_elapsed(self):
        snap=make_snapshot()
        snap["published_at_utc"]="2026-10-16T21:55:00Z"
        snap["benchmark"]["pending_player_game_examples"]=[
            {"game_id":"849810","hitter_id":"683734",
             "hitter_name":"Andrew Vaughn",
             "scheduled_first_pitch_utc":"2026-10-16T00:00:00Z",
             "status":"NO_SEALED_OFFICIAL_SETTLEMENT_YET"},
            {"game_id":"849817","hitter_id":"608070",
             "hitter_name":"José Ramírez",
             "scheduled_first_pitch_utc":"2026-10-17T00:00:00Z",
             "status":"NO_SEALED_OFFICIAL_SETTLEMENT_YET"},
        ]
        snap["benchmark"]["pending_examples_truncated"]=True
        snap["benchmark_sha256"]=hashlib.sha256(
            feed._canonical(snap["benchmark"]).encode()).hexdigest()
        out=reader.load_published_shadow_scoreboard(
            get=lambda *a,**kw:FakeResponse(snap),
            clock=lambda:"2026-10-16T21:56:00Z")
        timing=out["pending_saved_schedule_audit"]
        self.assertEqual((timing["shown"],timing["unshown_pending"]),(2,5))
        self.assertEqual((timing["scheduled_first_pitch_future"],
                          timing["scheduled_first_pitch_reached"]),(1,1))
        self.assertEqual(timing["events"][0]["time_state"],
                         "SAVED_FIRST_PITCH_REACHED_UNSETTLED")
        self.assertEqual(timing["events"][1]["time_state"],"SAVED_FIRST_PITCH_FUTURE")
        self.assertFalse(timing["official_game_state_verified"])
        self.assertTrue(all(v["no_verified_player_outcome"] for v in timing["events"]))
        next_clock=reader.load_published_shadow_scoreboard(
            get=lambda *a,**kw:FakeResponse(snap),
            clock=lambda:"2026-10-17T01:00:00Z")["pending_saved_schedule_audit"]
        self.assertEqual(next_clock["scheduled_first_pitch_future"],0)
        self.assertEqual(next_clock["scheduled_first_pitch_reached"],2)

    def test_pending_scheduled_first_pitch_malformed_fails_closed(self):
        snap=make_snapshot()
        snap["benchmark"]["pending_player_game_examples"]=[
            {"game_id":"849817","hitter_id":"608070",
             "scheduled_first_pitch_utc":"not-a-date",
             "status":"NO_SEALED_OFFICIAL_SETTLEMENT_YET"}]
        snap["benchmark"]["pending_examples_truncated"]=True
        snap["benchmark_sha256"]=hashlib.sha256(
            feed._canonical(snap["benchmark"]).encode()).hexdigest()
        with self.assertRaisesRegex(ValueError,"Invalid saved first pitch"):
            reader.load_published_shadow_scoreboard(
                get=lambda *a,**kw:FakeResponse(snap),clock=lambda:CLOCK)

    def test_legacy_pending_feed_does_not_claim_timing_coverage(self):
        snap=make_snapshot()
        out=reader.load_published_shadow_scoreboard(
            get=lambda *a,**kw:FakeResponse(snap),clock=lambda:CLOCK)
        audit=out["pending_saved_schedule_audit"]
        self.assertFalse(audit["available"])
        self.assertEqual(audit["unshown_pending"],7)
        self.assertIsNone(audit["scheduled_first_pitch_future"])
        self.assertIsNone(audit["scheduled_first_pitch_reached"])

    def test_old_snapshot_warns_and_missing_feed_fails_closed(self):
        valid=make_snapshot()
        out=reader.load_published_shadow_scoreboard(
            get=lambda *a,**kw:FakeResponse(valid),
            clock=lambda:"2026-10-16T03:00:00Z")
        self.assertTrue(out["may_be_stale"])
        fail=FakeResponse(valid)
        fail.status_code=404
        with self.assertRaisesRegex(RuntimeError,"unavailable"):
            reader.load_published_shadow_scoreboard(
                get=lambda *a,**kw:fail,clock=lambda:CLOCK)


if __name__=="__main__":
    unittest.main()
