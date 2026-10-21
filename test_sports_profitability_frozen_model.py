"""Regression contract: match the real untouched NHL Elo model and saved forecasts.

These are integrity tests, not an evaluation of profitability. The samples are
historical source records and MUST NEVER enter the future paper ROI population.
"""
import hashlib
import json
import math
import unittest
from pathlib import Path

import sports_profitability_v1 as profit

MODEL = Path("benchmarks/two_way_prospective/nhl/model.json")
ORIGINALS = Path("benchmarks/two_way_prospective/nhl/predictions")
SAMPLE_IDS = ("2026020084", "2026020121", "2026020151")


class ActualFrozenModelIdentityTests(unittest.TestCase):
    def test_fixed_model_digest_matches_unchanged_real_model_file(self):
        model = json.loads(MODEL.read_bytes())
        canonical = json.dumps(model, sort_keys=True, separators=(",", ":"),
                               allow_nan=False).encode()
        digest = hashlib.sha256(canonical).hexdigest()
        self.assertEqual(digest, profit.MODEL_SHA)
        self.assertEqual(model["sport"], "NHL")
        self.assertEqual(model["weights"], list(profit.MODEL_WEIGHTS))
        self.assertEqual(model["features"], ["intercept", "elo_difference_200"])
        self.assertTrue(model["training_only_no_independent_validation"])
        self.assertFalse(model["availability_effect_enabled"])

    def test_three_original_archived_nhl_forecasts_match_exact_frozen_sha(self):
        for game_id in SAMPLE_IDS:
            with self.subTest(game_id=game_id):
                original = json.loads((ORIGINALS / (game_id + ".json")).read_bytes())
                profit.verify_record(original)
                self.assertEqual(original["model_sha256"], profit.MODEL_SHA)
                self.assertEqual(original["game_id"], game_id)
                self.assertLess(profit.utc(original["generated_at"]),
                                profit.utc(original["recorded_at"]))
                self.assertLess(profit.utc(original["recorded_at"]),
                                profit.utc(original["kickoff"]))
                x = original["features"]
                z = sum(w * v for w, v in zip(profit.MODEL_WEIGHTS, x))
                home = 1.0 / (1.0 + math.exp(-z))
                self.assertAlmostEqual(home, original["model"]["home"], places=12)
                self.assertAlmostEqual(1 - home, original["model"]["away"], places=12)
                # Legacy forecasts are not future-only paper ROI samples.
                self.assertLess(profit.utc(original["recorded_at"]),
                                profit.utc(profit.ACTIVATION))

    def test_old_mistyped_identifier_is_never_accepted(self):
        pred = {
            "game_id": "synthetic_future", "event_id": "synthetic",
            "home": "PHI", "away": "BOS", "kickoff": "2026-10-24T19:00:00Z",
            "generated_at": "2026-10-23T18:02:00Z",
            "recorded_at": "2026-10-23T18:03:00Z",
            "model_sha256":
                "3ea760cc52051c9c094ffe33a9a2580256bbf7ab806f580babf7d217c039df3f",
            "probabilities": {"home": 0.6, "away": 0.4},
            "entry_quote_sha256": "f" * 64,
            "NO_BET": True, "actual_wagers": 0,
        }
        pred["sha256"] = profit.hash_record(pred)
        with self.assertRaisesRegex(ValueError, "Unfrozen or different"):
            profit.check_prediction(pred)

    def test_without_new_qualified_input_paper_returns_remain_unavailable(self):
        report = profit.evaluate([], [], [])
        self.assertEqual(report["forecast_count"], 0)
        self.assertEqual(report["paper_settled"], 0)
        self.assertIsNone(report["paper_roi"])
        self.assertIsNone(report["mean_price_clv_percentage_points"])
        self.assertEqual(report["actual_wagers"], 0)
        self.assertFalse(report["model_promotion_allowed"])


if __name__ == "__main__":
    unittest.main()
