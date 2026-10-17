"""Strict multi-source NCAA identity matching and original archive invariants."""
import gzip
import json
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path

import sports_expansion_observer as espn
import sports_ncaa_official_source as ncaa
import sports_ncaa_espn_identity as identity

AT=datetime(2026,10,17,14,tzinfo=timezone.utc)
KICKOFF="2026-10-17T17:00:00Z"
KICKOFF_EPOCH=int(datetime.fromisoformat(KICKOFF.replace("Z","+00:00")).timestamp())


def official_game(when=KICKOFF_EPOCH,home="Tulsa",away="Rice",final=False):
    return {
        "contestId":"654321","gameState":"F" if final else "P",
        "startDate":"10/17/2026","startTimeEpoch":str(when),
        "teams":[
            {"isHome":True,"nameShort":home,"score":"28" if final else None},
            {"isHome":False,"nameShort":away,"score":"21" if final else None},
        ],
    }


def espn_game(start=KICKOFF,home="Tulsa",away="Rice",completed=False):
    return {
        "id":"401100001","date":start,"season":{"type":2},
        "status":{"type":{"state":"post" if completed else "pre",
                          "completed":completed}},
        "competitions":[{"neutralSite":False,"competitors":[
            {"homeAway":"home","team":{
                "id":"202","location":home,"displayName":home+" Golden Hurricane"},
             "score":"28" if completed else None},
            {"homeAway":"away","team":{
                "id":"101","location":away,"displayName":away+" Owls"},
             "score":"21" if completed else None},
        ]}],
    }


class CollegeIdentityTests(unittest.TestCase):
    def seed(self,root,ncaa_when=KICKOFF_EPOCH,espn_when=KICKOFF,
             ncaa_final=False,espn_final=False):
        def f_ncaa(url):
            return json.dumps({"data":{"contests":[official_game(
                when=ncaa_when,final=ncaa_final)]}}).encode()
        ncaa.run(f_ncaa,base=root,now=AT)
        def f_espn(url):
            if "football/college-football" in url and "dates=20261017" in url:
                return json.dumps({"count":1,"events":[espn_game(
                    start=espn_when,completed=espn_final)]}).encode()
            return b'{"count":0,"events":[]}'
        espn.capture(f_espn,base=root,now=AT,days_ahead=0)

    def test_real_source_replay_and_exact_match_both_providers(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root)
            saved=identity.run(base=root,now=AT+timedelta(minutes=10))
            report=saved["report"]
            self.assertEqual((report["espn_games_examined"],
                              report["unique_source_game_identity_matches"],
                              report["unverified_game_identifiers"]),(1,1,0))
            case=report["matched"][0]
            self.assertEqual(case["espn_game_id"],"401100001")
            self.assertEqual(case["ncaa_game_id"],"654321")
            self.assertEqual(case["start_difference_minutes"],0)
            self.assertFalse(case["independent_result_grading_enabled"])
            self.assertFalse(report["forecasting_enabled"])
            self.assertTrue(report["NO_BET"])
            output=root/identity.ROOT/"captures"/"20261017T141000000000Z"/"manifest.json"
            self.assertEqual(json.loads(output.read_text()),saved)
            with self.assertRaisesRegex(ValueError,"collision"):
                identity.run(base=root,now=AT+timedelta(minutes=10))

    def test_known_120_minute_postponement_never_matches(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.seed(root,ncaa_when=KICKOFF_EPOCH+7200)
            report=identity.run(base=root,now=AT+timedelta(minutes=4))["report"]
            self.assertEqual(report["unique_source_game_identity_matches"],0)
            self.assertEqual(report["unverified"][0]["reason"],"NCAA_START_CHANGED")
            self.assertEqual(report["unverified"][0]["observed_ncaa_ids"],["654321"])

    def test_official_espn_final_score_disagreement_quarantined(self):
        base={"league":"NCAAF_FBS","ncaa_game_id":"654321",
              "home_name":"Tulsa","away_name":"Rice",
              "source_start_time_epoch":str(KICKOFF_EPOCH),
              "provider_reported_final":True,
              "ncaa_home_score":31,"ncaa_away_score":21}
        original={"league":"NCAAF_FBS","espn_game_id":"401100001",
                  "game_id":"401100001","home_name":"Tulsa Golden Hurricane",
                  "away_name":"Rice Owls","scheduled_start_utc":KICKOFF,
                  "home_score":28,"away_score":21,"provider_completed":True,
                  "school_names":{"home":"tulsa","away":"rice"}}
        mismatch=identity.reconcile([base],[original])
        self.assertEqual(mismatch["unverified"][0]["reason"],
                         "CONFLICTING_FINAL_SCORES_NO_GRADE")
        base["ncaa_home_score"]=28
        exact=identity.reconcile([base],[original])
        self.assertEqual(exact["unique_source_game_identity_matches"],1)
        self.assertFalse(exact["matched"][0]["independent_result_grading_enabled"])

    def test_missing_school_location_and_alias_never_fuzzy_match(self):
        college={"league":"NCAAM_D1","ncaa_game_id":"77",
                 "home_name":"Penn St.","away_name":"Michigan",
                 "source_start_time_epoch":str(KICKOFF_EPOCH),
                 "provider_reported_final":False}
        espn_game={"league":"NCAAM_D1","game_id":"123","espn_game_id":"123",
                   "scheduled_start_utc":KICKOFF,"provider_completed":False,
                   "school_names":{"home":"pennstate","away":"michigan"},
                   "home_name":"Penn State","away_name":"Michigan"}
        out=identity.reconcile([college],[espn_game])
        self.assertEqual(out["unique_source_game_identity_matches"],0)
        self.assertEqual(out["unverified"][0]["reason"],
                         "NO_UNAMBIGUOUS_NCAA_GAME_ID")
        espn_game["school_names"]["home"]=None
        out=identity.reconcile([college],[espn_game])
        self.assertEqual(out["unverified"][0]["reason"],
                         "ESPN_SCHOOL_LOCATION_UNAVAILABLE")

    def test_source_tampering_and_stale_sources_fail_before_any_new_crosswalk(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root)
            ncaa_capture=next((root/ncaa.ROOT/"captures").iterdir())
            raw=ncaa_capture/"NCAAF_FBS_week-08.json.gz"
            raw.write_bytes(gzip.compress(
                b'{"data":{"contests":[]}}'))
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                identity.run(base=root,now=AT+timedelta(minutes=10))
            self.assertFalse((root/identity.ROOT).exists())
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root)
            with self.assertRaisesRegex(ValueError,"stale"):
                identity.run(base=root,now=AT+timedelta(hours=13))
            self.assertFalse((root/identity.ROOT).exists())

    def test_duplicated_official_fixture_candidates_are_never_chosen(self):
        ncaa_entries=[{
            "league":"NCAAF_FBS","ncaa_game_id":str(i),
            "home_name":"Tulsa","away_name":"Rice",
            "source_start_time_epoch":str(KICKOFF_EPOCH+60*i),
            "provider_reported_final":False}
            for i in (1,2)]
        entry={"league":"NCAAF_FBS","espn_game_id":"4011",
               "scheduled_start_utc":KICKOFF,
               "school_names":{"home":"tulsa","away":"rice"},
               "provider_completed":False,
               "home_name":"Tulsa","away_name":"Rice"}
        report=identity.reconcile(ncaa_entries,[entry])
        self.assertEqual(report["unique_source_game_identity_matches"],0)
        self.assertEqual(report["unverified"][0]["reason"],
                         "MULTIPLE_NCAA_IDENTITIES")


if __name__=="__main__":
    unittest.main()
