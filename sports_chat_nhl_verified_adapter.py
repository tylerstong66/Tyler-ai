"""Read-only NHL chat adapter backed by the original prospective paper gates.

No network fetch, retrospective reconstruction, source certification, bet, or
model promotion occurs here. Callers must independently attest publication
timing and original source identity; this adapter validates retained bytes.
"""
from datetime import datetime, timezone

from sports_profitability_v1 import (
    ACTIVATION, BOOK, MARKET, MODEL_SHA, check_prediction, check_quote,
    decimal_odds, utc, verify_original_prediction,
)


def nhl_verified_chat_comparison(prediction, entry_quote, archive_root, now=None):
    """Evaluate a prospective NHL pair, failing closed on any evidence defect."""
    try:
        check_prediction(prediction)
        if utc(prediction["recorded_at"]) < utc(ACTIVATION):
            raise ValueError("Not a prospective activated model record")
        verify_original_prediction(prediction, archive_root)
        prices = check_quote(entry_quote, prediction, archive_root, "entry")
        clock = utc(now or datetime.now(timezone.utc).isoformat())
        if not (utc(prediction["recorded_at"]) <= clock < utc(prediction["kickoff"])):
            raise ValueError("Model record is future-dated or event already started")
        if utc(entry_quote["recorded_at"]) > clock:
            raise ValueError("Quote was not available at evaluation time")
        probabilities = prediction["probabilities"]
        outcomes = {}
        for side in ("home", "away"):
            decimal = decimal_odds(prices[side])
            outcomes[side] = {
                "model_probability": probabilities[side],
                "american_odds": prices[side],
                "implied_probability": 1 / decimal,
                "hypothetical_ev_per_unit": probabilities[side] * decimal - 1,
            }
        return {
            "status": "hypothetical_only",
            "sport": "NHL",
            "model_sha256": MODEL_SHA,
            "book": BOOK,
            "market": MARKET,
            "game_id": prediction["game_id"],
            "kickoff": prediction["kickoff"],
            "prediction_sha256": prediction["sha256"],
            "entry_quote_sha256": entry_quote["sha256"],
            "outcomes": outcomes,
            "NO_BET": True,
            "caveat": ("Original byte checks do not independently certify provider truth, "
                       "server publication timing, or sportsbook executability."),
        }
    except (ValueError, TypeError, KeyError, OSError, OverflowError) as exc:
        return {
            "status": "unavailable",
            "reason": str(exc),
            "NO_BET": True,
        }
