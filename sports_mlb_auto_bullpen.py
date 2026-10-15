"""Auto shortlist relief candidates and join independent MLB matchup research.

Every candidate is backed by recorded completed-game relief usage. No
calibrated appearance probability, odds, EV, or wager execution.
"""
from sports_mlb_combined import complete_matchup_research
from sports_mlb_reliever_candidates import collect_recent_relief_candidates
from sports_mlb_sources import OfficialMlbReader, utc


def auto_bullpen_matchup(game_id, hitter_id, hitter_side, *,
                        manual_reliever_ids=(), auto_select=True, reader=None):
    if not isinstance(auto_select, bool):
        raise ValueError("auto_select must be a boolean.")
    if not isinstance(manual_reliever_ids, (list,tuple)):
        raise ValueError("manual_reliever_ids must be a list.")
    if manual_reliever_ids and auto_select:
        raise ValueError("Use manual reliever IDs or automatic selection, not both.")
    reader = reader or OfficialMlbReader()
    discovery = None
    if auto_select:
        pitching_side = "away" if hitter_side == "home" else "home"
        discovery = collect_recent_relief_candidates(
            game_id, pitching_side, reader=reader, lookback_days=7, max_candidates=4)
        ids = [p["pitcher_id"] for p in discovery["selection"]]
    else:
        ids = list(manual_reliever_ids)
    combined = complete_matchup_research(
        game_id, hitter_id, hitter_side, ids, reader=reader)
    if discovery is not None:
        if (discovery["game_id"] != combined["game_id"] or
                discovery["probable_starter_id"] != combined["probable_starter"]["id"] or
                discovery["event_start"] != combined["matchup_research"]["event_start"]):
            raise ValueError("MLB game identity/starter/timing changed during bullpen analysis.")
        seen = [p["pitcher"]["id"] for p in combined["matchup_research"]["reliever_matchups"]]
        if seen != ids:
            raise ValueError("Automatic bullpen candidate list changed during matchup research.")
        if utc(discovery["as_of"]) >= utc(discovery["event_start"]):
            raise ValueError("Auto bullpen selection completed after first pitch.")
        combined["summary"].append(
            "Potential relief pitchers were selected from recent verified relief usage, "
            "not a statistical model of who will enter the game.")
        if not discovery["historical_game_coverage_complete"]:
            combined["summary"].append(
                "Some prior bullpen games were incomplete; selection coverage is partial.")
        if not ids:
            combined["summary"].append(
                "No eligible recently observed relief-pitching candidates could be verified; "
                "bullpen matchups remain unknown.")
    combined["auto_bullpen_discovery"] = discovery
    combined["auto_bullpen_enabled"] = auto_select
    combined["reliever_ids_analyzed"] = ids
    combined["decision"] = "RESEARCH ONLY - NO BET"
    combined["estimated_hit_probability"] = None
    combined["estimated_home_run_probability"] = None
    combined["estimated_relief_appearance_probability"] = None
    combined["parlay_joint_probability"] = None
    combined["expected_value"] = None
    combined["wager_executed"] = False
    return combined
