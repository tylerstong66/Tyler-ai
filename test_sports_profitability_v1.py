"""Synthetic only: never contributes to prospective evidence or a wagering record."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

import sports_profitability_v1 as p


def seal(value):
    value["sha256"] = p.hash_record(value)
    return value


class ProfitabilityContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.entry = self.source("entry.json", b'{"synthetic":"entry"}', "https://example.com/entry",
                                 "2026-10-23T18:00:00Z")
        self.closing = self.source("closing.json", b'{"synthetic":"closing"}', "https://example.com/closing",
                                   "2026-10-24T18:58:00Z")
        self.final1 = self.source("official.json", b'{"synthetic":"final1"}', "https://api-web.nhle.com/official",
                                  "2026-10-25T02:00:00Z")
        self.final2 = self.source("independent.json", b'{"synthetic":"final2"}', "https://site.api.espn.com/independent",
                                  "2026-10-25T02:01:00Z")
        self.identity = {"game_id": "2026020999", "event_id": "401899999", "home": "PHI", "away": "BOS",
                         "kickoff": "2026-10-24T19:00:00Z"}
        self.entry_quote = self.quote(self.entry, "entry", "2026-10-23T17:59:00Z",
                                      "2026-10-23T18:01:00Z", {"home": -110, "away": 110})
        self.pred = seal({**self.identity, "generated_at": "2026-10-23T18:02:00Z",
                          "recorded_at": "2026-10-23T18:03:00Z",
                          "model_sha256": p.MODEL_SHA,
                          "probabilities": {"home": .60, "away": .40},
                          "entry_quote_sha256": self.entry_quote["sha256"],
                          "NO_BET": True, "actual_wagers": 0})
        self.result = seal({**self.identity, "prediction_sha256": self.pred["sha256"],
                            "independent_final_verified": True, "outcome": "home",
                            "verified_at": "2026-10-25T02:02:00Z",
                            "final_sources": [self.final1, self.final2],
                            "NO_BET": True, "actual_wagers": 0})
        self.close_quote = self.quote(self.closing, "verified_closing", "2026-10-24T18:57:00Z",
                                      "2026-10-24T18:59:00Z", {"home": -130, "away": 115},
                                      verified=True)

    def source(self, path, content, url, at):
        (self.root / path).write_bytes(content)
        return {"path": path, "source_url": url,
                "sha256": hashlib.sha256(content).hexdigest(), "retrieved_at": at}

    def quote(self, source, phase, published, recorded, prices, verified=False):
        return seal({**{
            "game_id": "2026020999", "event_id": "401899999", "home": "PHI", "away": "BOS",
            "kickoff": "2026-10-24T19:00:00Z"},
            "source_snapshot": source, "book_id": p.BOOK, "market": p.MARKET,
            "line": None, "prices": prices, "quote_phase": phase,
            "observed_at": source["retrieved_at"], "provider_updated_at": published,
            "recorded_at": recorded, "available_to_paper": True,
            "last_pre_start_offering_verified": verified,
            "NO_BET": True, "actual_wagers": 0})

    def evaluate(self, predictions=None, quotes=None, results=None, closing=None):
        return p.evaluate([self.pred] if predictions is None else predictions,
                          [self.entry_quote] if quotes is None else quotes,
                          [self.result] if results is None else results,
                          [self.close_quote] if closing is None else closing, self.root)

    def test_positive_paper_unit_and_comparable_clv_without_real_wagers(self):
        report = self.evaluate()
        self.assertEqual(report["paper_selections"], 1)
        self.assertEqual(report["paper_settled"], 1)
        self.assertEqual(report["wins"], 1)
        self.assertAlmostEqual(report["paper_roi"], 100 / 110)
        self.assertAlmostEqual(report["mean_price_clv_percentage_points"],
                               100 * (p.implied(-130) - p.implied(-110)))
        self.assertEqual(report["graded_probability_forecasts"], 1)
        self.assertAlmostEqual(report["binary_brier"], .32)
        self.assertIsNone(report["paper_roi_block_uncertainty"]["ci95"])
        self.assertTrue(report["NO_BET"])
        self.assertEqual(report["actual_wagers"], 0)
        self.assertFalse(report["profitability_proven"])

    def test_missing_quote_does_not_recreate_historical_offer(self):
        report = self.evaluate(quotes=[], closing=[])
        self.assertEqual(report["unpriced_or_missing_original_quote"], 1)
        self.assertIsNone(report["paper_roi"])
        self.assertIsNone(report["mean_price_clv_percentage_points"])
        self.assertEqual(report["graded_probability_forecasts"], 0)

    def test_future_only_activation(self):
        older = copy.deepcopy(self.pred)
        older.update(generated_at="2026-10-22T18:02:00Z", recorded_at="2026-10-22T18:03:00Z")
        seal(older)
        report = self.evaluate(predictions=[older], quotes=[], results=[], closing=[])
        self.assertEqual(report["excluded_pre_activation"], 1)
        self.assertEqual(report["paper_selections"], 0)

    def test_low_edge_no_selection_still_scores_probability(self):
        pred = copy.deepcopy(self.pred)
        pred["probabilities"] = {"home": 0.52, "away": 0.48}
        seal(pred)
        result = copy.deepcopy(self.result)
        result["prediction_sha256"] = pred["sha256"]
        seal(result)
        report = self.evaluate(predictions=[pred], results=[result], closing=[])
        self.assertEqual(report["no_paper_selection"], 1)
        self.assertEqual(report["paper_selections"], 0)
        self.assertEqual(report["graded_probability_forecasts"], 1)
        self.assertIsNone(report["paper_roi"])

    def test_tampering_and_past_start_are_rejected(self):
        wrong = copy.deepcopy(self.entry_quote)
        wrong["prices"]["home"] = -300
        with self.assertRaisesRegex(ValueError, "hash"):
            self.evaluate(quotes=[wrong], closing=[])
        altered = copy.deepcopy(self.pred)
        altered["recorded_at"] = "2026-10-25T20:00:00Z"
        seal(altered)
        with self.assertRaisesRegex(ValueError, "prior"):
            self.evaluate(predictions=[altered], closing=[])

    def test_mismatched_book_market_line_and_quote_age_fail_closed(self):
        for update in ({"book_id": "fan_duel"}, {"market": "nhl_regulation"},
                       {"line": 1.5}, {"provider_updated_at": "2026-10-23T16:00:00Z"},
                       {"recorded_at": "2026-10-23T18:08:00Z"}):
            with self.subTest(update=update):
                bad = copy.deepcopy(self.entry_quote)
                bad.update(update)
                seal(bad)
                pred = copy.deepcopy(self.pred)
                pred["entry_quote_sha256"] = bad["sha256"]
                seal(pred)
                with self.assertRaises(ValueError):
                    self.evaluate(predictions=[pred], quotes=[bad], results=[], closing=[])

    def test_closing_must_match_and_be_verified_last_offering(self):
        for update in ({"book_id": "another_book"}, {"line": 0.5},
                       {"last_pre_start_offering_verified": False},
                       {"observed_at": "2026-10-24T18:30:00Z"},
                       {"provider_updated_at": "2026-10-24T19:00:00Z"}):
            with self.subTest(update=update):
                bad = copy.deepcopy(self.close_quote)
                bad.update(update)
                seal(bad)
                with self.assertRaises(ValueError):
                    self.evaluate(closing=[bad])

    def test_result_source_collision_and_changed_identity_rejected(self):
        bad = copy.deepcopy(self.result)
        bad["final_sources"][1]["source_url"] = "https://api-web.nhle.com/second"
        seal(bad)
        with self.assertRaisesRegex(ValueError, "distinct"):
            self.evaluate(results=[bad], closing=[])
        bad = copy.deepcopy(self.result)
        bad["kickoff"] = "2026-10-24T20:00:00Z"
        seal(bad)
        with self.assertRaisesRegex(ValueError, "identity"):
            self.evaluate(results=[bad], closing=[])

    def test_original_archive_bytes_required(self):
        (self.root / "entry.json").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.evaluate(closing=[])

    def test_duplicate_event_refused(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.evaluate(predictions=[self.pred, self.pred], closing=[])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.evaluate(quotes=[self.entry_quote, self.entry_quote], closing=[])

    def test_pending_and_unverified_finals_are_not_losses(self):
        report = self.evaluate(results=[], closing=[])
        self.assertEqual(report["paper_pending"], 1)
        self.assertEqual(report["paper_settled"], 0)
        self.assertIsNone(report["paper_roi"])
        unverified = copy.deepcopy(self.result)
        unverified["independent_final_verified"] = False
        seal(unverified)
        self.assertEqual(self.evaluate(results=[unverified], closing=[])["paper_pending"], 1)

    def test_interval_requires_30_results_and_five_dates(self):
        self.assertIsNone(p.interval([{"day": "2026-10-24", "profit": .9}] * 40)["ci95"])
        rows = [{"day": f"2026-10-{24+i}", "profit": 1 if j % 2 else -1}
                for i in range(5) for j in range(6)]
        output = p.interval(rows)
        self.assertEqual(output["draws"], 1000)
        self.assertEqual(output["blocks"], 5)
        self.assertIsNotNone(output["ci95"])
        self.assertEqual(output, p.interval(rows))


if __name__ == "__main__":
    unittest.main()
