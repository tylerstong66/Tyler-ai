"""Fail-closed bridge between independently verified model evidence and chat.

A web search excerpt is never a model probability, an executable sportsbook
quote, or proof of pre-event chronology. This module performs no I/O or wagers.
"""
import math
from datetime import datetime, timezone


def _utc(value):
    if not isinstance(value, str):
        raise ValueError("timestamp required")
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("timezone required")
    return date.astimezone(timezone.utc)


def verified_model_selection(evidence, now):
    """Return a hypothetical model comparison only with explicitly verified inputs.

    The caller must verify the original independent archives and model provenance.
    Boolean flags alone cannot independently certify source authenticity.
    """
    if not isinstance(evidence, dict):
        return {"status": "unavailable", "reason": "No verified model evidence supplied"}
    required = ("model_id", "model_version", "market", "event_id", "event_start",
                "prediction_recorded_at", "quote_recorded_at", "quote_verified",
                "prediction_verified", "source_url", "american_odds", "probability")
    if any(evidence.get(key) is None or evidence.get(key) == "" for key in required):
        return {"status": "unavailable", "reason": "Incomplete model, source or price evidence"}
    if evidence["prediction_verified"] is not True or evidence["quote_verified"] is not True:
        return {"status": "unavailable", "reason": "Model or sportsbook evidence unverified"}
    try:
        start = _utc(evidence["event_start"])
        predicted = _utc(evidence["prediction_recorded_at"])
        quoted = _utc(evidence["quote_recorded_at"])
        current = _utc(now)
        probability = float(evidence["probability"])
        odds = evidence["american_odds"]
        if isinstance(odds, bool) or not isinstance(odds, int) or -100 < odds < 100:
            raise ValueError("invalid American odds")
        if not math.isfinite(probability) or not 0 < probability < 1:
            raise ValueError("invalid probability")
        if not predicted <= quoted <= current < start:
            raise ValueError("stale, future or post-event evidence")
        if not str(evidence["source_url"]).startswith("https://"):
            raise ValueError("source URL not HTTPS")
    except (ValueError, TypeError, OverflowError):
        return {"status": "unavailable", "reason": "Invalid or non-prospective model evidence"}
    decimal = 1 + (odds / 100 if odds > 0 else 100 / abs(odds))
    return {"status": "hypothetical_only", "model_id": evidence["model_id"],
            "model_version": evidence["model_version"], "event_id": evidence["event_id"],
            "market": evidence["market"], "model_probability": probability,
            "american_odds": odds, "implied_probability": 1 / decimal,
            "expected_return_per_unit": probability * decimal - 1,
            "source_url": evidence["source_url"], "NO_BET": True}


def chat_model_status():
    """No verified prospective prediction/quote is wired into the chat endpoint."""
    return ("SPORTS MODEL EVIDENCE STATUS: unavailable in this chat request. "
            "Search results are research only, not model-generated probabilities or "
            "verified executable FanDuel odds. Do not claim that a sports model ran; "
            "do not assign numerical model probabilities, EV or model-ranked picks. "
            "Explain the unavailable model connection and identify missing evidence. "
            "NO_BET=true; no wagers.")
