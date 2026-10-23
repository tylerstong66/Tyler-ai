"""Provider-only college/NBA expansion with adversarial source tests."""
import gzip
import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sports_expansion_observer as obs


def event(game_id, league, *, stage=2, state="pre",
          completed=False, kickoff="2026-10-20T19:00:00Z",
          home_score="102", away_score="98"):
    return {
        "id":str(game_id),
        "date":kickoff,
        "season":{"type":stage},
        "status":{"type":{"state":state,"completed":completed}},
        "competitions":[{
            "neutralSite":False,
            "competitors":[
                {"homeAway":"home","team":{"id":"101","displayName":"Home"},
                 "score":home_score},
                {"homeAway":"away","team":{"id":"202","displayName":"Away"},
                 "score":away_score},
            ]}],
    }


def payload(*events):
    return {"count":len(events),"events":list(events)}


def response(*events):
    return json.dumps(payload(*events),sort_keys=True).encode()


class ExpansionObserverTests(unittest.TestCase):
    def test_three_explicit_leagues_and_constrained_source_groups(self):
        self.assertEqual(set(obs.LEAGUES),{"NCAAF_FBS","NCAAM_D1","NBA"})
        self.assertIn("groups=80",obs.scoreboard_url("NCAAF_FBS","2026-10-17"))
        self.assertIn("groups=50",obs.scoreboard_url("NCAAM_D1","2026-11-02"))
        self.assertNotIn("groups=",obs.scoreboard_url("NBA","2026-10-20"))
        for league in obs.LEAGUES:
            self.assertIn("limit=500",obs.scoreboard_url(league,"2026-11-02"))
        with self.assertRaisesRegex(ValueError,"Unsupported"):
            obs.scoreboard_url("NHL","2026-10-20")

    def test_provider_only_final_and_preseason_never_grade_or_forecast(self):
        data=obs.parse_scoreboard(payload(
            event(1,"NBA",state="post",completed=True),
            event(2,"NBA",stage=1),
            event(3,"NBA",state="pre",completed=False)), "NBA")
        self.assertEqual(data["eligible_observed"],2)
        self.assertEqual(data["excluded"][0]["game_id"],"2")
        self.assertTrue(data["games"][0]["provider_completed"])
        self.assertTrue(data["games"][0]["provider_final_not_independent_official_verification"])
        self.assertEqual(data["games"][0]["home_score"],102)
        self.assertIsNone(data["games"][1]["home_score"])
        self.assertEqual(data["result_trust"],
                         "ESPN_PROVIDER_ONLY_UNVERIFIED_OFFICIAL")

    def test_missing_season_identity_final_score_tie_and_truncation_fail(self):
        good=event(1,"NBA",state="post",completed=True)
        problems=[
            ({**good,"id":"bad"},"Non-numeric"),
            ({**good,"competitions":[]},"one unique"),
            ({**good,"competitions":[{**good["competitions"][0],
                  "competitors":[good["competitions"][0]["competitors"][0]]}]},
             "Missing opponent"),
            ({**good,"competitions":[{**good["competitions"][0],
                  "competitors":[good["competitions"][0]["competitors"][0]]*2}]},
             "Ambiguous"),
            ({**good,"competitions":[{**good["competitions"][0],
                  "competitors":[{**good["competitions"][0]["competitors"][0],
                                   "score":"NA"},
                                 good["competitions"][0]["competitors"][1]]}]},
             "integer score"),
            ({**good,"competitions":[{**good["competitions"][0],
                  "competitors":[{**good["competitions"][0]["competitors"][0],
                                   "score":"98"},
                                 good["competitions"][0]["competitors"][1]]}]},
             "tied"),
        ]
        for data,why in problems:
            with self.subTest(why=why),self.assertRaisesRegex(ValueError,why):
                obs.parse_scoreboard(payload(data),"NBA")
        with self.assertRaisesRegex(ValueError,"Repeated game"):
            obs.parse_scoreboard(payload(good,good),"NBA")
        with self.assertRaisesRegex(ValueError,"count exceeds"):
            obs.parse_scoreboard({"count":7,"events":[good]},"NBA")
        with self.assertRaisesRegex(ValueError,"truncated"):
            obs.parse_scoreboard({"events":[good]*500},"NBA")

    def test_mixed_type_team_ids_cannot_normalize_to_same_identity(self):
        # Source fields with int and str types previously compared as unequal,
        # although the saved game would contain the same ID for both teams.
        for home_id, away_id in ((101,"101"), ("202",202), ("0",0)):
            with self.subTest(home_id=home_id, away_id=away_id):
                item=event(123,"NBA")
                comp=item["competitions"][0]["competitors"]
                comp[0]["team"]["id"]=home_id
                comp[1]["team"]["id"]=away_id
                with self.assertRaisesRegex(ValueError, "Identical competing teams"):
                    obs.parse_scoreboard(payload(item),"NBA")
        self.assertEqual(obs.parse_scoreboard(
            payload(event(123,"NBA")),"NBA")["eligible_observed"],1)

    def test_scoreboard_count_rejects_noninteger_or_negative_denominator(self):
        good = event(123, "NBA")
        for invalid in (True, False, -1, -100, 1.0, "1"):
            with self.subTest(count=invalid), self.assertRaisesRegex(
                    ValueError, "nonnegative integer"):
                obs.parse_scoreboard({"count": invalid, "events": [good]}, "NBA")
        self.assertEqual(
            obs.parse_scoreboard({"count": 1, "events": [good]}, "NBA")
            ["eligible_observed"], 1)

    def test_provider_stage_unknown_is_excluded_not_declared_regular(self):
        item=event(1,"NBA")
        item.pop("season")
        q=obs.parse_scoreboard({"events":[item]},"NBA")
        self.assertEqual(q["eligible_observed"],0)
        self.assertEqual(q["excluded"][0]["reason"],
                         "not_confirmed_regular_or_postseason")

    def test_quarantine_conflicting_days_without_selecting_newer(self):
        a=obs.parse_scoreboard(payload(
            event(123,"NBA",kickoff="2026-10-20T19:00:00Z")),"NBA")
        b=obs.parse_scoreboard(payload(
            event(123,"NBA",kickoff="2026-10-20T21:00:00Z")),"NBA")
        c=obs.parse_scoreboard(payload(event(124,"NBA")),"NBA")
        ok,conflict=obs.reconcile([
            {"league":"NBA","day":"2026-10-19","parsed":a},
            {"league":"NBA","day":"2026-10-20","parsed":b},
            {"league":"NBA","day":"2026-10-21","parsed":c}])
        self.assertEqual([x["game_id"] for x in ok],["124"])
        self.assertEqual(conflict[0]["game_id"],"123")
        self.assertEqual(conflict[0]["action"],
                         "QUARANTINE_NOT_A_VERIFIED_RESULT")
        self.assertEqual(len(conflict[0]["observed_game_rows"]),2)
        ok,none=obs.reconcile([
            {"league":"NBA","day":"2026-10-19","parsed":a},
            {"league":"NBA","day":"2026-10-20","parsed":a}])
        self.assertEqual(len(ok),1)
        self.assertEqual(none,[])

    def test_live_capture_keeps_original_response_compressed_and_disables_models(self):
        at=datetime(2026,10,17,12,0,tzinfo=timezone.utc)
        history=[]
        source=response(event(123,"NCAAF_FBS",kickoff="2026-10-17T17:00:00Z"))
        def fetch(url):
            history.append(url)
            return source
        with tempfile.TemporaryDirectory() as temp:
            result=obs.capture(fetch,now=at,base=Path(temp),days_ahead=0)
            self.assertEqual(set(x["league"] for x in result["snapshots"]),
                             {"NCAAF_FBS","NBA"})
            self.assertEqual(len(history),2)
            self.assertFalse(result["forecasting_enabled"])
            self.assertFalse(result["official_final_scoring_enabled"])
            self.assertFalse(result["model_training_enabled"])
            self.assertFalse(result["promotion_allowed"])
            self.assertEqual(result["actual_wagers"],0)
            self.assertTrue(result["NO_BET"])
            for s in result["snapshots"]:
                root=Path(temp)/obs.ROOT/"captures"/"20261017T120000000000Z"
                self.assertEqual(gzip.decompress((root/s["compressed_file"]).read_bytes()),
                                 source)
                self.assertEqual(hashlib.sha256(source).hexdigest(),
                                 s["original_response_sha256"])
            self.assertEqual(result,json.loads(
                (root/"manifest.json").read_text()))
            with self.assertRaisesRegex(ValueError,"collision"):
                obs.capture(fetch,now=at,base=Path(temp),days_ahead=0)

    def test_invalid_second_source_fails_before_any_archival_write(self):
        at=datetime(2026,10,17,12,0,tzinfo=timezone.utc)
        calls=0
        def fetch(url):
            nonlocal calls
            calls+=1
            if calls>1:return b'{"broken":true}'
            return response(event(123,"NCAAF_FBS"))
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,"Missing or potentially"):
                obs.capture(fetch,now=at,base=Path(temp),days_ahead=0)
            self.assertFalse((Path(temp)/obs.ROOT).exists())

    def test_future_ncaa_mens_basketball_not_opened_retroactively(self):
        base=datetime(2026,10,17,12,0,tzinfo=timezone.utc)
        calls=[]
        def fetch(url):
            calls.append(url);return response()
        with tempfile.TemporaryDirectory() as temp:
            obs.capture(fetch,now=base,base=temp,days_ahead=3)
            self.assertTrue(all("mens-college-basketball" not in u for u in calls))
            self.assertEqual(len(calls),8)
        opening=datetime(2026,11,2,12,0,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as temp:
            result=obs.capture(fetch,now=opening,base=temp,days_ahead=0)
            self.assertEqual(set(x["league"] for x in result["snapshots"]),
                             {"NCAAF_FBS","NCAAM_D1","NBA"})


    def test_utc_capture_anchor_independent_of_caller_timezone(self):
        # Both offsets straddle a UTC day boundary. A local-day anchor
        # silently requests the wrong ESPN schedule without changing the
        # UTC timestamp written to the immutable source receipt.
        cases = [
            ("west_same_day", datetime(2026, 10, 20, 23, 30,
                tzinfo=timezone(timedelta(hours=-4))), 0, 0,
                ("2026-10-21",)),
            ("east_same_day", datetime(2026, 10, 21, 0, 30,
                tzinfo=timezone(timedelta(hours=5, minutes=30))), 0, 0,
                ("2026-10-20",)),
            ("west_lookback", datetime(2026, 10, 20, 23, 30,
                tzinfo=timezone(timedelta(hours=-4))), 1, 0,
                ("2026-10-20", "2026-10-21")),
            ("east_forward", datetime(2026, 10, 21, 0, 30,
                tzinfo=timezone(timedelta(hours=5, minutes=30))), 0, 1,
                ("2026-10-20", "2026-10-21")),
        ]
        import sports_expansion_audit as audit
        for label, now, days_back, days_ahead, days in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                observed_urls = []
                def fetch(url):
                    observed_urls.append(url)
                    return response()
                report = obs.capture(fetch, now=now, base=Path(directory),
                                     days_ahead=days_ahead, days_back=days_back)
                utc_day = now.astimezone(timezone.utc).date().isoformat()
                self.assertEqual(report["recorded_at_utc"],
                                 now.astimezone(timezone.utc).isoformat())
                self.assertEqual(
                    {snap["day"] for snap in report["snapshots"]}, set(days))
                self.assertEqual(
                    {snap["day"] for snap in report["snapshots"]
                     if snap["league"] == "NBA"}, set(days))
                self.assertEqual(
                    {snap["day"] for snap in report["snapshots"]
                     if snap["league"] == "NCAAF_FBS"}, set(days))
                self.assertEqual(
                    {url.split("dates=")[1][:8] for url in observed_urls},
                    {day.replace("-", "") for day in days})
                if days_back:
                    self.assertEqual(
                        report["collection_window"]["anchor_utc_date"], utc_day)
                self.assertTrue(report["NO_BET"])
                self.assertEqual(report["actual_wagers"], 0)
                self.assertFalse(report["forecasting_enabled"])
                replay = audit.audit(Path(directory))
                self.assertEqual(replay["source_responses_verified"],
                                 2 * len(days))
                self.assertTrue(replay["no_official_independent_final_claim"])


if __name__=="__main__":
    unittest.main()
