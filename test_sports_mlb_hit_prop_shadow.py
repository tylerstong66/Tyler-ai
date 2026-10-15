"""No-network tests for experimental MLB hitter 1+ hit/HR game shadow baseline."""
import copy
import math
import unittest
from datetime import date, timedelta

from sports_mlb_hit_prop_shadow import (
    parse_hitter_game_log, conditional_shadow_forecast,
    retrospective_walk_forward, retrieve_game_logs, _train, PRIORS
)

HITTER=683734


def game_row(day, game_id, ab=4, hits=1, hr=0, season=2025, game_type="R"):
    return {
        "date":day, "season":str(season), "gameType":game_type,
        "game":{"gamePk":game_id, "gameNumber":1},
        "player":{"id":HITTER,"fullName":"Synthetic Hitter"},
        "team":{"id":158},
        "stat":{"atBats":ab,"hits":hits,"homeRuns":hr,
                "plateAppearances":ab+1,"baseOnBalls":1}
    }


def envelope(rows):
    return {"stats":[{"type":{"displayName":"gameLog"},
                      "group":{"displayName":"hitting"}, "splits":rows}]}


class Parsing(unittest.TestCase):
    def test_game_ids_and_both_doubleheader_games_preserved(self):
        raw=envelope([game_row("2025-07-01",800001),
                      game_row("2025-07-01",800002,ab=0,hits=0),
                      game_row("2025-07-02",800003,ab=3,hits=2,hr=1)])
        parsed=parse_hitter_game_log(raw,HITTER,2025)
        self.assertEqual(len(parsed),3)
        self.assertEqual([x["game_id"] for x in parsed],[800001,800002,800003])
        self.assertFalse(parsed[1]["eligible_at_least_one_ab"])
        self.assertEqual((parsed[2]["has_hit"],parsed[2]["has_hr"]),(1,1))

    def test_duplicate_game_ids_and_wrong_hitter_are_rejected(self):
        row=game_row("2025-07-01",800001)
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            parse_hitter_game_log(envelope([row,copy.deepcopy(row)]),HITTER,2025)
        bad=copy.deepcopy(row);bad["player"]["id"]=99
        with self.assertRaisesRegex(ValueError,"identity"):
            parse_hitter_game_log(envelope([bad]),HITTER,2025)

    def test_bad_date_invalid_stats_and_future_season_split(self):
        row=game_row("2025-07-01",800001)
        for change in ({"date":"2025-02-30"},{"date":"2024-07-01"},
                       {"stat":{"atBats":3,"hits":4,"homeRuns":0,"plateAppearances":4}},
                       {"stat":{"atBats":True,"hits":0,"homeRuns":0,"plateAppearances":1}}):
            bad=copy.deepcopy(row);bad.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):
                parse_hitter_game_log(envelope([bad]),HITTER,2025)
        mixed=game_row("2026-07-01",800002,season=2026)
        self.assertEqual(len(parse_hitter_game_log(envelope([row,mixed]),HITTER,2025)),1)

    def test_wrong_game_type_is_excluded_and_missing_stats_fail_closed(self):
        mixed=game_row("2025-10-01",800002,game_type="W")
        self.assertEqual(parse_hitter_game_log(envelope([mixed]),HITTER,2025),[])
        bad=game_row("2025-06-01",800001);del bad["stat"]["atBats"]
        with self.assertRaisesRegex(ValueError,"atBats"):
            parse_hitter_game_log(envelope([bad]),HITTER,2025)


def sample():
    rows=[]
    start=date(2025,5,1)
    for i in range(45):
        day=(start+timedelta(days=i)).isoformat()
        rows.append(game_row(day,800000+i,hits=1 if (i%3 or i%13==0) else 0,hr=1 if i%13==0 else 0))
    for i in range(18):
        day=(date(2026,5,1)+timedelta(days=i)).isoformat()
        rows.append(game_row(day,900000+i,hits=1 if (i%2 or i%11==0) else 0,hr=1 if i%11==0 else 0,season=2026))
    return parse_hitter_game_log(envelope(rows[:45]),HITTER,2025)+parse_hitter_game_log(envelope(rows[45:]),HITTER,2026)


