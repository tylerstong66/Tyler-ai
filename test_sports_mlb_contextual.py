import copy
import unittest
from unittest.mock import patch
import sports_mlb_contextual as module

class ContextTests(unittest.TestCase):
    def report(self):
        return {"hitter":{"id":1,"name":"Test Hitter"},"probable_starter":{"id":2,"name":"Test Starter"},
                "matchup_research":{"event_start":"2026-10-15T23:00:00+00:00"},"summary":[],
                "wager_executed":False,"estimated_hit_probability":None,"estimated_home_run_probability":None}
    def context(self):
        return {"hitter":{"id":1,"hand":"R"},"opposing_probable_starter":{"id":2,"hand":"L"},
                "first_pitch":"2026-10-15T23:00:00+00:00","as_of":"2026-10-15T18:00:00+00:00",
                "season_statistics":[{"season":2025,"hits":4,"ab":20,"hr":1,"pa":24,"batting_average":.2},
                                     {"season":2026,"hits":8,"ab":25,"hr":1,"pa":29,"batting_average":.32}]}
    def test_combination_keeps_probabilities_unknown(self):
        with patch.object(module,"auto_bullpen_matchup",return_value=self.report()),patch.object(
            module,"hitter_season_context",return_value=self.context()):
            got=module.contextual_mlb_research(1,1,"away")
        self.assertIsNone(got["estimated_hit_probability"])
        self.assertIsNone(got["estimated_home_run_probability"])
        self.assertEqual(got["hitter_season_context"]["hitter"]["hand"],"R")
        self.assertTrue(any("2026" in x for x in got["summary"]))
    def test_inconsistent_identity_and_date_are_rejected(self):
        c=self.context();c["opposing_probable_starter"]["id"]=3
        with patch.object(module,"auto_bullpen_matchup",return_value=self.report()),patch.object(
            module,"hitter_season_context",return_value=c):
            with self.assertRaises(ValueError):module.contextual_mlb_research(1,1,"away")
        c=self.context();c["as_of"]="2026-10-15T23:10:00+00:00"
        with patch.object(module,"auto_bullpen_matchup",return_value=self.report()),patch.object(
            module,"hitter_season_context",return_value=c):
            with self.assertRaises(ValueError):module.contextual_mlb_research(1,1,"away")

if __name__=="__main__":unittest.main()
