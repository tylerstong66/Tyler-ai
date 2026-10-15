"""Recent opposing bullpen workload from official completed MLB game boxscores.

Research-only historical counts, never a forecast that a reliever will appear,
an availability confirmation, or a betting recommendation. Not used for model
promotion, frozen paper predictions, or wagering.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

from sports_mlb_sources import OfficialMlbReader, positive_id, utc

EASTERN = ZoneInfo("America/New_York")
LIMIT_GAMES = 12


def _game_time(value):
    return utc(value)


def recent_pitcher_usage(upcoming_game_id, pitching_side, candidate_ids=(), *,
                         reader=None, lookback_days=5):
    upcoming_game_id = positive_id(upcoming_game_id, "game ID")
    if pitching_side not in ("home", "away"):
        raise ValueError("pitching_side must be home or away.")
    if not isinstance(candidate_ids, (list, tuple)) or len(candidate_ids) > 4:
        raise ValueError("At most four reliever IDs may be researched.")
    ids = [positive_id(i, "relief pitcher ID") for i in candidate_ids]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate pitcher ID.")
    if isinstance(lookback_days, bool) or not isinstance(lookback_days, int) or not 1 <= lookback_days <= 7:
        raise ValueError("Lookback days must be between 1 and 7.")
    reader = reader or OfficialMlbReader()
    upcoming, _ = reader.load("game/" + str(upcoming_game_id) + "/feed/live")
    gd = upcoming.get("gameData", {})
    if upcoming.get("gamePk") != upcoming_game_id or gd.get("status", {}).get("abstractGameState") != "Preview":
        raise ValueError("Upcoming official MLB game identity/pregame status not verified.")
    first_pitch = _game_time(gd.get("datetime", {}).get("dateTime"))
    cutoff = utc(reader.clock())
    if cutoff >= first_pitch:
        raise ValueError("Cannot use bullpen history at or after upcoming first pitch.")
    team = gd.get("teams", {}).get(pitching_side, {})
    team_id = positive_id(team.get("id"), "Pitching team ID")
    if team_id == gd.get("teams", {}).get("away" if pitching_side == "home" else "home", {}).get("id"):
        raise ValueError("Teams have nonunique MLB IDs.")
    game_day = first_pitch.astimezone(EASTERN).date().isoformat()
    roster, _ = reader.load("teams/" + str(team_id) + "/roster",
                             {"rosterType": "active", "date": game_day})
    roster_p = {r.get("person", {}).get("id") for r in roster.get("roster", [])
                if r.get("position", {}).get("abbreviation") == "P"}
    if any(pid not in roster_p for pid in ids):
        raise ValueError("A candidate relief pitcher is not on the official active pitcher roster.")
    end = cutoff.astimezone(EASTERN).date()
    start = (end - timedelta(days=lookback_days)).isoformat()
    schedule, schedule_receipt = reader.load("schedule", {
        "sportId": 1, "teamId": team_id, "startDate": start,
        "endDate": end.isoformat(), "gameTypes": "R,F,D,L,W"})
    games = [g for d in schedule.get("dates", []) for g in d.get("games", [])]
    if len(games) > LIMIT_GAMES:
        raise ValueError("Too many games in the official recent-window schedule.")
    observed = {pid: [] for pid in ids}
    failed_games = []
    scheduled_ids = set()
    for g in games:
        pk = g.get("gamePk")
        if not isinstance(pk, int) or isinstance(pk, bool) or pk in scheduled_ids:
            raise ValueError("Duplicate/invalid official past game IDs.")
        scheduled_ids.add(pk)
        scheduled = _game_time(g.get("gameDate"))
        if scheduled >= cutoff or pk == upcoming_game_id:
            continue
        sides = g.get("teams", {})
        matched = [side for side in ("home", "away")
                   if sides.get(side, {}).get("team", {}).get("id") == team_id]
        if len(matched) != 1:
            raise ValueError("Past schedule identity does not contain the specified team once.")
        match_side = matched[0]
        status = g.get("status", {})
        if status.get("abstractGameState") != "Final" or status.get("detailedState") != "Final":
            failed_games.append({"game_id": pk, "reason": "not_verified_final"})
            continue
        feed, receipt = reader.load("game/" + str(pk) + "/feed/live")
        fd = feed.get("gameData", {})
        if (feed.get("gamePk") != pk or
                fd.get("teams", {}).get(match_side, {}).get("id") != team_id or
                abs((_game_time(fd.get("datetime", {}).get("dateTime")) - scheduled).total_seconds()) > 60 or
                fd.get("status", {}).get("abstractGameState") != "Final" or
                fd.get("status", {}).get("detailedState") != "Final"):
            raise ValueError("Official past final contradicts schedule event identity.")
        box = feed.get("liveData", {}).get("boxscore", {}).get("teams", {}).get(match_side, {})
        pitchers = box.get("pitchers")
        if not isinstance(pitchers, list) or any(not isinstance(p, int) or isinstance(p, bool) for p in pitchers):
            failed_games.append({"game_id": pk, "reason": "pitcher_boxscore_missing"})
            continue
        if len(pitchers) != len(set(pitchers)):
            raise ValueError("Official past pitcher appearance IDs are duplicated.")
        players = box.get("players", {})
        records = {}
        incomplete = False
        for pid in ids:
            if pid not in pitchers:
                continue
            entry = players.get("ID" + str(pid))
            count = entry.get("stats", {}).get("pitching", {}).get("numberOfPitches") if isinstance(entry, dict) else None
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                incomplete = True
                break
            records[pid] = count
        if incomplete:
            failed_games.append({"game_id": pk, "reason": "pitch_count_missing"})
            continue
        for pid, pitches in records.items():
            observed[pid].append({"game_id": pk, "game_start_utc": scheduled.isoformat(),
                                  "pitches_thrown": pitches, "source_url": receipt["source_url"],
                                  "retrieved_at": receipt["retrieved_at"]})
    as_of = utc(reader.clock())
    if as_of >= first_pitch:
        raise ValueError("Recent bullpen research crossed scheduled first pitch.")
    results = []
    for pid in ids:
        games_for = observed[pid]
        recent = max((utc(g["game_start_utc"]) for g in games_for), default=None)
        results.append({
            "pitcher_id": pid, "recorded_appearances": len(games_for),
            "pitches_thrown_observed": sum(g["pitches_thrown"] for g in games_for),
            "last_recorded_game_start_utc": recent.isoformat() if recent else None,
            "game_records": games_for,
            "coverage_complete": not failed_games,
            "availability": "unknown",
            "projected_appearance_probability": None,
        })
    return {
        "upcoming_game_id": str(upcoming_game_id), "pitching_team_id": team_id,
        "as_of": as_of.isoformat(), "upcoming_first_pitch": first_pitch.isoformat(),
        "window_days": lookback_days, "historical_games_listed": len(games),
        "historical_games_with_incomplete_data": failed_games,
        "candidates": results,
        "schedule_evidence": schedule_receipt, "capture_receipts": list(reader.audit),
        "decision": "RESEARCH ONLY - NO BET",
        "limitations": [
            "Counts reflect only verified completed game boxscores in the requested recent window.",
            "Incomplete, delayed or nonfinal game records are flagged and are not guessed.",
            "Active roster listing does not establish relief role, game availability or likelihood of entering.",
            "Past pitch totals and last appearance are descriptive, not a calibrated workload-risk model.",
            "No probability, line, sportsbook odds, parlay, expected value, or wager execution.",
        ],
    }
