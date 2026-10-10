import copy
import json
import unittest
from unittest.mock import patch

import app_v2_19_3_32 as v
from sports_betting import SportsLedger, digest
from sports_nhl_paper import (NhlPublicFeed, NhlPaperTrial, PreviewArticle, validate_nhl,
    NHL_PREDICTIONS, NHL_RESULTS, NHL_QUOTES)
from sports_paper_trial import PaperTrial, PAPER_PREDICTIONS
from test_v2_18_skill_lab import MemoryStore
from test_v2_19_3_31_sports_paper import game as nfl_game, forecast as nfl_forecast

NOW = "2026-10-09T20:00:00+00:00"
START = "2026-10-09T23:00:00Z"


def forecast():
    return {"probabilities": {"home": .55, "away": .45}, "rationale": "Experimental estimate from the supplied market and tiny season sample.",
            "uncertainty": "Starting goalies and final rosters are unconfirmed; probabilities are uncalibrated."}


def game():
    g=nfl_game();g.update(event_id="401892466",event="New York Rangers at Washington Capitals",event_start=START,
        official_game_id="2026020067",sport="NHL",market="two_way_moneyline_including_overtime_shootout")
    g["teams"]={s:{"id":i,"official_id":oi,"abbreviation":a,"name":n,"short_name":sn,"score":None} for s,i,oi,a,n,sn in
        [("home","23","15","WSH","Washington Capitals","Capitals"),("away","13","3","NYR","New York Rangers","Rangers")]}
    g["moneyline_quote"]["prices"]={"home":-142,"away":120}
    return g


def summary():
    g=game()
    return {"header":{"id":g["event_id"],"league":{"abbreviation":"NHL"},"season":{"year":2027,"type":2},
        "competitions":[{"date":START,"neutralSite":False,"status":{"type":{"state":"pre","completed":False}},
        "competitors":[{"id":t["id"],"homeAway":s,"team":{"displayName":t["name"],"name":t["short_name"],"abbreviation":t["abbreviation"]}} for s,t in g["teams"].items()]}]},
        "pickcenter":[{"provider":{"name":"DraftKings"},"moneyline":{s:{"close":{"odds":str(p)}} for s,p in g["moneyline_quote"]["prices"].items()}}],
        "injuries":[{"team":{"id":"23","displayName":"Washington Capitals"},"injuries":[{"status":"Out","date":NOW,"athlete":{"displayName":"A Player"}}]}]}


