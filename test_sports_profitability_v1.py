"""Synthetic only: never contributes to prospective evidence or a wagering record."""
import copy
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

import sports_profitability_v1 as p
import sports_profitability_selection as selection


def seal(value):
    value.pop("sha256", None)
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
        self.official_final = {"id": 2026020999, "gameType": 2,
            "gameState": "OFF", "gameScheduleState": "OK",
            "startTimeUTC": "2026-10-24T19:00:00Z",
            "homeTeam": {"id": 22, "abbrev": "PHI", "score": 3},
            "awayTeam": {"id": 6, "abbrev": "BOS", "score": 2}}
        self.espn_final = {"events": [{
            "id": "401899999", "date": "2026-10-24T19:00:00Z",
            "status": {"type": {"state": "post", "completed": True}},
            "competitions": [{"competitors": [
                {"homeAway": "home", "team": {"abbreviation": "PHI"}, "score": "3"},
                {"homeAway": "away", "team": {"abbreviation": "BOS"}, "score": "2"}
            ]}]}]}
        self.final1 = self.source("official.json", json.dumps(self.official_final).encode(),
            "https://api-web.nhle.com/v1/gamecenter/2026020999/landing",
            "2026-10-25T02:00:00Z")
        self.final2 = self.source("independent.json", json.dumps(self.espn_final).encode(),
            "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates=20261024",
            "2026-10-25T02:01:00Z")
        self.identity = {"game_id": "2026020999", "event_id": "401899999", "home": "PHI", "away": "BOS",
                         "kickoff": "2026-10-24T19:00:00Z"}
        self.entry_quote = self.quote(self.entry, "entry", "2026-10-23T17:59:00Z",
                                      "2026-10-23T18:01:00Z", {"home": -110, "away": 110})
        feature = (math.log(.60 / .40) - p.MODEL_WEIGHTS[0]) / p.MODEL_WEIGHTS[1]
        self.original = seal({**self.identity, "sport": "NHL",
                              "generated_at": "2026-10-23T18:02:00Z",
                              "recorded_at": "2026-10-23T18:02:10Z",
                              "model_sha256": p.MODEL_SHA,
                              "features": [1, feature],
                              "model": {"home": .60, "away": .40},
                              "NO_BET": True, "actual_wagers": 0})
        original_path = "benchmarks/two_way_prospective/nhl/predictions/2026020999.json"
        original_bytes = (json.dumps(self.original, sort_keys=True, indent=2) + "\n").encode()
        self.original_archive = self.source(original_path, original_bytes,
            "https://github.com/tylerstong66/Tyler-ai/blob/main/" + original_path,
            "2026-10-23T18:02:30Z")
        self.pred = seal({**self.identity, "generated_at": "2026-10-23T18:02:00Z",
                          "recorded_at": "2026-10-23T18:03:00Z",
                          "model_sha256": p.MODEL_SHA,
                          "probabilities": {"home": .60, "away": .40},
                          "entry_quote_sha256": self.entry_quote["sha256"],
                          "source_prediction_sha256": self.original["sha256"],
                          "source_prediction_archive": self.original_archive,
                          "NO_BET": True, "actual_wagers": 0})
        self.selection = selection.make_receipt(self.pred, self.entry_quote,
            self.root, "2026-10-23T18:04:00Z")
        self.result = seal({**self.identity, "prediction_sha256": self.pred["sha256"],
                            "independent_final_verified": True, "outcome": "home",
                            "scores": {"home": 3, "away": 2},
                            "verified_at": "2026-10-25T02:02:00Z",
                            "final_sources": [self.final1, self.final2],
                            "NO_BET": True, "actual_wagers": 0})
        self.close_quote = self.quote(self.closing, "verified_closing", "2026-10-24T18:57:00Z",
                                      "2026-10-24T18:59:00Z", {"home": -130, "away": 115},
                                      verified=True)

    def source(self, path, content, url, at):
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
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

    def evaluate(self, predictions=None, quotes=None, results=None, closing=None,
                 selections=None):
        return p.evaluate([self.pred] if predictions is None else predictions,
                          [self.entry_quote] if quotes is None else quotes,
                          [self.result] if results is None else results,
                          [self.close_quote] if closing is None else closing,
                          self.root,
                          [self.selection] if selections is None else selections)

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

    def test_unsealed_hindsight_selection_never_counts_toward_return(self):
        report = self.evaluate(selections=[])
        self.assertEqual(report["missing_pre_event_selection_receipt"], 1)
        self.assertEqual(report["paper_selections"], 0)
        self.assertEqual(report["paper_settled"], 0)
        self.assertIsNone(report["paper_roi"])

    def test_paper_selection_receipt_is_exclusive_and_not_wager(self):
        self.assertTrue(self.selection["NO_BET"])
        self.assertEqual(self.selection["actual_wagers"], 0)
        self.assertEqual(self.selection["paper_selection_side"], "home")
        self.assertEqual(self.selection["paper_stake_units"], 1)
        path = self.root / "paper_selections" / "2026020999.json"
        selection.persist_exclusive(path, self.selection)
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            selection.persist_exclusive(path, self.selection)
        self.assertEqual(path.read_bytes(), original)

    def test_rehashed_wrong_side_or_stake_cannot_rewrite_frozen_decision(self):
        for changes in ({"paper_selection_side": "away"},
                        {"paper_stake_units": 2},
                        {"maximum_model_expected_unit_return": 1.5},
                        {"recorded_at": "2026-10-25T01:00:00Z"}):
            with self.subTest(changes=changes):
                receipt = copy.deepcopy(self.selection)
                receipt.update(changes)
                seal(receipt)
                with self.assertRaises(ValueError):
                    self.evaluate(selections=[receipt])

    def test_stale_pre_event_paper_selection_receipts_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "too delayed"):
            selection.make_receipt(self.pred, self.entry_quote, self.root,
                                   "2026-10-23T18:15:00Z")
        altered = copy.deepcopy(self.selection)
        altered["recorded_at"] = "2026-10-23T18:15:00Z"
        seal(altered)
        with self.assertRaisesRegex(ValueError, "stale"):
            self.evaluate(selections=[altered])

    def test_refuse_retrospective_receipt_creation_after_kickoff(self):
        with self.assertRaisesRegex(ValueError, "before kickoff"):
            selection.make_receipt(self.pred, self.entry_quote, self.root,
                                   "2026-10-25T01:00:00Z")

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
        quote = copy.deepcopy(self.entry_quote)
        quote["prices"] = {"home": -200, "away": 110}
        seal(quote)
        pred = copy.deepcopy(self.pred)
        pred["entry_quote_sha256"] = quote["sha256"]
        seal(pred)
        result = copy.deepcopy(self.result)
        result["prediction_sha256"] = pred["sha256"]
        seal(result)
        receipt = selection.make_receipt(pred, quote, self.root,
            "2026-10-23T18:04:00Z")
        report = self.evaluate(predictions=[pred], quotes=[quote], results=[result],
                               closing=[], selections=[receipt])
        self.assertEqual(report["no_paper_selection"], 1)
        self.assertEqual(report["paper_selections"], 0)
        self.assertEqual(report["graded_probability_forecasts"], 1)
        self.assertIsNone(report["paper_roi"])

    def test_cannot_claim_different_probabilities_under_frozen_model_sha(self):
        altered = copy.deepcopy(self.pred)
        altered["probabilities"] = {"home": .75, "away": .25}
        seal(altered)
        with self.assertRaisesRegex(ValueError, "replay/paper probability mismatch"):
            self.evaluate(predictions=[altered], closing=[])

    def test_original_frozen_forecast_model_fingerprint_and_archive_must_match(self):
        altered = copy.deepcopy(self.pred)
        altered["source_prediction_sha256"] = "f" * 64
        seal(altered)
        with self.assertRaisesRegex(ValueError, "digest linkage"):
            self.evaluate(predictions=[altered], closing=[])
        original_path = self.root / self.original_archive["path"]
        original_path.write_bytes(original_path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "original source bytes|SHA-256"):
            self.evaluate(closing=[])

    def test_original_model_features_cannot_be_faked_even_if_rehashed(self):
        bad_original = copy.deepcopy(self.original)
        bad_original["features"][1] += 1
        seal(bad_original)
        path = self.original_archive["path"]
        contents = (json.dumps(bad_original, sort_keys=True, indent=2) + "\n").encode()
        (self.root / path).write_bytes(contents)
        updated_source = copy.deepcopy(self.original_archive)
        updated_source["sha256"] = hashlib.sha256(contents).hexdigest()
        pred = copy.deepcopy(self.pred)
        pred["source_prediction_sha256"] = bad_original["sha256"]
        pred["source_prediction_archive"] = updated_source
        seal(pred)
        with self.assertRaisesRegex(ValueError, "replay/paper probability mismatch"):
            self.evaluate(predictions=[pred], closing=[])

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

    def test_reject_final_winner_mislabel_even_with_valid_saved_hash(self):
        modified = copy.deepcopy(self.result)
        modified["outcome"] = "away"
        seal(modified)
        with self.assertRaisesRegex(ValueError, "winner"):
            self.evaluate(results=[modified], closing=[])

    def test_reject_false_reported_scores_even_when_result_rehashed(self):
        modified = copy.deepcopy(self.result)
        modified["scores"]["home"] = 4
        seal(modified)
        with self.assertRaisesRegex(ValueError, "scores"):
            self.evaluate(results=[modified], closing=[])

    def test_reject_independent_espn_score_disagreement_even_with_matching_hash(self):
        data = copy.deepcopy(self.espn_final)
        data["events"][0]["competitions"][0]["competitors"][0]["score"] = "4"
        raw = json.dumps(data).encode()
        (self.root / "independent.json").write_bytes(raw)
        edited = copy.deepcopy(self.result)
        edited["final_sources"][1]["sha256"] = hashlib.sha256(raw).hexdigest()
        seal(edited)
        with self.assertRaisesRegex(ValueError, "disagree"):
            self.evaluate(results=[edited], closing=[])

    def test_reject_espn_start_or_opponent_mismatch_not_rewritten_from_result(self):
        for key, value in (("date", "2026-10-24T19:01:00Z"),
                           ("team", "TOR")):
            with self.subTest(key=key):
                data = copy.deepcopy(self.espn_final)
                if key == "date":
                    data["events"][0]["date"] = value
                else:
                    data["events"][0]["competitions"][0]["competitors"][1]["team"]["abbreviation"] = value
                raw = json.dumps(data).encode()
                (self.root / "independent.json").write_bytes(raw)
                edited = copy.deepcopy(self.result)
                edited["final_sources"][1]["sha256"] = hashlib.sha256(raw).hexdigest()
                seal(edited)
                with self.assertRaises(ValueError):
                    self.evaluate(results=[edited], closing=[])

    def test_reject_unrelated_final_bytes_from_correct_source_hosts(self):
        raw = json.dumps({"events": []}).encode()
        (self.root / "independent.json").write_bytes(raw)
        changed = copy.deepcopy(self.result)
        changed["final_sources"][1]["sha256"] = hashlib.sha256(raw).hexdigest()
        seal(changed)
        with self.assertRaisesRegex(ValueError, "Exactly one pinned ESPN"):
            self.evaluate(results=[changed], closing=[])

    def test_reject_final_source_recorded_before_original_event_started(self):
        altered = copy.deepcopy(self.result)
        altered["final_sources"][0]["retrieved_at"] = "2026-10-24T18:59:00Z"
        seal(altered)
        with self.assertRaisesRegex(ValueError, "obtained after kickoff"):
            self.evaluate(results=[altered], closing=[])

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

    def test_direct_final_source_verifier_requires_original_hashes(self):
        from sports_profitability_nhl_finals import verify_final_sources
        evidence = copy.deepcopy(self.result['final_sources'])
        evidence[0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            verify_final_sources(self.pred, self.result, evidence, self.root)

    def test_direct_final_source_verifier_rejects_redirected_original(self):
        from sports_profitability_nhl_finals import verify_final_sources
        target = self.root/self.final1['path']
        moved = self.root/'redirected.json'
        target.rename(moved); target.symlink_to(moved)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            verify_final_sources(self.pred, self.result, self.result['final_sources'], self.root)

    def test_direct_final_source_verifier_bounds_original_before_opening(self):
        from sports_profitability_nhl_finals import verify_final_sources
        from unittest.mock import patch
        target = self.root/self.final1['path']
        with target.open('wb') as stream:
            stream.truncate(4_000_001)
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('Unbounded read')):
            with self.assertRaisesRegex(ValueError, 'Oversized'):
                verify_final_sources(self.pred, self.result, self.result['final_sources'], self.root)


if __name__ == "__main__":
    unittest.main()
