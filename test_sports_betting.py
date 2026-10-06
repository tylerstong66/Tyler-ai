import copy
import json
import unittest
from datetime import datetime, timezone

from sports_betting import SportsLedger, evaluate_snapshot, price_analysis, implied_probability
from sports_validation import SportsValidation, HOLDOUTS
from test_v2_18_skill_lab import MemoryStore, FakeEngine
from skill_lab import SkillPromotionLab

NOW = "2026-10-06T15:00:00+00:00"


def snapshot():
    return {
        "event": "Synthetic NFL fixture", "market": "receiving_yards", "selection": "Over",
        "line": 52.5, "event_start": "2026-10-07T00:00:00Z", "indoor": True,
        "odds": 150, "p_win": 0.47, "p_low": 0.43, "p_high": 0.51,
        "probability_method": "synthetic distribution", "rationale": "Illustrative fixture, not a live tip.",
        "evidence": {kind: {"summary": "Synthetic supplied evidence", "source_url": "https://example.com/fixture",
                            "captured_at": NOW} for kind in ("odds", "availability", "usage")},
    }


class SportsMathTests(unittest.TestCase):
    def test_plus_150_edge_and_ev(self):
        result = price_analysis(150, .47)
        self.assertAlmostEqual(result["implied_probability"], .4)
        self.assertAlmostEqual(result["edge_percentage_points"], 7)
        self.assertAlmostEqual(result["expected_profit_per_unit"], .175)

    def test_negative_odds(self):
        result = price_analysis(-125, .59)
        self.assertAlmostEqual(result["implied_probability"], 5/9)
        self.assertAlmostEqual(result["expected_profit_per_unit"], .062)

    def test_push_probabilities_are_conditioned_consistently(self):
        result = price_analysis(-110, .49, .08)
        self.assertAlmostEqual(result["expected_profit_per_unit"], .49*100/110-.43)
        self.assertAlmostEqual(result["estimated_probability_given_no_push"], .49/.92)
        self.assertGreater(result["edge_percentage_points"], 0)

    def test_two_way_vig_does_not_turn_fair_coin_into_value(self):
        result = price_analysis(-110, .5, opposite_odds=-110)
        self.assertAlmostEqual(result["no_vig_market_probability"], .5)
        self.assertLess(result["expected_profit_per_unit"], 0)

    def test_invalid_odds_and_probabilities(self):
        for odds in (0, 99, -99, 150.5, True, float("nan"), float("inf"), "bad"):
            with self.subTest(odds=odds), self.assertRaises(ValueError):
                implied_probability(odds)
        for p in (47, -.1, True, float("nan")):
            with self.subTest(p=p), self.assertRaises(ValueError):
                price_analysis(150, p)
        with self.assertRaises(ValueError):
            price_analysis(150, .95, .1)


