"""Prospective-only immutable NHL paper decision receipts.

This module does not place wagers, poll sportsbook prices, or establish genuine
GitHub server publication time. A receipt is an offline-required prerequisite,
never independent evidence that an original sportsbook quote was executable.
"""
import json
import math
from datetime import timedelta
from pathlib import Path

from sports_profitability_v1 import (
    ACTIVATION, MIN_EV, UNIT_STAKE, check_prediction, check_quote, decimal_odds,
    hash_record, same_event, utc, verify_original_prediction, verify_record,
)

POLICY_ID = "future-only-nhl-fixed-unit-v1"


def compute_decision(prediction, prices):
    probs = prediction["probabilities"]
    ev = {s: probs[s] * decimal_odds(prices[s]) - 1 for s in ("home", "away")}
    best = max(("home", "away"), key=lambda s: (ev[s], s == "home"))
    eligible = ev[best] >= MIN_EV
    return {
        "paper_selection_side": best if eligible else None,
        "paper_stake_units": UNIT_STAKE if eligible else 0,
        "maximum_model_expected_unit_return": ev[best],
    }


def make_receipt(prediction, entry_quote, archive_root, recorded_at):
    check_prediction(prediction)
    if utc(prediction["recorded_at"]) < utc(ACTIVATION):
        raise ValueError("No retrospective paper selection is permitted")
    verify_original_prediction(prediction, archive_root)
    prices = check_quote(entry_quote, prediction, archive_root, "entry")
    clock = utc(recorded_at)
    if not (
            utc(prediction["recorded_at"]) <= clock
            and utc(entry_quote["recorded_at"]) <= clock
            and clock < utc(prediction["kickoff"])):
        raise ValueError("Original paper selection must be recorded before kickoff")
    if (clock - utc(prediction["recorded_at"]) > timedelta(minutes=5)
            or clock - utc(entry_quote["observed_at"]) > timedelta(minutes=10)):
        raise ValueError("Paper selection receipt is too delayed after original forecast/quote")
    details = compute_decision(prediction, prices)
    record = {
        **{key: prediction[key] for key in (
            "game_id", "event_id", "home", "away", "kickoff")},
        "policy": POLICY_ID, "recorded_at": recorded_at,
        "prediction_sha256": prediction["sha256"],
        "entry_quote_sha256": entry_quote["sha256"],
        **details,
        "publication_server_attested": False,
        "profitability_proven": False,
        "NO_BET": True, "actual_wagers": 0,
    }
    record["sha256"] = hash_record(record)
    return record


def verify_receipt(receipt, prediction, entry_quote, prices):
    verify_record(receipt)
    same_event(prediction, receipt)
    if (receipt.get("policy") != POLICY_ID
            or receipt.get("prediction_sha256") != prediction["sha256"]
            or receipt.get("entry_quote_sha256") != entry_quote["sha256"]):
        raise ValueError("Paper selection not linked to exact frozen inputs/policy")
    if not (utc(ACTIVATION) <= utc(prediction["recorded_at"])
            <= utc(receipt["recorded_at"]) < utc(prediction["kickoff"])):
        raise ValueError("Paper decision was not frozen before kickoff")
    if utc(entry_quote["recorded_at"]) > utc(receipt["recorded_at"]):
        raise ValueError("Paper decision precedes original price")
    if (utc(receipt["recorded_at"]) - utc(prediction["recorded_at"])
            > timedelta(minutes=5) or
            utc(receipt["recorded_at"]) - utc(entry_quote["observed_at"])
            > timedelta(minutes=10)):
        raise ValueError("Paper selection receipt is stale relative to saved forecast/price")
    expected = compute_decision(prediction, prices)
    if (receipt.get("paper_selection_side") != expected["paper_selection_side"]
            or isinstance(receipt.get("paper_stake_units"), bool)
            or receipt.get("paper_stake_units") != expected["paper_stake_units"]
            or not isinstance(receipt.get("maximum_model_expected_unit_return"),
                               (float, int))
            or isinstance(receipt["maximum_model_expected_unit_return"], bool)
            or not math.isfinite(receipt["maximum_model_expected_unit_return"])
            or not math.isclose(
                receipt["maximum_model_expected_unit_return"],
                expected["maximum_model_expected_unit_return"],
                rel_tol=0, abs_tol=1e-12)):
        raise ValueError("Saved paper selection or fixed stake differs from frozen rule")
    if receipt.get("publication_server_attested") is not False or (
            receipt.get("profitability_proven") is not False):
        raise ValueError("Offline receipt cannot claim server publication or proven profit")
    return expected


def persist_exclusive(path, receipt):
    """Save exactly once; a clock/assertion is NOT a server publication receipt."""
    verify_record(receipt)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    return destination
