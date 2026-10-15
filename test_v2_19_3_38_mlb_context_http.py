import unittest
from unittest.mock import patch
import app as core
import app_v2_19_3_38 as latest
from test_v2_19_3_37_mlb_auto_http import report, resolved, MSG

KEY="synthetic-hitter-context-test-key"

def payload():
    r=report()
    r["matchup_research"]["starter_matchup"]={"pitcher":r["probable_starter"],
        "hits":0,"at_bats":3,"plate_appearances":3,"historical_batting_average":0.0}
    r["hitter_season_context"]={
        "hitter":{"id":10001,"hand":"R"},
        "opposing_probable_starter":{"id":20001,"hand":"R"},
        "season_statistics":[{"season":2026,"hits":88,"ab":288,"hr":6,"pa":331,
            "batting_average":round(88/288,4)}]}
    return r

class RouteTests(unittest.TestCase):
    def setUp(self):self.client=latest.app.test_client()
    def test_authorized_research_adds_regular_season_context(self):
        with patch.object(core,"TYLER_API_KEY",KEY),patch.object(
             latest,"resolve_named_pregame",return_value=resolved()),patch.object(
             latest,"contextual_mlb_research",return_value=payload()) as work:
            res=self.client.post("/chat",json={"message":MSG},headers={"X-Tyler-Key":KEY})
        self.assertEqual(res.status_code,200,res.get_data(as_text=True)[:500])
        obj=res.get_json()
        self.assertEqual(obj["sports_mlb_contextual_research"]["hitter_season_context"]
                         ["season_statistics"][0]["hits"],88)
        self.assertIsNone(obj["sports_mlb_contextual_research"]["estimated_home_run_probability"])
        work.assert_called_once()
    def test_unauthorized_request_blocked(self):
        with patch.object(core,"TYLER_API_KEY",KEY),patch.object(
             latest,"contextual_mlb_research",side_effect=AssertionError("not authorized")) as fn:
            res=self.client.post("/chat",json={"message":MSG})
        self.assertEqual(res.status_code,401)
        fn.assert_not_called()
    def test_bad_source_fails_closed(self):
        with patch.object(core,"TYLER_API_KEY",KEY),patch.object(
             latest,"resolve_named_pregame",return_value=resolved()),patch.object(
             latest,"contextual_mlb_research",side_effect=ValueError("No verified stats")):
            res=self.client.post("/chat",json={"message":MSG},headers={"X-Tyler-Key":KEY})
        self.assertEqual(res.status_code,409)
        self.assertFalse(res.get_json()["success"])
    def test_declares_uncalibrated_and_read_only(self):
        data=self.client.get("/status").get_json()
        self.assertTrue(data["sports_mlb_official_season_context_supported"])
        self.assertTrue(data["sports_mlb_official_handedness_supported"])
        self.assertFalse(data["sports_mlb_player_prop_probabilities_calibrated"])
        self.assertFalse(data["sports_mlb_contextual_wager_execution_enabled"])

if __name__=="__main__":unittest.main()