class SnapshotTests(unittest.TestCase):
    def test_value_candidate_is_not_a_verified_live_recommendation(self):
        result = evaluate_snapshot(snapshot(), NOW)
        self.assertEqual(result["decision"], "VALUE CANDIDATE")
        self.assertFalse(result["profitability_proven"])
        self.assertFalse(result["wager_executed"])
        self.assertIn("not_independently_verified", result["evidence_origin"])

    def test_uncertainty_overrules_positive_point_estimate(self):
        data = snapshot()
        data.update(odds=-125, p_win=.59, p_low=.52, p_high=.64)
        self.assertEqual(evaluate_snapshot(data, NOW)["decision"], "NO BET")

    def test_missing_or_stale_availability_means_no_bet(self):
        for absent in (True, False):
            data = snapshot()
            if absent:
                del data["evidence"]["availability"]
            else:
                data["evidence"]["availability"]["captured_at"] = "2026-10-02T00:00:00Z"
            self.assertEqual(evaluate_snapshot(data, NOW)["decision"], "NO BET")

    def test_future_data_is_not_current(self):
        data = snapshot()
        data["evidence"]["odds"]["captured_at"] = "2026-10-06T15:01:00Z"
        self.assertEqual(evaluate_snapshot(data, NOW)["decision"], "NO BET")

    def test_outdoor_and_unknown_venue_require_weather(self):
        for indoor in (False, "true", None):
            data = snapshot()
            data["indoor"] = indoor
            self.assertEqual(evaluate_snapshot(data, NOW)["decision"], "NO BET")

    def test_naive_correlated_parlay_is_rejected(self):
        data = snapshot()
        data.update(is_parlay=True, joint_probability_method="independent_product")
        self.assertEqual(evaluate_snapshot(data, NOW)["decision"], "NO BET")

    def test_started_event_is_no_bet(self):
        data = snapshot()
        data["event_start"] = NOW
        self.assertEqual(evaluate_snapshot(data, NOW)["decision"], "NO BET")

    def test_missing_range_and_naive_timestamp_are_invalid(self):
        data = snapshot()
        del data["p_low"]
        with self.assertRaises(ValueError):
            evaluate_snapshot(data, NOW)
        data = snapshot()
        data["event_start"] = "2026-10-07T00:00:00"
        with self.assertRaises(ValueError):
            evaluate_snapshot(data, NOW)

    def test_credential_bearing_sources_are_not_persistable(self):
        for url in ("http://example.com", "https://user:pass@example.com", "https://example.com?api_key=abc"):
            data = snapshot()
            data["evidence"]["odds"]["source_url"] = url
            with self.subTest(url=url), self.assertRaises(ValueError):
                evaluate_snapshot(data, NOW)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.now = NOW
        self.ledger = SportsLedger(self.store.get_rows, self.store.save_row, lambda: self.now)

    def record(self):
        return self.ledger.record_prediction(snapshot(), 1, "fixture-model")

    def test_prediction_is_a_frozen_copy(self):
        data = snapshot()
        saved = self.ledger.record_prediction(data, 1, "fixture-model")
        data["selection"] = "Under"
        self.assertEqual(saved["snapshot"]["selection"], "Over")
        self.assertEqual(self.ledger.report()["predictions_in_window"], 1)

    def test_pre_event_only_and_confirmed_persistence(self):
        self.now = "2026-10-08T00:00:00Z"
        with self.assertRaises(ValueError):
            self.record()
        self.assertEqual(self.store.rows, [])
        self.now = NOW
        self.ledger.save_row = lambda *args: []
        with self.assertRaises(RuntimeError):
            self.record()

    def test_results_append_without_altering_original_and_report_paper_roi(self):
        prediction = self.record()
        original_row = copy.deepcopy(self.store.rows[0])
        self.now = "2026-10-08T00:00:00Z"
        result = self.ledger.settle(prediction["prediction_id"], "win", "https://example.com/result", 130, 52.5)
        self.assertEqual(original_row, self.store.rows[0])
        self.assertAlmostEqual(result["flat_unit_profit"], 1.5)
        self.assertGreater(result["price_clv_percentage_points"], 0)
        report = self.ledger.report()
        self.assertAlmostEqual(report["hypothetical_flat_unit_roi"], 1.5)
        self.assertAlmostEqual(report["conditional_brier_score"], (.47-1)**2)
        self.assertFalse(report["profitability_proven"])

    def test_changed_line_cannot_be_called_price_clv(self):
        prediction = self.record()
        self.now = "2026-10-08T00:00:00Z"
        result = self.ledger.settle(prediction["prediction_id"], "loss", "https://example.com/result", 130, 55.5)
        self.assertIsNone(result["price_clv_percentage_points"])

    def test_settlement_cannot_precede_event_or_rewrite_result(self):
        prediction = self.record()
        with self.assertRaises(ValueError):
            self.ledger.settle(prediction["prediction_id"], "win", "https://example.com/result")
        self.now = "2026-10-08T00:00:00Z"
        self.ledger.settle(prediction["prediction_id"], "loss", "https://example.com/result")
        with self.assertRaises(ValueError):
            self.ledger.settle(prediction["prediction_id"], "win", "https://example.com/result")

    def test_integrity_failure_is_reported_not_hidden(self):
        self.record()
        row = json.loads(self.store.rows[0]["memories"])
        row["payload"]["snapshot"]["selection"] = "Under"
        self.store.rows[0]["memories"] = json.dumps(row)
        with self.assertRaises(RuntimeError):
            self.ledger.report()

    def test_no_records_means_unknown_metrics(self):
        report = self.ledger.report()
        self.assertIsNone(report["hypothetical_flat_unit_roi"])
        self.assertIsNone(report["conditional_brier_score"])


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.lab.bootstrap_sports_betting_skill()
        self.validation = SportsValidation(self.lab, self.store.get_rows, self.store.save_row, "gemini", "fixture-model", lambda: NOW)
        self.lab._run = lambda *args: "fixture output, not a real model call"
        self.lab._judge = lambda profile, case, output: {"case_id": case["case_id"], "score": 95, "passed": True, "output": output}

    def test_complete_requires_two_full_baselines_and_separate_holdouts(self):
        session = self.validation.start()
        self.assertEqual(session["total_cases"], 25)
        for _ in range(24):
            session = self.validation.advance()
        self.assertEqual(session["status"], "running")
        session = self.validation.advance()
        self.assertEqual(session["status"], "passed")
        self.assertEqual(session["metrics"]["holdout"]["case_count"], 5)
        self.assertFalse(session["profitability_proven"])
        self.assertFalse({c["case_id"] for c in HOLDOUTS} & {c["case_id"] for c in self.lab.benchmark_cases("Sports Betting Analyst")})
        baselines = self.lab.evaluations("Sports Betting Analyst", "active")
        self.assertEqual(len(baselines), 2)
        self.assertTrue(all(run["case_count"] == 10 for run in baselines))
        self.assertTrue(all(run["evaluation_model"] == "fixture-model" for run in baselines))

    def test_failure_does_not_advance_persisted_checkpoint(self):
        self.validation.start()
        def fail(*args):
            raise RuntimeError("Provider quota exhausted")
        self.lab._run = fail
        with self.assertRaises(RuntimeError):
            self.validation.advance()
        self.assertEqual(self.validation.latest()["completed_cases"], 0)

    def test_single_failed_case_fails_readiness_even_with_high_average(self):
        self.validation.start()
        self.lab._judge = lambda profile, case, output: {"case_id": case["case_id"], "score": 79, "passed": False}
        self.validation.advance()
        self.lab._judge = lambda profile, case, output: {"case_id": case["case_id"], "score": 100, "passed": True}
        for _ in range(24):
            session = self.validation.advance()
        self.assertEqual(session["status"], "failed")

    def test_changed_model_or_profile_invalidates_previous_checkpoint(self):
        self.validation.start()
        self.validation.model = "different-model"
        self.assertIsNone(self.validation.latest())
        with self.assertRaises(ValueError):
            self.validation.advance()
        self.validation.start()
        self.engine.skills["sports-betting-analyst"]["instructions"].append("new instruction")
        self.assertIsNone(self.validation.latest())

    def test_unconfirmed_save_is_not_success(self):
        self.validation.save_row = lambda *args: []
        with self.assertRaises(RuntimeError):
            self.validation.start()

    def test_partial_baseline_is_not_available_to_champion_training(self):
        self.validation.start()
        for _ in range(9):
            self.validation.advance()
        self.assertEqual(self.lab.evaluations("Sports Betting Analyst", "active"), [])
        self.validation.advance()
        self.assertEqual(len(self.lab.evaluations("Sports Betting Analyst", "active")), 1)


if __name__ == "__main__":
    unittest.main()
