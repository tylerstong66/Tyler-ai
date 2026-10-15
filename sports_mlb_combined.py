"""Combine independently fetched MLB hitter/starter and bullpen research, NO BET.

No calibrated hit/HR or reliever appearance probabilities are inferred from raw
historical rates. Does not write predictions, change Tyler profile, or execute bets.
"""
from sports_mlb_bullpen_usage import recent_pitcher_usage
from sports_mlb_sources import OfficialMlbReader, pregame_research, utc


def complete_matchup_research(game_id, hitter_id, hitter_side,
                              reliever_ids=(), *, reader=None):
    if hitter_side not in ("home", "away"):
        raise ValueError("hitter_side must be home or away.")
    reader = reader or OfficialMlbReader()
    hitter = pregame_research(game_id, hitter_id, hitter_side, reliever_ids, reader=reader)
    pitching_side = "home" if hitter_side == "away" else "away"
    workload = recent_pitcher_usage(game_id, pitching_side, reliever_ids, reader=reader)
    if hitter["game_id"] != workload["upcoming_game_id"]:
        raise ValueError("Two independently collected MLB game identities disagree.")
    if abs((utc(hitter["event_start"]) - utc(workload["upcoming_first_pitch"])).total_seconds()) > 0:
        raise ValueError("Game starting times changed during combined research.")
    match_ids = [x["pitcher"]["id"] for x in hitter["reliever_matchups"]]
    work_ids = [x["pitcher_id"] for x in workload["candidates"]]
    if match_ids != work_ids:
        raise ValueError("Bulpen candidate IDs differ between official research components.")
    event_start = utc(hitter["event_start"])
    if utc(hitter["as_of"]) >= event_start or utc(workload["as_of"]) >= event_start:
        raise ValueError("Combined evidence was captured too late.")
    starter = hitter["starter_matchup"]
    notes = []
    if starter["plate_appearances"] is None:
        notes.append("Starter head-to-head data unavailable. No batting or HR rate can be inferred.")
    else:
        rate = starter["historical_batting_average"]
        average = "unknown" if rate is None else f"{rate:.3f}"
        notes.append(
            f"Probable starter {starter['pitcher']['name']}: "
            f"{starter['hits']} hits in {starter['at_bats']} at-bats, "
            f"{starter['plate_appearances']} plate appearances; descriptive AVG {average}.")
        if starter["small_sample_under_25_pa"]:
            notes.append("Starter matchup has fewer than 25 historical PA; treat it as a small sample.")
    if not hitter["reliever_matchups"]:
        notes.append("No prospective relievers were supplied or verified.")
    for row, work in zip(hitter["reliever_matchups"], workload["candidates"]):
        name = row["pitcher"]["name"]
        sample = row["plate_appearances"]
        h2h = "no verified head-to-head count" if sample is None else f"{sample} historical PA"
        notes.append(
            f"Possible reliever {name}: {h2h}; "
            f"{work['recorded_appearances']} completed-game appearances and "
            f"{work['pitches_thrown_observed']} recorded pitches over {workload['window_days']} calendar days. "
            "Future use/availability unknown.")
    coverage_complete = not workload["historical_games_with_incomplete_data"]
    if not coverage_complete:
        notes.append("Recent bullpen evidence is incomplete; affected games are not silently treated as zero.")
    notes.append("These are research facts, not calibrated player-prop odds or joint parlay probabilities.")
    return {
        "game_id": hitter["game_id"], "hitter": hitter["hitter"],
        "probable_starter": starter["pitcher"],
        "summary": notes,
        "matchup_research": hitter,
        "recent_bullpen_research": workload,
        "coverage": {
            "historical_pitcher_matchups": hitter["coverage"],
            "recent_bullpen_records_complete": coverage_complete,
        },
        "decision": "RESEARCH ONLY - NO BET",
        "estimated_hit_probability": None,
        "estimated_home_run_probability": None,
        "estimated_relief_appearance_probability": None,
        "parlay_joint_probability": None,
        "expected_value": None,
        "wager_executed": False,
    }
