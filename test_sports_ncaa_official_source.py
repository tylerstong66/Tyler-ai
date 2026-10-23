"""Independent NCAA-owned source parser and fail-closed capture regression tests."""
import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import date,datetime,timezone,timedelta
from pathlib import Path

import sports_ncaa_official_source as n
import sports_expansion_observer as e


def contest(identifier="12345",state="P",score1=None,score2=None):
    return {"contestId":identifier,"gameState":state,
            "startDate":"2026-10-17",
            "startTimeEpoch":"1792256400",
            "teams":[
                {"isHome":True,"nameShort":"Penn State","score":score1},
                {"isHome":False,"nameShort":"Michigan","score":score2},
            ]}


def raw(*items):
    return json.dumps({"data":{"contests":list(items)}}).encode()


class NcaaSourceTests(unittest.TestCase):
    def test_source_is_ncaa_owned_graphql_not_third_party_aggregator(self):
        football=n.graph_url("NCAAF_FBS",year=2026,week=8)
        self.assertTrue(football.startswith("https://sdataprod.ncaa.com/"))
        self.assertIn("sha256Hash",football)
        self.assertIn("MFB",football)
        self.assertIn("11",football)
        basketball=n.graph_url("NCAAM_D1",year=2026,day="2026-11-02")
        self.assertIn("MBB",basketball)
        self.assertIn("2026%2F11%2F02",basketball)
        with self.assertRaisesRegex(ValueError,"Choose"):
            n.graph_url("NCAAM_D1",year=2026)
        with self.assertRaisesRegex(ValueError,"uses week"):
            n.graph_url("NCAAF_FBS",year=2026,day="2026-10-17")
        with self.assertRaisesRegex(ValueError,"Unsupported NCAA football week"):
            n.graph_url("NCAAF_FBS",year=2026,week=0)

    def test_fbs_and_hoops_queried_only_in_declared_windows(self):
        today=n.requested_windows(date(2026,10,17))
        self.assertEqual(len(today),5)
        self.assertEqual({x[0] for x in today},{"NCAAF_FBS"})
        first_college_hoops=n.requested_windows(date(2026,10,30))
        self.assertIn("NCAAM_D1",{x[0] for x in first_college_hoops})
        self.assertNotIn("NBA",{x[0] for x in first_college_hoops})
        with self.assertRaisesRegex(ValueError,"exceeds"):
            n.requested_windows(date(2026,10,17),8)

    def test_future_matchup_is_not_result_and_known_final_still_not_scored(self):
        p=n.official_scoreboard(raw(contest()),"NCAAF_FBS")
        self.assertEqual(p[0]["source_state"],"P")
        self.assertIsNone(p[0]["ncaa_home_score"])
        self.assertFalse(p[0]["final_result_scoring_authorized"])
        f=n.official_scoreboard(raw(contest(state="F",score1=27,score2=24)),
                                "NCAAF_FBS")
        self.assertEqual((f[0]["ncaa_home_score"],f[0]["ncaa_away_score"]),(27,24))
        self.assertTrue(f[0]["provider_reported_final"])
        self.assertFalse(f[0]["final_result_scoring_authorized"])

    def test_incomplete_final_duplicate_game_home_identity_graphql_error_fail(self):
        invalid=[
            ({"data":{"contests":None}},"Missing or"),
            ({"errors":[{"message":"unavailable"}],"data":{"contests":[]}},"GraphQL"),
            ({"data":{"contests":[contest(),contest()]}},"Repeated NCAA"),
            ({"data":{"contests":[contest(state="F",score1=27,score2=None)]}},
             "Incomplete final"),
            ({"data":{"contests":[contest(state="F",score1=27,score2=27)]}},"tied"),
            ({"data":{"contests":[{**contest(),"gameState":"?"}]}},"Unrecognized"),
            ({"data":{"contests":[{**contest(),"teams":[
                {**contest()["teams"][0]},{**contest()["teams"][0]}]}]}},"repeated home"),
        ]
        for payload,reason in invalid:
            with self.subTest(reason=reason),self.assertRaisesRegex(ValueError,reason):
                n.official_scoreboard(json.dumps(payload).encode(),"NCAAM_D1")

    def test_sealed_source_replay_and_conflicting_week_quarantine(self):
        at=datetime(2026,10,17,12,tzinfo=timezone.utc)
        original=raw(contest())
        revised=raw(contest(state="I"))
        urls=[]
        def fetch(url):
            urls.append(url)
            return revised if "week%22%3A8" in url else original
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            out=n.run(fetch,base=root,now=at,days_ahead=0)
            self.assertEqual(len(out["snapshots"]),5)
            self.assertTrue(out["NO_BET"])
            self.assertFalse(out["official_final_scoring_enabled"])
            self.assertFalse(out["college_to_espn_identity_map_verified"])
            self.assertFalse(out["fbs_source_week_completeness_verified"])
            self.assertEqual(len(out["quarantined_ncaa_contests"]),1)
            self.assertEqual(len(out["unambiguous_ncaa_contests"]),0)
            folder=root/n.ROOT/"captures"/"20261017T120000000000Z"
            self.assertEqual(json.loads((folder/"manifest.json").read_text()),out)
            for snap in out["snapshots"]:
                saved=gzip.decompress((folder/snap["source_file"]).read_bytes())
                self.assertEqual(hashlib.sha256(saved).hexdigest(),snap["source_sha256"])
            with self.assertRaisesRegex(ValueError,"collision"):
                n.run(fetch,base=root,now=at,days_ahead=0)

    def test_all_ncaa_capture_windows_are_utc_anchored_even_without_lookback(self):
        # These opposite offsets straddle the opening of the 2026-27
        # Division I basketball source window in UTC.
        cases=[
            ("west_opens_d1",datetime(2026,10,29,23,30,
                tzinfo=timezone(timedelta(hours=-4))),True),
            ("east_not_yet_d1",datetime(2026,10,30,0,30,
                tzinfo=timezone(timedelta(hours=5,minutes=30))),False),
        ]
        for label,at,expected_d1 in cases:
            with self.subTest(label=label),tempfile.TemporaryDirectory() as td:
                seen=[]
                def fetch(url):
                    seen.append(url)
                    return raw(contest())
                result=n.run(fetch,base=Path(td),now=at,days_ahead=0)
                expected=n.requested_windows(at.astimezone(timezone.utc).date(),
                                             days_ahead=0,days_back=0)
                self.assertEqual([(s["league"],s["window"],s["source_url"])
                                  for s in result["snapshots"]],expected)
                self.assertEqual(len(seen),len(expected))
                self.assertEqual(
                    result["recorded_at_utc"],at.astimezone(timezone.utc).isoformat())
                self.assertEqual(any(s["league"]=="NCAAM_D1" for s in
                                     result["snapshots"]),expected_d1)
                self.assertTrue(result["NO_BET"])
                self.assertEqual(result["actual_wagers"],0)

    def test_partial_failed_provider_fetch_does_not_publish_source(self):
        counter=0
        def fetch(url):
            nonlocal counter
            counter+=1
            return raw(contest()) if counter==1 else b'{"data": {"contests": null}}'
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            with self.assertRaisesRegex(ValueError,"Missing or potentially"):
                n.run(fetch,base=root,
                      now=datetime(2026,10,17,12,tzinfo=timezone.utc))
            self.assertFalse((root/n.ROOT).exists())


if __name__=="__main__":
    unittest.main()
