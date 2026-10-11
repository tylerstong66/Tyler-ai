import csv
import io
import json
import math
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sports_historical_benchmark as b


def game(identifier="g1", start="2020-09-01T17:00:00+00:00", season=2020, home="A", away="B", hs=21, aws=10, neutral=False, hp=-120, ap=110):
    return b.Game(identifier, season, 1, "REG", b.utc(start), home, away, neutral, hs, aws, hp, ap)


class HistoricalBenchmarkTests(unittest.TestCase):
    def test_current_game_scores_and_prices_cannot_change_features(self):
        prior = game()
        next_game = game("g2", "2020-09-08T17:00:00+00:00")
        original = b.chronological_features([prior, next_game])
        changed = b.chronological_features([prior, replace(next_game, home_score=0, away_score=70, home_price=500, away_price=-800)])
        self.assertEqual(original[1]["x"], changed[1]["x"])

    def test_future_outcomes_do_not_change_any_earlier_row(self):
        games = [game(), game("g2", "2020-09-08T17:00:00+00:00"), game("g3", "2020-09-15T17:00:00+00:00")]
        changed = games[:2] + [replace(games[2], home_score=0, away_score=99)]
        self.assertEqual([r["x"] for r in b.chronological_features(games)], [r["x"] for r in b.chronological_features(changed)])

    def test_same_kickoff_cannot_consume_same_batch_result(self):
        rows = b.chronological_features([game("g2"), game("g1")])
        self.assertTrue(all(r["prior_results_used"] == 0 for r in rows))
        self.assertEqual(rows[0]["x"], rows[1]["x"])

    def test_24_hour_result_delay_and_strict_pre_kickoff_cutoff(self):
        first = game()
        exact = replace(game("exact"), kickoff=first.kickoff + timedelta(hours=24))
        later = replace(game("later"), kickoff=first.kickoff + timedelta(hours=25))
        rows = b.chronological_features([later, exact, first])
        self.assertEqual([r["prior_results_used"] for r in rows], [0, 0, 1])
        self.assertLessEqual(b.utc(rows[2]["latest_result_available_at"]), b.utc(rows[2]["cutoff"]))
        with self.assertRaises(ValueError):
            b.chronological_features([first], 3)

    def test_neutral_venue_has_no_home_venue_feature(self):
        self.assertEqual(b.PriorState().features(game(neutral=True))[2], 0)
        self.assertEqual(b.PriorState().features(game())[2], 1)

    def test_rest_is_derived_from_prior_games_not_csv_rest(self):
        state = b.PriorState()
        g = game("target", "2020-09-10T17:00:00+00:00")
        state.last_played["A"] = g.kickoff - timedelta(days=10)
        state.last_played["B"] = g.kickoff - timedelta(days=4)
        self.assertAlmostEqual(state.features(g)[3], 6 / 7)
        state.last_played["A"] = g.kickoff - timedelta(days=200)
        state.last_played["B"] = g.kickoff - timedelta(days=180)
        self.assertEqual(state.features(g)[3], 0)

    def test_season_transition_regresses_prior_rating(self):
        state = b.PriorState(); state.new_season(2020); state.ratings["A"] = 1800
        state.new_season(2021)
        self.assertEqual(state.ratings["A"], 1700)
        state.new_season(2021)
        self.assertEqual(state.ratings["A"], 1700)

    def test_missing_moneyline_excluded_from_paired_metrics_only(self):
        rows = b.chronological_features([game(hp=None)])
        metrics, paired = b.summarize(rows, {"weights": [0] * 5, "tie_probability": .01}, .5)
        self.assertEqual(metrics["games"], 1)
        self.assertEqual(metrics["paired_priced_decisive_games"], 0)
        self.assertIsNotNone(metrics["full_three_outcome_brier"])
        self.assertEqual(paired, [])

    def test_ties_have_full_score_and_are_not_two_way_market_results(self):
        rows = b.chronological_features([game(hs=10, aws=10)])
        metrics, paired = b.summarize(rows, {"weights": [0] * 5, "tie_probability": .01}, .5)
        self.assertEqual(metrics["ties"], 1)
        self.assertEqual(metrics["decisive_games"], 0)
        self.assertEqual(paired, [])
        self.assertAlmostEqual(metrics["full_three_outcome_log_loss"], -math.log(.01))

    def test_margin_and_rating_use_prior_scores_once(self):
        rows = b.chronological_features([game(), game("g2", "2020-09-08T17:00:00+00:00")])
        self.assertEqual(rows[1]["prior_results_used"], 1)
        self.assertAlmostEqual(rows[1]["x"][4], 22 / 14)
        self.assertGreater(rows[1]["x"][1], 0)

    def test_american_market_normalization(self):
        self.assertAlmostEqual(b.market_probability(game(hp=-100, ap=100)), .5)
        self.assertAlmostEqual(b.market_probability(game(hp=-200, ap=180)), (2/3) / ((2/3) + (100/280)))

    def test_injury_adapter_rejects_unverified_or_late_data(self):
        record = {"game_id": "g1", "source_url": "https://example.test/injuries", "publication_time_verified": True,
            "published_at": "2020-09-01T12:00:00Z", "retrieved_at": "2020-09-01T12:30:00Z"}
        cutoff = "2020-09-01T16:00:00Z"
        self.assertEqual(len(b.verified_observations([record], "g1", cutoff)), 1)
        for changes in ({"publication_time_verified": False}, {"retrieved_at": "2020-09-02T12:00:00Z"},
                        {"published_at": "2020-09-01T13:00:00Z"}, {"source_url": "http://example.test"}):
            with self.assertRaises(ValueError):
                b.verified_observations([record | changes], "g1", cutoff)
        self.assertEqual(b.verified_observations([record], "different-game", cutoff), [])

    def test_timezone_is_required_for_observation(self):
        with self.assertRaises(ValueError):
            b.utc("2020-09-01T12:00:00")

    def test_fitter_converges_and_probabilities_are_valid(self):
        games = [game(str(i), (b.utc("2020-09-01T17:00:00Z") + timedelta(days=7*i)).isoformat(), hs=21 if i%3 else 7) for i in range(15)]
        rows = b.chronological_features(games)
        model = b.fit(rows, .01)
        self.assertTrue(model["converged"])
        for row in rows:
            p = b.probabilities(model["weights"], row, .01)
            self.assertAlmostEqual(sum(p.values()), 1)
            self.assertTrue(all(math.isfinite(v) and 0 < v < 1 for v in p.values()))
        self.assertLess(b.objective(rows, model["weights"], .01), b.objective(rows, [0]*5, .01))
        with self.assertRaises(ValueError):
            b.fit(rows, 0)

    def test_bootstrap_is_reproducible_and_includes_all_week_rows(self):
        paired = [{"week": i%4, "model_brier": .6, "market_brier": .4} for i in range(12)]
        a = b.week_bootstrap(paired)
        self.assertEqual(a, b.week_bootstrap(paired))
        self.assertEqual(a["blocks"], 4)
        self.assertAlmostEqual(a["mean_model_minus_market"], .2)

    def make_snapshot(self, path, mutate_test=False):
        rows = []
        for season in (2020, 2021, 2022):
            for i in range(8):
                g = game(f"{season}-{i}", f"{season}-09-{1+i*3:02d}T17:00:00Z", season=season, hs=21 if i%3 else 7)
                if mutate_test and season == 2022:
                    g = replace(g, home_score=0, away_score=40)
                rows.append({"game_id":g.identifier,"season":season,"week":i+1,"game_type":"REG",
                    "gameday":g.kickoff.date().isoformat(),"gametime":"13:00","home_team":g.home,"away_team":g.away,
                    "home_score":g.home_score,"away_score":g.away_score,"home_moneyline":-120,"away_moneyline":110,"location":"Home"})
        with path.open("w",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        protocol={"snapshot_sha256":b.sha256(path.read_bytes()),"history":{"first":2020,"last":2022},
            "result_delay_hours":24,"train_seasons":[2020],"validation_seasons":[2021],"test_seasons":[2022],"penalties":[.001,.01]}
        return protocol

    def test_test_labels_cannot_change_selected_penalty_or_coefficients(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); reports=[];models=[]
            for suffix, changed in (("a",False),("b",True)):
                snapshot=root/(suffix+".csv");protocol=self.make_snapshot(snapshot,changed)
                config=root/(suffix+".json");config.write_text(json.dumps(protocol))
                reports.append(b.run_benchmark(snapshot,config,root/suffix))
                models.append(json.loads((root/suffix/"model.json").read_text()))
            self.assertEqual(models[0]["weights"],models[1]["weights"])
            self.assertEqual(reports[0]["selection"],reports[1]["selection"])
            self.assertEqual(models[0]["tie_probability"],models[1]["tie_probability"])
            self.assertNotEqual(reports[0]["test"],reports[1]["test"])

    def test_snapshot_hash_and_existing_output_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);snapshot=root/"data.csv";protocol=self.make_snapshot(snapshot)
            config=root/"protocol.json";config.write_text(json.dumps(protocol));output=root/"run"
            b.run_benchmark(snapshot,config,output)
            with self.assertRaises(ValueError): b.run_benchmark(snapshot,config,output)
            snapshot.write_text(snapshot.read_text()+"\n")
            with self.assertRaises(ValueError): b.run_benchmark(snapshot,config,root/"new")
            self.assertFalse((root/"new").exists())

    def test_eastern_kickoff_and_relocated_team_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"data.csv";self.make_snapshot(path)
            data=path.read_text().replace(",A,B,",",OAK,SD,")
            path.write_text(data)
            g=b.read_games(path,2020,2022)[0]
            self.assertEqual(g.kickoff.hour,17)
            self.assertEqual((g.home,g.away),("LV","LAC"))

    def test_invalid_duplicate_or_unknown_venue_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"data.csv";self.make_snapshot(path)
            original=path.read_text();path.write_text(original+original.splitlines()[1]+"\n")
            with self.assertRaises(ValueError): b.read_games(path,2020,2022)
            path.write_text(original.replace("Home","Unknown"))
            with self.assertRaises(ValueError): b.read_games(path,2020,2022)


if __name__ == "__main__":
    unittest.main()
