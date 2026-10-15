"""Deterministic no-network verified relief-usage candidate tests."""
import copy
import unittest
from datetime import datetime

from sports_mlb_reliever_candidates import collect_recent_relief_candidates
from test_sports_mlb_bullpen_usage import setup, PAST_PK

START="2026-10-15T23:00:00Z"


def fixture():
    r=setup()
    base=r.rows["game/"+str(PAST_PK)+"/feed/live"]
    box=base["liveData"]["boxscore"]["teams"]["home"]
    box["players"]["ID20001"]["stats"]["pitching"]["gamesStarted"]=1
    box["players"]["ID30001"]["stats"]["pitching"]["gamesStarted"]=0
    return r


class ReliefCandidateTests(unittest.TestCase):
    def test_selects_only_recorded_relief_appearances_excluding_starter(self):
        r=fixture()
        got=collect_recent_relief_candidates(849831, "home", reader=r)
        self.assertEqual(got["status"], "HISTORICAL RELIEF CANDIDATES - NO BET")
        self.assertEqual([p["pitcher_id"] for p in got["selection"]],[30001])
        self.assertEqual(got["selection"][0]["verified_relief_appearances"],1)
        self.assertEqual(got["selection"][0]["pitches_thrown_in_relief"],16)
        self.assertIsNone(got["selection"][0]["projected_appearance_probability"])
        self.assertFalse(got["selection"][0]["confirmed_available"])
        self.assertTrue(got["historical_game_coverage_complete"])
        self.assertEqual(got["probable_starter_id"],20001)

    def test_distinguishes_prior_start_from_a_relief_appearance(self):
        r=fixture()
        r.rows["game/"+str(PAST_PK)+"/feed/live"]["liveData"]["boxscore"]["teams"]["home"]["players"]["ID30001"]["stats"]["pitching"]["gamesStarted"]=1
        got=collect_recent_relief_candidates(849831,"home",reader=r)
        self.assertEqual(got["selection"],[])

    def test_repeated_relief_games_rank_before_single_appearance(self):
        r=fixture()
        roster=r.rows["teams/119/roster"]["roster"]
        roster.append({"person":{"id":30002,"fullName":"Reliever B"},"position":{"abbreviation":"P"}})
        past=copy.deepcopy(r.rows["schedule"]["dates"][0]["games"][0])
        past["gamePk"]=849701
        past["gameDate"]="2026-10-12T23:00:00Z"
        r.rows["schedule"]["dates"][0]["games"].append(past)
        g=copy.deepcopy(r.rows["game/"+str(PAST_PK)+"/feed/live"])
        g["gamePk"]=849701
        g["gameData"]["datetime"]["dateTime"]=past["gameDate"]
        b=g["liveData"]["boxscore"]["teams"]["home"]
        b["pitchers"].append(30002)
        b["players"]["ID30002"]={"stats":{"pitching":{"gamesStarted":0,"numberOfPitches":9}}}
        r.rows["game/849701/feed/live"]=g
        got=collect_recent_relief_candidates(849831,"home",reader=r)
        self.assertEqual(got["selection"][0]["pitcher_id"],30001)
        self.assertEqual(got["selection"][0]["verified_relief_appearances"],2)
        self.assertEqual(got["selection"][0]["pitches_thrown_in_relief"],32)
        self.assertEqual(got["selection"][1]["pitcher_id"],30002)
        self.assertEqual(got["selection"][1]["verified_relief_appearances"],1)

    def test_incomplete_pitcher_stat_skips_whole_game_and_flags_gap(self):
        r=fixture()
        del r.rows["game/"+str(PAST_PK)+"/feed/live"]["liveData"]["boxscore"]["teams"]["home"]["players"]["ID30001"]["stats"]["pitching"]["gamesStarted"]
        got=collect_recent_relief_candidates(849831,"home",reader=r)
        self.assertEqual(got["selection"],[])
        self.assertFalse(got["historical_game_coverage_complete"])
        self.assertEqual(got["incomplete_games"][0]["reason"],"pitching_role_or_count_missing")

    def test_nonfinal_and_wrong_game_identity_do_not_become_evidence(self):
        r=fixture()
        r.rows["schedule"]["dates"][0]["games"][0]["status"]["detailedState"]="In Progress"
        got=collect_recent_relief_candidates(849831,"home",reader=r)
        self.assertEqual(got["selection"],[])
        self.assertEqual(got["incomplete_games"][0]["reason"],"not_verified_final")
        r=fixture()
        r.rows["game/"+str(PAST_PK)+"/feed/live"]["gamePk"]+=10
        with self.assertRaisesRegex(ValueError,"disagree"):
            collect_recent_relief_candidates(849831,"home",reader=r)

    def test_repeated_game_ids_and_nonprobable_starter_are_rejected(self):
        r=fixture()
        same=copy.deepcopy(r.rows["schedule"]["dates"][0]["games"][0])
        r.rows["schedule"]["dates"][0]["games"].append(same)
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            collect_recent_relief_candidates(849831,"home",reader=r)
        r=fixture()
        del r.rows["game/849831/feed/live"]["gameData"]["probablePitchers"]["home"]
        with self.assertRaisesRegex(ValueError,"probable"):
            collect_recent_relief_candidates(849831,"home",reader=r)

    def test_postfirstpitch_and_invalid_limits_refused(self):
        r=fixture()
        r.now=datetime.fromisoformat("2026-10-16T00:00:00+00:00")
        with self.assertRaisesRegex(ValueError,"started"):
            collect_recent_relief_candidates(849831,"home",reader=r)
        for n in (0,8,True,"5"):
            with self.subTest(n=n),self.assertRaises(ValueError):
                collect_recent_relief_candidates(849831,"home",reader=fixture(),lookback_days=n)
        for n in (0,5,False,"4"):
            with self.subTest(n=n),self.assertRaises(ValueError):
                collect_recent_relief_candidates(849831,"home",reader=fixture(),max_candidates=n)

    def test_active_roster_mismatch_and_wrong_side_refused(self):
        r=fixture()
        r.rows["teams/119/roster"]["roster"][0]["position"]["abbreviation"]="1B"
        with self.assertRaisesRegex(ValueError,"starter"):
            collect_recent_relief_candidates(849831,"home",reader=r)
        with self.assertRaisesRegex(ValueError,"pitching_side"):
            collect_recent_relief_candidates(849831,"both",reader=fixture())


if __name__=="__main__":
    unittest.main()