def official():
    g=game()
    return {"id":2026020067,"startTimeUTC":START,"gameType":2,"gameScheduleState":"OK","gameState":"FUT","tiesInUse":False,
        **{s+"Team":{"id":int(t["official_id"]),"abbrev":t["abbreviation"],"score":None,"record":"2-1-0"} for s,t in g["teams"].items()},
        "matchup":{"goalieComparison":{"homeTeam":{"leaders":[{"name":{"default":"A Goalie"},"savePctg":.92}]}}}}


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.data=official();self.espn=summary();self.schedule={"gameWeek":[{"games":[copy.deepcopy(self.data)]}]}
        self.html='<script type="application/ld&#x2B;json">'+json.dumps({"@type":"NewsArticle","headline":"Rangers at Capitals projected lineups",
            "articleBody":"Rangers projected lineup\nA Goalie\nCapitals projected lineup\nB Goalie","datePublished":"2026-10-09T14:00:00Z"})+'</script>'
        self.urls=[];self.feed=NhlPublicFeed(now_fn=lambda:NOW);self.feed._fetch=self.fetch

    def fetch(self,url,params=None,text=False):
        self.urls.append(url)
        if url.endswith("summary"): data=self.espn
        elif "/schedule/" in url:data=self.schedule
        elif "/landing" in url:data=self.data
        elif "/news/" in url:data=self.html
        else:self.fail("Unexpected request: "+url)
        return copy.deepcopy(data),{"source_url":url,"parameters":params or {},"retrieved_at":NOW,"provider_updated_at":None,"response_sha256":digest(data)}

    def test_crossmatched_official_identity_and_projected_goalies(self):
        g=self.feed.pregame("401892466")
        self.assertEqual(g["official_game_id"],"2026020067")
        self.assertEqual(g["confirmed_starting_goalies"],{"home":None,"away":None})
        self.assertEqual(g["official_projected_lineup"]["status"],"projected, not confirmed")
        self.assertEqual(len(g["evidence"]),4)
        self.assertEqual(g["reported_injuries"][0]["players"][0]["status"],"Out")

    def test_official_missing_or_ambiguous_match_fails_closed(self):
        for games in ([],[self.data,self.data]):
            self.schedule={"gameWeek":[{"games":games}]}
            with self.subTest(count=len(games)),self.assertRaisesRegex(ValueError,"uniquely"): self.feed.game("401892466")

    def test_publisher_aliases_match_schedule_and_pinned_final(self):
        for espn,nhl in [("NJ","NJD"),("SJ","SJS"),("TB","TBL"),("LA","LAK")]:
            with self.subTest(alias=espn):
                self.espn["header"]["competitions"][0]["competitors"][0]["team"]["abbreviation"]=espn
                self.data["homeTeam"]["abbrev"]=nhl
                self.schedule={"gameWeek":[{"games":[copy.deepcopy(self.data)]}]}
                original=self.feed.game("401892466")
                self.assertEqual(original["teams"]["home"]["abbreviation"],espn)
                self.data.update(gameState="OFF",homeTeam={**self.data["homeTeam"],"score":3},awayTeam={**self.data["awayTeam"],"score":1})
                self.assertTrue(self.feed.final_game({"snapshot":original})["completed"])

    def test_alias_does_not_relax_opponent_or_time_checks(self):
        self.espn["header"]["competitions"][0]["competitors"][0]["team"]["abbreviation"]="SJ"
        self.data["homeTeam"]["abbrev"]="SJS"
        self.schedule={"gameWeek":[{"games":[copy.deepcopy(self.data)]}]}
        for mutate in (lambda d:d["awayTeam"].update(abbrev="BOS"),lambda d:d.update(startTimeUTC="2026-10-09T22:00:00Z")):
            d=copy.deepcopy(self.data);mutate(d);self.schedule={"gameWeek":[{"games":[d]}]}
            with self.assertRaisesRegex(ValueError,"uniquely"):self.feed.game("401892466")

    def test_official_event_id_teams_time_and_rules_must_match(self):
        for mutate in (lambda d:d.update(id=2026020099),lambda d:d['homeTeam'].update(abbrev="OTHER"),
                       lambda d:d.update(startTimeUTC="2026-10-09T22:00:00Z"),lambda d:d.update(gameType=1),
                       lambda d:d.update(tiesInUse=True),lambda d:d.update(gameScheduleState="PPD")):
            self.data=official();mutate(self.data)
            with self.subTest(data=self.data),self.assertRaises(ValueError): self.feed.game("401892466")

    def test_optional_preview_failure_keeps_starters_unknown(self):
        old=self.feed._fetch
        def fetch(url,*a,**k):
            if "/news/" in url:raise RuntimeError("Unavailable")
            return old(url,*a,**k)
        self.feed._fetch=fetch;g=self.feed.pregame("401892466")
        self.assertIsNone(g["official_projected_lineup"])
        self.assertIsNone(g["confirmed_starting_goalies"]["home"])

    def test_live_official_state_overrides_stale_publisher_pre_state(self):
        self.data["gameState"]="LIVE"
        with self.assertRaisesRegex(ValueError,"before"):self.feed.pregame("401892466")

    def test_final_retrieval_uses_pinned_id_without_publisher_or_schedule(self):
        record={"snapshot":game()};self.data.update(gameState="OFF")
        g=self.feed.final_game(record)
        self.assertTrue(g["completed"])
        self.assertEqual(len(self.urls),1)
        self.assertTrue(self.urls[0].endswith("2026020067/landing"))

    def test_article_parser_handles_encoded_jsonld_type_without_scripts(self):
        p=PreviewArticle();p.feed(self.html+'<script>alert("ignore")</script>')
        self.assertEqual(len(p.articles),1)
        self.assertIn("projected",p.articles[0]["articleBody"])

    def test_wrong_league_and_bad_ids_cannot_be_used(self):
        self.espn["header"]["league"]["abbreviation"]="NFL"
        with self.assertRaises(ValueError):self.feed.game("401892466")
        self.urls=[]
        with self.assertRaises(ValueError):self.feed.game("https://example.com")
        self.assertEqual(self.urls,[])

    def test_schedule_today_uses_eastern_date_after_utc_midnight(self):
        f=NhlPublicFeed(now_fn=lambda:"2026-10-10T00:30:00+00:00")
        self.assertEqual(f.schedule_today().isoformat(),"2026-10-09")
        f._fetch=lambda *a,**k:({"events":[]},{})
        self.assertEqual(f.schedule("2026-10-09")["events"],[])

    def test_pinned_final_reader_rejects_changed_team_and_schedule(self):
        self.data["homeTeam"]["abbrev"]="BOS"
        with self.assertRaisesRegex(ValueError,"identities"):self.feed.final_game({"snapshot":game()})
        self.data=official();self.data["gameScheduleState"]="CNCL"
        with self.assertRaises(ValueError):self.feed.final_game({"snapshot":game()})


