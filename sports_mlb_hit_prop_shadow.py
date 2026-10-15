"""Experimental MLB hitter-game binary-prop baseline with chronological diagnostics.

This code is research-only. It estimates conditional event frequencies (1+ hit
or HR in an MLB game *given at least one official at-bat*). It is NOT an
unconditional sportsbook player-prop forecast: lineup, no-AB outcomes, injuries,
pitch mix, bullpen, game script, odds, closing lines and model calibration are
not represented. Historical replay from a present-day stats API is retrospective
diagnostics, NOT independently archived prospective performance.
"""
import hashlib
import json
import math
from datetime import date
from zoneinfo import ZoneInfo

from sports_mlb_sources import OfficialMlbReader, positive_id, utc

EASTERN = ZoneInfo("America/New_York")
MODEL_NAME = "mlb_hitter_game_frequency_shadow_v1"
MIN_HISTORY = 30
WINDOW = 80
PRIOR_WEIGHT = 20
PRIORS = {"hit": 0.60, "hr": 0.08}


def _date(value):
    if not isinstance(value, str):
        raise ValueError("Hitter game date must be YYYY-MM-DD.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError("Invalid official hitter game date.") from None
    if parsed.isoformat() != value:
        raise ValueError("Official hitter game date must be canonical.")
    return parsed


def _count(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(label + " must be a nonnegative integer.")
    return value


def parse_hitter_game_log(payload, hitter_id, season):
    """Use only official season+regular-game individual game log entries.

    Player name is never used to join. A suspended, postponed or doubleheader
    game remains individually identified by official gamePk. Never aggregate
    future season-to-date totals into individual-game labels.
    """
    positive_id(hitter_id, "hitter_id")
    if isinstance(season, bool) or not isinstance(season, int) or not 1900 <= season <= 2100:
        raise ValueError("Invalid MLB hitter-log season.")
    groups = payload.get("stats") if isinstance(payload, dict) else None
    if not isinstance(groups, list):
        raise ValueError("Official hitter log has no stats list.")
    records = []
    ids = set()
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("Malformed official game-log group.")
        if (group.get("type", {}).get("displayName") != "gameLog" or
                group.get("group", {}).get("displayName") != "hitting"):
            continue
        splits = group.get("splits")
        if not isinstance(splits, list):
            raise ValueError("Missing official individual-game splits.")
        for split in splits:
            if not isinstance(split, dict):
                raise ValueError("Malformed official individual-game row.")
            if str(split.get("season")) != str(season) or split.get("gameType") != "R":
                continue
            player = split.get("player")
            if not isinstance(player, dict) or player.get("id") != hitter_id:
                raise ValueError("Game-log player identity mismatch.")
            day = _date(split.get("date"))
            if day.year != season:
                raise ValueError("Game-log date disagrees with requested season.")
            game = split.get("game")
            if not isinstance(game, dict):
                raise ValueError("Official game-log row lacks game metadata.")
            pk = positive_id(game.get("gamePk"), "gamePk")
            if pk in ids:
                raise ValueError("Duplicate official player-game ID; refusing duplicate labels.")
            ids.add(pk)
            team = split.get("team")
            team_id = positive_id(team.get("id") if isinstance(team, dict) else None, "team_id")
            stat = split.get("stat")
            if not isinstance(stat, dict):
                raise ValueError("Game-log row lacks official hitting stats.")
            ab = _count(stat.get("atBats"), "atBats")
            hits = _count(stat.get("hits"), "hits")
            hr = _count(stat.get("homeRuns"), "homeRuns")
            pa = _count(stat.get("plateAppearances"), "plateAppearances")
            if not 0 <= hr <= hits <= ab <= pa:
                raise ValueError("Game-log counting statistics are inconsistent.")
            records.append({
                "game_id": pk, "hitter_id": hitter_id, "team_id": team_id,
                "game_day": day.isoformat(), "season": season,
                "ab": ab, "hits": hits, "hr": hr, "pa": pa,
                "has_hit": int(hits >= 1), "has_hr": int(hr >= 1),
                "eligible_at_least_one_ab": ab >= 1})
    return sorted(records, key=lambda x: (x["game_day"], x["game_id"]))


def _train(history):
    """Preregistered benchmark parameters; never tuned using target outcomes."""
    seen = [row for row in history if row["eligible_at_least_one_ab"]]
    recent = seen[-WINDOW:]
    if len(recent) < MIN_HISTORY:
        return None
    results = {}
    for stat, key in (("hit", "has_hit"), ("hr", "has_hr")):
        successes = sum(row[key] for row in recent)
        prior = PRIORS[stat]
        estimate = (successes + PRIOR_WEIGHT * prior) / (len(recent) + PRIOR_WEIGHT)
        results[stat] = {
            "experimental_conditional_probability": round(estimate, 6),
            "historical_event_frequency": round(successes / len(recent), 6),
            "prior": prior, "pseudo_games": PRIOR_WEIGHT,
            "rolling_games": len(recent), "successes": successes,
            "condition": "at_least_one_official_at_bat",
            "calibrated": False,
            "player_prop_betting_eligible": False,
        }
    return results


def conditional_shadow_forecast(game_log, event_start):
    """Use only rows with a local game day *strictly before* target game day.

    Same-day games (including doubleheaders) are excluded to avoid leakage
    when official start timestamps of individual game logs are unavailable.
    """
    event = utc(event_start)
    day = event.astimezone(EASTERN).date()
    history = [row for row in game_log if _date(row["game_day"]) < day]
    # Validate chronology and uniqueness through the dedicated official parser
    # upstream, and preserve a digest of the exact input event history.
    model = _train(sorted(history, key=lambda x: (x["game_day"], x["game_id"])))
    canonical = json.dumps(history, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {
        "model": MODEL_NAME, "event_start": event.isoformat(),
        "historical_cutoff_game_day_exclusive": day.isoformat(),
        "games_observed_before_target": len(history),
        "at_bat_eligible_history": sum(r["eligible_at_least_one_ab"] for r in history),
        "model_ready": model is not None,
        "estimates": model, "historical_input_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "status": "EXPERIMENTAL CONDITIONAL FREQUENCY - NO BET",
        "actual_wager": 0,
        "limitations": [
            "Forecast is conditional on at least one official at-bat; lineup appearance is not known.",
            "Not calibrated, not priced against a real sportsbook, and not a recommended wager.",
            "Empirical historical frequency is not an independent assessment of pitcher or bullpen matchups.",
            "All same-local-date game-log rows are excluded to guard against doubleheader leakage.",
            "An after-the-fact gameLog cannot prove its contents were publicly available by historical cutoff.",
        ],
    }


def _brier(predictions, outcomes):
    return sum((p - y)**2 for p, y in zip(predictions, outcomes)) / len(outcomes)


def _log_loss(predictions, outcomes):
    return -sum(y * math.log(max(p, 1e-12)) + (1-y) * math.log(max(1-p, 1e-12))
                for p, y in zip(predictions, outcomes)) / len(outcomes)


def retrospective_walk_forward(game_log, *, evaluation_season):
    """Date-block walk-forward diagnostics: future and same-day games excluded.

    This deliberately reports an *unverified retrospective* cohort; the data
    were not independently timestamped at each simulated forecast.
    """
    if isinstance(evaluation_season, bool) or not isinstance(evaluation_season, int):
        raise ValueError("Invalid evaluation season.")
    rows = sorted(game_log, key=lambda x: (x["game_day"], x["game_id"]))
    unique = {(x["hitter_id"], x["game_id"]) for x in rows}
    if len(unique) != len(rows):
        raise ValueError("Duplicate player-game labels in backtest.")
    evaluated = {"hit": {"prediction": [], "outcome": []},
                 "hr": {"prediction": [], "outcome": []}}
    skipped_zero_ab = 0
    skipped_no_history = 0
    for row in rows:
        if row["season"] != evaluation_season:
            continue
        if not row["eligible_at_least_one_ab"]:
            skipped_zero_ab += 1
            continue
        # Always replay the entire same-day block without outcomes from that date.
        previous = [x for x in rows if x["game_day"] < row["game_day"]]
        estimates = _train(previous)
        if estimates is None:
            skipped_no_history += 1
            continue
        for kind, outcome_key in (("hit", "has_hit"), ("hr", "has_hr")):
            evaluated[kind]["prediction"].append(
                estimates[kind]["experimental_conditional_probability"])
            evaluated[kind]["outcome"].append(row[outcome_key])
    summary = {}
    for kind, series in evaluated.items():
        probs = series["prediction"]
        labels = series["outcome"]
        base = PRIORS[kind]
        summary[kind] = {
            "n_games_with_at_least_one_ab": len(labels),
            "outcome_events": sum(labels),
            "observed_rate": round(sum(labels)/len(labels), 6) if labels else None,
            "model_brier": round(_brier(probs, labels), 6) if labels else None,
            "fixed_prior_brier": round(_brier([base]*len(labels), labels), 6) if labels else None,
            "model_log_loss": round(_log_loss(probs, labels), 6) if labels else None,
            "fixed_prior_log_loss": round(_log_loss([base]*len(labels), labels), 6) if labels else None,
            "improvement_established": False,
        }
    return {
        "model": MODEL_NAME, "evaluation_season": evaluation_season,
        "source_type": "CURRENTLY_RETRIEVED_OFFICIAL_GAMELOG",
        "design": "RETROSPECTIVE CHRONOLOGICAL DATE_BLOCK_DIAGNOSTIC",
        "prospective_validation": False, "sportsbook_value_established": False,
        "no_wagers": True, "condition": "at_least_one_official_at_bat",
        "skipped_zero_at_bats": skipped_zero_ab,
        "skipped_insufficient_prior_history": skipped_no_history,
        "outcomes": summary,
        "limitations": [
            "Hindsight retrieval of season-long gameLogs is not a frozen prospective pregame experiment.",
            "Evaluation excludes no-AB games; cannot model an unconditional sportsbook player prop.",
            "Source cohort, survivor-selection effects, injuries, time-varying roles, changes in team and lineup are uncontrolled.",
            "Fixed priors are reference comparators, not current betting market forecasts.",
            "No positive edge, statistical significance, calibration, or real-money profitability established.",
        ],
    }


def retrieve_game_logs(hitter_id, seasons, *, reader=None):
    """Bounded MLB public gameLog retrieval for source audit or a live shadow."""
    hitter_id = positive_id(hitter_id, "hitter_id")
    if not isinstance(seasons, (tuple, list)) or not 1 <= len(seasons) <= 3:
        raise ValueError("Provide one to three official MLB regular seasons.")
    if any(isinstance(s, bool) or not isinstance(s, int) or not 1900 <= s <= 2100 for s in seasons):
        raise ValueError("Invalid season.")
    if len(set(seasons)) != len(seasons):
        raise ValueError("Duplicate season.")
    reader = reader or OfficialMlbReader()
    games = []
    for season in sorted(seasons):
        data, receipt = reader.load("people/" + str(hitter_id) + "/stats", {
            "stats": "gameLog", "group": "hitting", "season": season, "gameType": "R"})
        parsed = parse_hitter_game_log(data, hitter_id, season)
        games.extend(parsed)
    if len({x["game_id"] for x in games}) != len(games):
        raise ValueError("Duplicate MLB game IDs across requested seasons.")
    return games, list(reader.audit)
