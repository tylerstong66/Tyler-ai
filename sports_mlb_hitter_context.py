"""Official MLB hitter season context and handedness, pregame research only.

Explicitly avoid double-counting league aggregate plus per-team season splits
after trades. These historical rates are NOT player-prop game probabilities.
"""
from sports_mlb_sources import OfficialMlbReader, positive_id, utc


def _name_and_handedness(payload, player_id, role):
    people = payload.get("people")
    if not isinstance(people, list) or len(people) != 1:
        raise ValueError("Ambiguous official MLB " + role + " person payload.")
    person = people[0]
    if person.get("id") != player_id or not isinstance(person.get("fullName"), str):
        raise ValueError("Official MLB " + role + " identity does not match requested ID.")
    field = "batSide" if role == "hitter" else "pitchHand"
    desc = person.get(field)
    code = desc.get("code") if isinstance(desc, dict) else None
    if code is not None and code not in ("L", "R", "S"):
        raise ValueError("Invalid official MLB handedness code.")
    if code == "S" and role == "starter":
        raise ValueError("Unexpected switch-throwing starter notation; no guessing.")
    return {"id": player_id, "name": person["fullName"].strip(),
            "hand": code, "hand_source_field": field}


def _counts(row):
    keys = ("gamesPlayed", "plateAppearances", "atBats", "hits", "homeRuns", "baseOnBalls")
    if not isinstance(row, dict) or any(isinstance(row.get(k), bool) or not isinstance(row.get(k), int)
                                        or row[k] < 0 for k in keys):
        raise ValueError("Missing or invalid MLB season statistics.")
    games, pa, ab, hits, hr, walks = (row[k] for k in keys)
    if not (0 <= hr <= hits <= ab <= pa and walks <= pa - ab):
        raise ValueError("Inconsistent official MLB season counting statistics.")
    return {"games": games, "pa": pa, "ab": ab, "hits": hits, "hr": hr, "walks": walks}


def season_counts(payload, hitter_id, year):
    """Return one official regular-season total; never sum total and team splits."""
    if isinstance(year, bool) or not isinstance(year, int) or not 1900 <= year <= 2100:
        raise ValueError("Invalid baseball season.")
    groups = payload.get("stats")
    if not isinstance(groups, list):
        raise ValueError("MLB season results missing stats groups.")
    global_splits, team_splits = [], {}
    for group in groups:
        if (not isinstance(group, dict) or not isinstance(group.get("type"), dict)
                or not isinstance(group.get("group"), dict)):
            raise ValueError("Malformed official MLB season group.")
        if (group["type"].get("displayName") != "season" or
                group["group"].get("displayName") != "hitting"):
            continue
        splits = group.get("splits", [])
        if not isinstance(splits, list):
            raise ValueError("Malformed MLB season splits.")
        for item in splits:
            if not isinstance(item, dict):
                raise ValueError("Malformed MLB hitter season split.")
            if str(item.get("season")) != str(year) or item.get("gameType") != "R":
                continue
            player = item.get("player")
            if not isinstance(player, dict) or player.get("id") != hitter_id:
                raise ValueError("MLB season split has incorrect hitter ID.")
            stats = _counts(item.get("stat"))
            team = item.get("team")
            if team is None:
                global_splits.append(stats)
            else:
                ident = team.get("id") if isinstance(team, dict) else None
                if isinstance(ident, bool) or not isinstance(ident, int) or ident <= 0:
                    raise ValueError("Invalid MLB season team ID.")
                if ident in team_splits:
                    raise ValueError("Duplicate MLB team-season split.")
                team_splits[ident] = stats
    if len(global_splits) > 1:
        raise ValueError("Ambiguous official season aggregate; no summing duplicate totals.")
    if global_splits:
        overall = global_splits[0]
        if team_splits:
            keys = ("games", "pa", "ab", "hits", "hr", "walks")
            summed = {k: sum(stat[k] for stat in team_splits.values()) for k in keys}
            if summed != overall:
                raise ValueError("Season-wide MLB total disagrees with separate team totals.")
        aggregation = "official_all_team_total"
    elif team_splits:
        keys = ("games", "pa", "ab", "hits", "hr", "walks")
        overall = {k: sum(stat[k] for stat in team_splits.values()) for k in keys}
        aggregation = "distinct_team_splits_summed"
    else:
        return None
    # Rates are descriptive per AB or PA, never game-hitting prop estimates.
    return {"season": year, **overall,
            "batting_average": round(overall["hits"] / overall["ab"], 4) if overall["ab"] else None,
            "home_runs_per_pa": round(overall["hr"] / overall["pa"], 4) if overall["pa"] else None,
            "aggregation": aggregation,
            "teams_observed": sorted(team_splits),
            "is_game_probability": False}


def hitter_season_context(hitter_id, opposing_starter_id, event_start, *,
                          hitter_name=None, starter_name=None, reader=None):
    hitter_id = positive_id(hitter_id, "hitter_id")
    opposing_starter_id = positive_id(opposing_starter_id, "opposing_starter_id")
    if hitter_id == opposing_starter_id:
        raise ValueError("Hitter and opposing starter IDs must differ.")
    event = utc(event_start)
    reader = reader or OfficialMlbReader()
    if utc(reader.clock()) >= event:
        raise ValueError("Hitter context must be captured before first pitch.")
    prior_receipts = len(reader.audit)
    hitter_data, _ = reader.load("people/" + str(hitter_id))
    pitcher_data, _ = reader.load("people/" + str(opposing_starter_id))
    hitter = _name_and_handedness(hitter_data, hitter_id, "hitter")
    starter = _name_and_handedness(pitcher_data, opposing_starter_id, "starter")
    if hitter_name is not None and hitter["name"] != hitter_name:
        raise ValueError("Official hitter name changed from matched pregame identity.")
    if starter_name is not None and starter["name"] != starter_name:
        raise ValueError("Official probable starter name changed from matched pregame identity.")
    years = (event.year - 1, event.year)
    seasons = []
    for year in years:
        payload, evidence = reader.load("people/" + str(hitter_id) + "/stats", {
            "stats": "season", "group": "hitting", "season": year, "gameType": "R"})
        counts = season_counts(payload, hitter_id, year)
        if counts is not None:
            counts["source_url"] = evidence["source_url"]
            counts["retrieved_at"] = evidence["retrieved_at"]
        seasons.append(counts)
    as_of = utc(reader.clock())
    if as_of >= event:
        raise ValueError("MLB context collection crossed scheduled first pitch.")
    return {
        "hitter": hitter, "opposing_probable_starter": starter,
        "years": list(years), "season_statistics": seasons,
        "as_of": as_of.isoformat(), "first_pitch": event.isoformat(),
        "sources": list(reader.audit[prior_receipts:]),
        "decision": "HISTORICAL MLB CONTEXT - NO BET",
        "limitations": [
            "Regular-season counts and handedness are descriptive observations, not next-game player-prop probabilities.",
            "No assumption is made that batter or probable starter actually starts today's game.",
            "Team changes may create aggregate and split records; total rows are never added to team rows.",
            "Pitch location/mix, lineup position, expected at-bats, bullpen encounters, weather and odds are not modeled.",
            "Historical averages are not proof of any profitable wagering edge.",
        ],
    }
