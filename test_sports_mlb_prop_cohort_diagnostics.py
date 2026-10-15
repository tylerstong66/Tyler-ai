"""Mock-only cohort selection contract tests; no live odds or wagers."""
import copy
import unittest
from datetime import datetime

from sports_mlb_prop_cohort_diagnostics import roster_review

NOW=datetime.fromisoformat("2026-10-15T19:00:00+00:00")


class Reader:
    def __init__(self):
        self.audit=[]
    def clock(self):
        return NOW
    def load(self,path,params=None,api_version="v1"):
        if path=="game/849810/feed/live":
            data={"gamePk":849810,"gameData":{
                "status":{"abstractGameState":"Preview"},
                "datetime":{"dateTime":"2026-10-15T23:00:00Z"},
                "teams":{"home":{"id":119},"away":{"id":158}}}}
        elif path.startswith("teams/"):
            tid=int(path.split("/")[1])
            data={"roster":[
                {"person":{"id":tid*100+12,"fullName":"Hitter B"},"position":{"abbreviation":"1B"}},
                {"person":{"id":tid*100+10,"fullName":"Hitter A"},"position":{"abbreviation":"RF"}},
                {"person":{"id":tid*100+1,"fullName":"Pitcher"},"position":{"abbreviation":"P"}}]}
        elif path.endswith("/stats"):
            pid=int(path.split("/")[1]);year=params["season"]
            data={"stats":[{"type":{"displayName":"gameLog"},"group":{"displayName":"hitting"},
                "splits":[{"date":f"{year}-06-{1+i:02d}","season":str(year),"gameType":"R",
                    "game":{"gamePk":year*100000+pid*100+i},
                    "player":{"id":pid},"team":{"id":pid//100},
                    "stat":{"atBats":4,"hits":i%2,"homeRuns":0,"plateAppearances":4}}
                    for i in range(1,25)]}]}
        else:
            raise AssertionError("Unexpected official source "+path)
        receipt={"source_url":"https://statsapi.mlb.com/api/v1/"+path,
                 "retrieved_at":NOW.isoformat()}
        self.audit.append(receipt)
        return copy.deepcopy(data),receipt


class RosterCohortTests(unittest.TestCase):
    def test_team_side_ids_sorted_and_pitchers_excluded(self):
        result=roster_review(849810,2026,reader=Reader(),hitters_per_team=1)
        self.assertEqual(result["hitter_count"],2)
        self.assertEqual(result["hitter_ids"],[11910,15810])
        self.assertFalse(result["independently_frozen_prospective"])
        self.assertFalse(result["wager_execution"])
        self.assertFalse(result["model_approved_for_sportsbook_value"])
        self.assertEqual(result["roster_selection"]["hitter_selection_rule"],
                         "lowest_official_numeric_player_ids_per_side")
        self.assertGreater(result["pooled"]["hit"]["eligible_player_games"],0)

    def test_invalid_requested_group_size_rejected(self):
        for count in (0,9,True,"5"):
            with self.subTest(count=count),self.assertRaises(ValueError):
                roster_review(849810,2026,reader=Reader(),hitters_per_team=count)

    def test_nonpregame_game_rejected(self):
        r=Reader()
        old=r.load
        def changed(path,params=None,api_version="v1"):
            data,receipt=old(path,params,api_version)
            if path.startswith("game/"):
                data["gameData"]["status"]["abstractGameState"]="Final"
            return data,receipt
        r.load=changed
        with self.assertRaisesRegex(ValueError,"pregame"):
            roster_review(849810,2026,reader=r)


if __name__=="__main__":
    unittest.main()
