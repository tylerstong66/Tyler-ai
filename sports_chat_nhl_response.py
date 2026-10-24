"""Deterministic, opt-in NHL model evidence response for chat.

Only a trusted server caller may supply the manifest and archive root. Never
derive archive paths from an untrusted chat message or web search excerpt.
"""
from sports_chat_nhl_evidence_manifest import compare_nhl_manifest


import math
from sports_profitability_v1 import BOOK, MARKET, MODEL_SHA, decimal_odds

def _valid_comparison(result):
    if not isinstance(result, dict) or result.get("status") != "hypothetical_only" or result.get("NO_BET") is not True:
        return False
    if (result.get("model_sha256"), result.get("book"), result.get("market")) != (MODEL_SHA, BOOK, MARKET):
        return False
    if not isinstance(result.get("game_id"), str) or not result["game_id"] or not isinstance(result.get("caveat"), str):
        return False
    outcomes = result.get("outcomes")
    if not isinstance(outcomes, dict) or set(outcomes) != {"home", "away"}:
        return False
    total = 0
    for side in ("home", "away"):
        row = outcomes[side]
        if not isinstance(row, dict):
            return False
        p, odds, ev = row.get("model_probability"), row.get("american_odds"), row.get("hypothetical_ev_per_unit")
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in (p, ev)):
            return False
        if not 0 < p < 1:
            return False
        try:
            expected = p * decimal_odds(odds) - 1
        except (ValueError, TypeError, ZeroDivisionError):
            return False
        if not math.isclose(ev, expected, rel_tol=0, abs_tol=1e-9):
            return False
        total += p
    return math.isclose(total, 1, rel_tol=0, abs_tol=1e-12)

def nhl_chat_evidence_response(manifest, archive_root, now=None):
    result = compare_nhl_manifest(manifest, archive_root, now=now)
    if not _valid_comparison(result):
        return ("Verified prospective NHL model/price evidence unavailable. "
                "No model probability, expected value or executable price can be claimed. "
                "NO_BET=true.")
    outcomes = result["outcomes"]
    lines = [
        "Read-only NHL archived model comparison (hypothetical; NOT an executable quote).",
        "Game: " + str(result["game_id"]),
        "Model SHA-256: " + result["model_sha256"],
        "Book: " + result["book"] + "; market: " + result["market"],
    ]
    for side in ("home", "away"):
        row = outcomes[side]
        lines.append(
            f"{side}: model probability {row['model_probability']:.4f}; "
            f"archived American odds {row['american_odds']:+d}; "
            f"hypothetical EV/unit {row['hypothetical_ev_per_unit']:+.4f}"
        )
    lines.extend((result["caveat"], "NO_BET=true; no real wagers or model promotion."))
    return "\n".join(lines)
