"""Offline MLB season context tests: traded players, no double counting, hands."""
import copy
import unittest
from datetime import datetime

from sports_mlb_hitter_context import season_counts, hitter_season_context

NOW = datetime.fromisoformat("2026-10-15T18:40:00+00:00")
START = "2026-10-15T23:00:00Z"


def split(year, team_id=None, *, games=48, pa=193, ab=185, hits=35, hr=5, walks=7):
    return {
        "season":str(year), "gameType":"R", "player":{"id":683734,"fullName":"Synthetic Hitter"},
        **({"team":{"id":team_id}} if team_id else {}),
        "stat":{"gamesPlayed":games,"plateAppearances":pa,"atBats":ab,
                "hits":hits,"homeRuns":hr,"baseOnBalls":walks}}


def fixture(year):
    if year==2025:
        return {"stats":[{"type":{"displayName":"season"},"group":{"displayName":"hitting"},
          "splits":[
            split(2025,None,games=112,pa=447,ab=406,hits=103,hr=14,walks=31),
            split(2025,145),
            split(2025,158,games=64,pa=254,ab=221,hits=68,hr=9,walks=24),
            split(2019,158,games=100,pa=300,ab=200,hits=100,hr=40,walks=40),
            {**split(2025,151),"gameType":"W"}]}]}
    return {"stats":[{"type":{"displayName":"season"},"group":{"displayName":"hitting"},
           "splits":[split(2026,158,games=104,pa=331,ab=288,hits=88,hr=6,walks=35)]}]}


class Reader:
    def __init__(self):
        self.now=NOW
        self.audit=[]
        self.responses={
            "people/683734":{"people":[{"id":683734,"fullName":"Synthetic Hitter",
                                         "batSide":{"code":"R","description":"Right"}}]},
            "people/607192":{"people":[{"id":607192,"fullName":"Synthetic Starter",
                                         "pitchHand":{"code":"R","description":"Right"}}]},
        }
    def clock(self):
        return self.now
    def load(self,path,params=None):
        if path.endswith("/stats"):
            value=fixture(params["season"])
        else:
            value=self.responses[path]
        e={"source_url":"https://statsapi.mlb.com/api/v1/"+path,
            "retrieved_at":self.now.isoformat(),"data_through":self.now.isoformat()}
        self.audit.append(e)
        return copy.deepcopy(value),e


class SeasonContextTests(unittest.TestCase):
    def test_aggregate_does_not_add_team_rows_twice(self):
        a=season_counts(fixture(2025),683734,2025)
        self.assertEqual((a["games"],a["pa"],a["ab"],a["hits"],a["hr"]),
                         (112,447,406,103,14))
        self.assertEqual(a["aggregation"],"official_all_team_total")
        self.assertEqual(a["teams_observed"],[145,158])
        self.assertEqual(a["batting_average"],round(103/406,4))
        self.assertFalse(a["is_game_probability"])

    def test_single_team_year_returns_season_without_fabricated_total(self):
        a=season_counts(fixture(2026),683734,2026)
        self.assertEqual((a["pa"],a["hits"],a["hr"]),(331,88,6))
        self.assertEqual(a["aggregation"],"distinct_team_splits_summed")

    def test_wrong_team_sums_and_duplicate_or_ambiguous_totals_rejected(self):
        a=fixture(2025)
        a["stats"][0]["splits"][2]["stat"]["hits"]=69
        with self.assertRaisesRegex(ValueError,"disagrees"):
            season_counts(a,683734,2025)
        a=fixture(2025)
        a["stats"][0]["splits"].append(copy.deepcopy(a["stats"][0]["splits"][0]))
        with self.assertRaisesRegex(ValueError,"Ambiguous"):
            season_counts(a,683734,2025)
        a=fixture(2026)
        a["stats"][0]["splits"].append(copy.deepcopy(a["stats"][0]["splits"][0]))
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            season_counts(a,683734,2026)

    def test_wrong_season_and_game_type_not_included(self):
        a=fixture(2025)
        self.assertIsNone(season_counts(a,683734,2026))
        a["stats"][0]["splits"][1]["gameType"]="W"
        with self.assertRaisesRegex(ValueError,"disagrees"):
            season_counts(a,683734,2025)

    def test_bad_official_counts_or_hitter_id_refused(self):
        a=fixture(2026)
        a["stats"][0]["splits"][0]["stat"]["homeRuns"]=100
        with self.assertRaisesRegex(ValueError,"Inconsistent"):
            season_counts(a,683734,2026)
        a=fixture(2026)
        a["stats"][0]["splits"][0]["player"]["id"]=99999
        with self.assertRaisesRegex(ValueError,"incorrect hitter"):
            season_counts(a,683734,2026)

    def test_full_season_source_and_handedness_composition(self):
        r=Reader()
        v=hitter_season_context(683734,607192,START,
                                hitter_name="Synthetic Hitter",starter_name="Synthetic Starter",
                                reader=r)
        self.assertEqual(v["hitter"]["hand"],"R")
        self.assertEqual(v["opposing_probable_starter"]["hand"],"R")
        self.assertEqual(len(v["sources"]),4)
        self.assertEqual([x["season"] for x in v["season_statistics"]],[2025,2026])
        self.assertIsNone(v["season_statistics"][1].get("estimated_hit_probability"))
        self.assertIn("NO BET",v["decision"])

    def test_identity_and_future_after_first_pitch_are_rejected(self):
        r=Reader()
        r.responses["people/607192"]["people"][0]["id"]=1
        with self.assertRaisesRegex(ValueError,"identity"):
            hitter_season_context(683734,607192,START,reader=r)
        r=Reader()
        with self.assertRaisesRegex(ValueError,"name"):
            hitter_season_context(683734,607192,START,hitter_name="Someone Else",reader=r)
        r=Reader()
        r.now=datetime.fromisoformat("2026-10-15T23:30:00+00:00")
        with self.assertRaisesRegex(ValueError,"before first pitch"):
            hitter_season_context(683734,607192,START,reader=r)


if __name__=="__main__":
    unittest.main()
