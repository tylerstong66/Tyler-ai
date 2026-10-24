"""Fail-closed pregame chronology gates for future college/NBA research rows.

This module does not create predictions, results, bets, or training datasets.
It validates candidate evidence timing before any future modeling pipeline.
"""
from datetime import datetime, timezone
from sports_expansion_observer import utc

def verify_pregame_candidate(candidate):
    """Accept only evidence captured before kickoff and frozen before kickoff."""
    if not isinstance(candidate, dict):
        raise ValueError("Candidate must be a dictionary")
    if (candidate.get("NO_BET") is not True or type(candidate.get("actual_wagers")) is not int
            or candidate.get("actual_wagers") != 0):
        raise ValueError("Research-only guard missing")
    if candidate.get("forecasting_enabled") is not False:
        raise ValueError("Forecasting must remain disabled")
    if candidate.get("independent_official_final_verified") is not True:
        raise ValueError("Independent official final verification required")
    if candidate.get("identity_crosswalk_verified") is not True:
        raise ValueError("Independent game identity crosswalk required")
    kickoff = utc(candidate["scheduled_start_utc"])
    freeze = utc(candidate["frozen_at_utc"])
    if not freeze < kickoff:
        raise ValueError("Freeze must precede scheduled kickoff")
    seen = candidate.get("feature_observed_at_utc")
    if not isinstance(seen, list) or not seen:
        raise ValueError("Missing feature observation provenance")
    for stamp in seen:
        observed = utc(stamp)
        if observed > freeze:
            raise ValueError("Feature observed after forecast freeze")
        if observed >= kickoff:
            raise ValueError("Feature observed at or after kickoff")
    result_time = utc(candidate["official_final_observed_at_utc"])
    if result_time <= kickoff or result_time <= freeze:
        raise ValueError("Official final timestamp cannot precede kickoff/freeze")
    return {
        "schema": "tyler-college-nba-chronology-preflight-v1",
        "identity_crosswalk_verified": True,
        "independent_official_final_verified": True,
        "chronology_preflight_passed": True,
        "forecasting_enabled": False,
        "NO_BET": True,
        "actual_wagers": 0,
        "promotion_allowed": False,
    }
