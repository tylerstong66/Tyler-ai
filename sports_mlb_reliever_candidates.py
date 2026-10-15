"""Select *historically used* MLB relievers from verified prior final boxscores.

Ranking is by completed-game relief appearances, NOT a predicted probability
of entering the upcoming game. No bets, model writes, or assumptions about
availability. Missing/ambiguous evidence is identified and never treated as 0.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

from sports_mlb_sources import OfficialMlbReader, _roster_people, positive_id, utc

EASTERN = ZoneInfo("America/New_York")


def collect_recent_relief_candidates(game_id, pitching_side, *, reader=None,
                                     lookback_days=7, max_candidates=4):
    game_id = positive_id(game_id, "upcoming_game_id")
    if pitching_side not in ("home", "away"):
        raise ValueError("pitching_side must be home or away.")
    if (isinstance(lookback_days, bool) or not isinstance(lookback_days, int)
            or not 2 <= lookback_days <= 7):
        raise ValueError("Lookback must be 2 to 7 calendar days.")
    if (isinstance(max_candidates, bool) or not isinstance(max_candidates, int)
            or not 1 <= max_candidates <= 4):
        raise ValueError("Can select 1 to 4 historically used relief pitchers.")
    reader = reader or OfficialMlbReader()
    upcoming, upcoming_source = reader.load(
        "game/" + str(game_id) + "/feed/live", api_version="v1.1")
    gd = upcoming.get("gameData", {})
    if (upcoming.get("gamePk") != game_id or
            gd.get("status", {}).get("abstractGameState") != "Preview" or
            gd.get("status", {}).get("detailedState") not in ("Scheduled", "Pre-Game")):
        raise ValueError("Upcoming event not verified as official MLB pregame.")
    first_pitch = utc(gd.get("datetime", {}).get("dateTime"))
    if utc(reader.clock()) >= first_pitch:
        raise ValueError("Upcoming game started before bullpen selection.")
    teams = gd.get("teams", {})
    team_id = positive_id(teams.get(pitching_side, {}).get("id"), "pitching_team_id")
    opposite = "away" if pitching_side == "home" else "home"
    opponent_id = positive_id(teams.get(opposite, {}).get("id"), "other_team_id")
    if opponent_id == team_id:
        raise ValueError("MLB event has duplicate team IDs.")
    probable = gd.get("probablePitchers", {}).get(pitching_side)
    if not isinstance(probable, dict) or not isinstance(probable.get("id"), int):
        raise ValueError("Opposing probable starter missing; cannot exclude starter.")
    starter_id = positive_id(probable["id"], "probable_starter_id")
    local_date = first_pitch.astimezone(EASTERN).date()
    roster, roster_source = reader.load(
        "teams/" + str(team_id) + "/roster",
        {"rosterType": "active", "date": local_date.isoformat()})
    names = _roster_people(roster)
    available_ids = {p["id"] for p in names.values() if p["position"] == "P"}
    if starter_id not in available_ids:
        raise ValueError("Probable starter not on official active pitching roster.")
    cutoff = utc(reader.clock())
    end = cutoff.astimezone(EASTERN).date()
    schedule, schedule_source = reader.load("schedule", {
        "sportId": 1, "teamId": team_id,
        "startDate": (end - timedelta(days=lookback_days)).isoformat(),
        "endDate": end.isoformat(), "gameTypes": "R,F,D,L,W"})
    dates = schedule.get("dates", [])
    if not isinstance(dates, list):
        raise ValueError("Official bullpen schedule does not contain dates.")
    events = [g for day in dates for g in day.get("games", [])]
    if len(events) > 16:
        raise ValueError("Abnormal volume of prior MLB team games.")
    observed = {}
    incomplete = []
    seen = set()
    verified_final_games = 0
    for event in events:
        pk = event.get("gamePk")
        if isinstance(pk, bool) or not isinstance(pk, int) or pk <= 0 or pk in seen:
            raise ValueError("Duplicate or invalid scheduled game identity.")
        seen.add(pk)
        start = utc(event.get("gameDate"))
        if pk == game_id or start >= cutoff:
            continue
        sides = [side for side in ("home", "away") if
                 event.get("teams", {}).get(side, {}).get("team", {}).get("id") == team_id]
        if len(sides) != 1:
            raise ValueError("Historical event team identity is ambiguous.")
        side = sides[0]
        status = event.get("status", {})
        if (status.get("abstractGameState") != "Final" or
                status.get("detailedState") != "Final"):
            incomplete.append({"game_id": pk, "reason": "not_verified_final"})
            continue
        prior, source = reader.load(
            "game/" + str(pk) + "/feed/live", api_version="v1.1")
        past = prior.get("gameData", {})
        if (prior.get("gamePk") != pk or
                past.get("teams", {}).get(side, {}).get("id") != team_id or
                utc(past.get("datetime", {}).get("dateTime")) != start or
                past.get("status", {}).get("abstractGameState") != "Final" or
                past.get("status", {}).get("detailedState") != "Final"):
            raise ValueError("Historical MLB schedule and final boxscore identity disagree.")
        box = prior.get("liveData", {}).get("boxscore", {}).get("teams", {}).get(side, {})
        listed = box.get("pitchers")
        if (not isinstance(listed, list) or not listed or
                any(isinstance(x, bool) or not isinstance(x, int) for x in listed) or
                len(set(listed)) != len(listed)):
            incomplete.append({"game_id": pk, "reason": "pitchers_missing_or_duplicated"})
            continue
        data = box.get("players", {})
        if not isinstance(data, dict):
            incomplete.append({"game_id": pk, "reason": "player_boxscore_missing"})
            continue
        # Reject the complete game rather than silently ranking players from a
        # partial or ambiguous final boxscore.
        appearances = []
        invalid = False
        for pid in listed:
            raw = data.get("ID" + str(pid))
            stats = raw.get("stats", {}).get("pitching", {}) if isinstance(raw, dict) else {}
            starts, pitches = stats.get("gamesStarted"), stats.get("numberOfPitches")
            if (isinstance(starts, bool) or starts not in (0, 1) or
                    isinstance(pitches, bool) or not isinstance(pitches, int) or pitches < 0):
                invalid = True
                break
            appearances.append((pid, starts, pitches))
        if invalid:
            incomplete.append({"game_id": pk, "reason": "pitching_role_or_count_missing"})
            continue
        verified_final_games += 1
        for pid, starts, pitches in appearances:
            if starts == 1 or pid not in available_ids or pid == starter_id:
                continue
            observed.setdefault(pid, []).append({
                "game_id": pk, "game_start_utc": start.isoformat(),
                "pitches": pitches, "source_url": source["source_url"]})
    as_of = utc(reader.clock())
    if as_of >= first_pitch:
        raise ValueError("Evidence collection crossed first pitch.")
    ranked = sorted(observed, key=lambda pid: (
        -len(observed[pid]),
        -max(utc(row["game_start_utc"]).timestamp() for row in observed[pid]),
        pid))
    candidates = []
    for pid in ranked[:max_candidates]:
        records = observed[pid]
        candidates.append({
            "pitcher_id": pid, "pitcher_name": names[pid]["name"],
            "verified_relief_appearances": len(records),
            "pitches_thrown_in_relief": sum(row["pitches"] for row in records),
            "last_completed_relief_game_start_utc": max(
                row["game_start_utc"] for row in records),
            "evidence_games": records,
            "reason_selected": "recent_verified_relief_appearances",
            "projected_appearance_probability": None,
            "confirmed_available": False,
        })
    return {
        "game_id": str(game_id), "team_id": team_id, "probable_starter_id": starter_id,
        "as_of": as_of.isoformat(), "event_start": first_pitch.isoformat(),
        "lookback_days": lookback_days, "historical_games_listed": len(events),
        "verified_final_games": verified_final_games,
        "incomplete_games": incomplete,
        "historical_game_coverage_complete": not incomplete,
        "selection": candidates,
        "official_sources": {
            "pregame": upcoming_source, "active_roster": roster_source,
            "prior_schedule": schedule_source, "capture_receipts": list(reader.audit),
        },
        "status": "HISTORICAL RELIEF CANDIDATES - NO BET",
        "limitations": [
            "These pitchers are ranked by recent *recorded* relief appearances, not a validated likelihood of facing the batter.",
            "A past relief appearance does not establish today's availability, role, injury status or game script.",
            "Partial or unverified past-game boxscores are omitted and listed, not silently assumed to contain no relief use.",
            "The list excludes the listed probable starter and historical starts; it is not a complete projection of tonight's bullpen.",
            "No estimated appearances, hit/HR prop probabilities, sportsbook odds, EV or wagers.",
        ],
    }