class FakeFeed:
    def __init__(self):self.data=game()
    def pregame(self,i):return copy.deepcopy(self.data)
    def game(self,i):return copy.deepcopy(self.data)
    def final_game(self,r):return copy.deepcopy(self.data)


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.now=NOW;self.store=MemoryStore();self.feed=FakeFeed()
        self.ledger=SportsLedger(self.store.get_rows,self.store.save_row,lambda:self.now)
        self.trial=NhlPaperTrial(self.ledger,self.feed,lambda g:forecast(),"test-model",lambda:{"version":1})

    def saved(self):return self.trial.analyze("401892466")
    def final(self,home=4,away=3):
        self.now="2026-10-10T02:00:00+00:00";self.feed.data.update(state="post",completed=True)
        self.feed.data["teams"]["home"]["score"]=home;self.feed.data["teams"]["away"]["score"]=away

    def test_binary_forecast_no_tie_or_push(self):
        r=self.saved();self.assertTrue(r["paper_prediction_id"].startswith("NHP-"))
        self.assertEqual(set(r["forecast"]["probabilities"]),{"home","away"})
        self.assertEqual(r["hypothetical_price_metrics"]["estimated_push_probability"],0)
        self.assertFalse(r["wager_executed"]);self.assertEqual(r["decision"],"NO BET")
        self.assertEqual(r["profile_role"],"active-profile identity only; forecasting uses a separate experimental NHL prompt")

    def test_regulation_tie_probability_cannot_enter_binary_market(self):
        f=forecast();f["probabilities"]["tie"]=.01
        with self.assertRaisesRegex(ValueError,"no tie"):validate_nhl(f)
        f=forecast();f["probabilities"]["home"]=.6
        with self.assertRaises(ValueError):validate_nhl(f)

    def test_nhl_and_nfl_records_and_reports_stay_separate(self):
        class NflFeed:
            def pregame(self,i):return nfl_game()
        nfl=PaperTrial(self.ledger,NflFeed(),lambda g:nfl_forecast(),"same-model",lambda:{"version":1})
        nfl.analyze("401872981");self.saved()
        self.assertEqual(nfl.report()["predictions_in_window"],1)
        self.assertEqual(self.trial.report()["predictions_in_window"],1)
        self.assertEqual({r["category"] for r in self.store.rows},{PAPER_PREDICTIONS,NHL_PREDICTIONS})

    def test_overtime_or_shootout_win_is_a_win_and_original_is_unchanged(self):
        r=self.saved();original=self.store.rows[0]["memories"]
        self.final(4,3);result=self.trial.settle(r["paper_prediction_id"])
        self.assertEqual(result["outcome"],"home")
        self.assertAlmostEqual(result["hypothetical_flat_unit_profit"],100/142)
        self.assertEqual(self.store.rows[0]["memories"],original)
        self.assertEqual(result["prediction_sha256"],digest(r))
        self.assertEqual(self.trial.report()["multiclass_brier_score"],(.55-1)**2+.45**2)
        self.assertIsNone(result["price_clv_percentage_points"])

    def test_tied_final_is_not_a_push_or_scored_result(self):
        r=self.saved();self.final(3,3)
        with self.assertRaisesRegex(ValueError,"cannot be tied"):self.trial.settle(r["paper_prediction_id"])
        self.assertEqual(self.ledger._records(NHL_RESULTS),[])

    def test_live_or_changed_official_identity_cannot_settle(self):
        r=self.saved()
        with self.assertRaisesRegex(ValueError,"final result"):self.trial.settle(r["paper_prediction_id"])
        self.final();self.feed.data["official_game_id"]="2026020099"
        with self.assertRaisesRegex(ValueError,"identity"):self.trial.settle(r["paper_prediction_id"])

    def test_duplicate_prediction_and_result_rejected(self):
        r=self.saved()
        with self.assertRaisesRegex(ValueError,"already exists"):self.saved()
        self.final();self.trial.settle(r["paper_prediction_id"])
        with self.assertRaisesRegex(ValueError,"already recorded"):self.trial.settle(r["paper_prediction_id"])

    def test_quotes_are_observed_and_never_verified_closing_lines(self):
        r=self.saved();q=self.trial.capture_quote(r["paper_prediction_id"])
        self.assertFalse(q["verified_closing_line"])
        self.assertEqual(len(self.ledger._records(NHL_QUOTES)),1)
        self.assertEqual(len(self.ledger._records("sports_paper_quote")),0)

    def test_generation_crossing_start_and_failed_completion_save_nothing(self):
        def generate(g):self.now=START;return forecast()
        self.trial.forecast_fn=generate
        with self.assertRaisesRegex(ValueError,"started"):self.saved()
        self.assertEqual(self.store.rows,[])
        self.now=NOW;self.trial.forecast_fn=lambda g:{"probabilities":{"home":.5}}
        with self.assertRaises(ValueError):self.saved()
        self.assertEqual(self.store.rows,[])