class ShadowBaselineTests(unittest.TestCase):
    def test_pregame_shadow_probability_is_conditional_and_not_actionable(self):
        rows=sample()
        forecast=conditional_shadow_forecast(rows,"2026-05-08T23:05:00Z")
        self.assertTrue(forecast["model_ready"])
        self.assertEqual(forecast["status"],"EXPERIMENTAL CONDITIONAL FREQUENCY - NO BET")
        self.assertEqual(forecast["actual_wager"],0)
        for kind in ("hit","hr"):
            estimate=forecast["estimates"][kind]
            self.assertTrue(0 < estimate["experimental_conditional_probability"] < 1)
            self.assertFalse(estimate["calibrated"])
            self.assertFalse(estimate["player_prop_betting_eligible"])
            self.assertEqual(estimate["condition"],"at_least_one_official_at_bat")

    def test_same_day_doubleheader_never_enrolls_into_same_day_model(self):
        rows=sample()
        cutoff="2026-05-08T23:05:00Z"
        first=conditional_shadow_forecast(rows,cutoff)
        plus=copy.deepcopy(rows)
        plus.append({
            **copy.deepcopy(rows[-1]),"game_id":990999,
            "game_day":"2026-05-08","has_hit":1,"hits":2,"has_hr":1,"hr":1})
        second=conditional_shadow_forecast(plus,cutoff)
        self.assertEqual(first["historical_input_sha256"],second["historical_input_sha256"])
        self.assertEqual(first["estimates"],second["estimates"])

    def test_minimum_history_enforced(self):
        self.assertIsNone(_train(sample()[:29]))
        self.assertIsNotNone(_train(sample()[:30]))
        report=conditional_shadow_forecast(sample()[:10],"2025-08-01T23:00:00Z")
        self.assertFalse(report["model_ready"])
        self.assertIsNone(report["estimates"])

    def test_retrospective_evaluation_frozen_at_each_game_date(self):
        report=retrospective_walk_forward(sample(),evaluation_season=2026)
        self.assertFalse(report["prospective_validation"])
        self.assertFalse(report["sportsbook_value_established"])
        self.assertTrue(report["no_wagers"])
        self.assertEqual(report["outcomes"]["hit"]["n_games_with_at_least_one_ab"],18)
        self.assertEqual(report["outcomes"]["hr"]["n_games_with_at_least_one_ab"],18)
        for kind in ("hit","hr"):
            result=report["outcomes"][kind]
            self.assertTrue(math.isfinite(result["model_brier"]))
            self.assertTrue(math.isfinite(result["model_log_loss"]))
            self.assertFalse(result["improvement_established"])

    def test_zero_ab_is_skipped_not_counted_as_zero_hit_game(self):
        rows=sample()
        row=copy.deepcopy(rows[-1]);row.update(game_id=912344,game_day="2026-05-21",
                                               ab=0,pa=1,hits=0,hr=0,
                                               eligible_at_least_one_ab=False,has_hit=0,has_hr=0)
        report=retrospective_walk_forward(rows+[row],evaluation_season=2026)
        self.assertEqual(report["skipped_zero_at_bats"],1)
        self.assertEqual(report["outcomes"]["hit"]["n_games_with_at_least_one_ab"],18)

    def test_last_80_games_window_and_fixed_prior_smoothing(self):
        rows=sample()
        rolling=_train(rows)
        self.assertEqual(rolling["hit"]["rolling_games"],63)
        k=sum(r["has_hit"] for r in rows)
        self.assertAlmostEqual(rolling["hit"]["experimental_conditional_probability"],
                               (k+20*PRIORS["hit"])/83,places=6)


class ReaderTests(unittest.TestCase):
    def test_official_reader_fetches_separate_seasons_and_preserves_receipts(self):
        class Stub:
            audit=[]
            def load(self,path,params=None):
                year=params["season"]
                d=envelope([game_row(f"{year}-07-01",800001+year,season=year)])
                receipt={"source_url":"https://statsapi.mlb.com/api/v1/"+path,
                         "retrieved_at":"2026-10-15T10:00:00Z","sha256":"synthetic"}
                self.audit.append(receipt)
                return d,receipt
        reader=Stub()
        rows,receipts=retrieve_game_logs(HITTER,[2025,2026],reader=reader)
        self.assertEqual(len(rows),2)
        self.assertEqual(len(receipts),2)
        self.assertEqual([x["season"] for x in rows],[2025,2026])
        with self.assertRaisesRegex(ValueError,"Duplicate season"):
            retrieve_game_logs(HITTER,[2025,2025],reader=reader)


if __name__=="__main__":
    unittest.main()