class RuntimeTests(unittest.TestCase):
    def test_accepted_benchmark_model_and_promotion_gates_remain_unchanged(self):
        with v.app.app_context():d=v.status().get_json()
        self.assertEqual(d["sports_harness_version"],"sports-validation-v20-bounded-revision")
        self.assertEqual(d["sports_answer_model"],v.provider.GEMINI_MODEL)
        self.assertFalse(d["automatic_skill_activation_enabled"])
        self.assertFalse(d["sports_wager_execution_enabled"])
        self.assertFalse(d["sports_profitability_proven"])

    def test_nhl_categories_protected_from_general_rewrite_and_delete(self):
        for category in (NHL_PREDICTIONS,NHL_RESULTS,NHL_QUOTES):
            with self.subTest(category=category),patch.object(v.base,"get_memory",return_value={"category":category}):
                with self.assertRaises(ValueError):v.base.patch_memory_raw(1,"rewrite")
                with self.assertRaises(ValueError):v.base.delete_memory(1)

    def test_commands_strict_arguments_and_frozen_evidence(self):
        _,code=v.handle_message('sports nhl paper analyze :: {"event_id":"401892466","url":"https://example.com"}')
        self.assertEqual(code,409)
        r={"snapshot":game(),"forecast":forecast()}
        with patch.object(v.NHL_TRIAL,"_prediction",return_value=r):
            payload,code=v.handle_message('show nhl paper evidence :: {"paper_prediction_id":"NHP-TEST"}')
        self.assertEqual(code,200);self.assertEqual(payload["sports_paper"]["sha256"],digest(r))

    def test_combined_report_keeps_sports_separate(self):
        with patch.object(v.PAPER_TRIAL,"report",return_value={"pending":1}),patch.object(v.NHL_TRIAL,"report",return_value={"pending":2}):
            p,c=v.handle_message("show sports paper trials")
        self.assertEqual(c,200);self.assertEqual(p["sports_paper"],{"NFL":{"pending":1},"NHL":{"pending":2}})

    def test_model_uses_pinned_complete_provider_and_hockey_rules(self):
        def complete(messages,**kw):
            self.assertEqual(v.provider._TRAINING_PROVIDER_CONTEXT.get(),"gemini")
            self.assertTrue(v.provider._REQUIRE_FINISHED_RESPONSE_CONTEXT.get())
            self.assertIn("overtime and shootouts",messages[0]["content"])
            self.assertIn("null means unknown",messages[0]["content"])
            return json.dumps(forecast())
        with patch.object(v.ENGINE,"complete",side_effect=complete):self.assertEqual(v.nhl_forecast(game()),forecast())

    def test_nhl_chat_remains_private(self):
        r=v.app.test_client().post("/ui/chat",json={"message":"show nhl paper trial"})
        self.assertEqual(r.status_code,401)


if __name__ == "__main__":unittest.main()
