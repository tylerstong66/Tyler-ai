"""Strict name-to-ID resolution for upcoming MLB research, official sources only.

No fuzzy aliases, guesses, predicted lineups, reliever appearance probabilities,
sportsbook odds, or wagers. Ambiguous matchups fail closed.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

from sports_mlb_sources import OfficialMlbReader, positive_id, utc, _roster_people

EASTERN = ZoneInfo("America/New_York")


def _name(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 120:
        raise ValueError(label + " must be a nonempty name <=120 characters.")
    if any(ord(ch) < 32 for ch in value):
        raise ValueError(label + " has invalid characters.")
    return value.strip().casefold()


def _names(raw, label):
    if not isinstance(raw, list) or len(raw) > 4:
        raise ValueError(label + " must be an array of at most four pitcher names.")
    values = [_name(x, label) for x in raw]
    if len(values) != len(set(values)):
        raise ValueError("Duplicate requested reliever names.")
    return values


def resolve_named_pregame(date, hitter_name, *, team_name=None, starter_name=None,
                          reliever_names=None, game_id=None, reader=None):
    """Resolve exact named participants against an upcoming MLB event and roster.

    Returns verified IDs for a separately validated read-only research call.
    team_name is recommended and game_id is required for a doubleheader.
    """
    reader = reader or OfficialMlbReader()
    if not isinstance(date, str) or len(date) != 10:
        raise ValueError("date must be YYYY-MM-DD in America/New_York.")
    from datetime import date as date_type
    try:
        target = date_type.fromisoformat(date)
    except ValueError:
        raise ValueError("date must be valid YYYY-MM-DD.") from None
    if target.isoformat() != date:
        raise ValueError("date must be canonical YYYY-MM-DD.")
    now = utc(reader.clock())
    local_now = now.astimezone(EASTERN).date()
    if not local_now <= target <= local_now + timedelta(days=5):
        raise ValueError("Only today's or upcoming five days of MLB games are accepted.")
    hitter_key = _name(hitter_name, "hitter_name")
    team_key = _name(team_name, "team_name") if team_name is not None else None
    starter_key = _name(starter_name, "starter_name") if starter_name is not None else None
    reliever_keys = _names(reliever_names if reliever_names is not None else [], "reliever_names")
    if game_id is not None:
        game_id = positive_id(game_id, "game_id")
    schedule, schedule_source = reader.load("schedule", {
        "sportId": 1, "startDate": date, "endDate": date,
        "gameTypes": "R,F,D,L,W"})
    games = [g for d in schedule.get("dates", []) for g in d.get("games", [])]
    if len(games) > 20:
        raise ValueError("Unexpected number of scheduled MLB games.")
    candidates = []
    inspected = set()
    for game in games:
        pk = game.get("gamePk")
        if not isinstance(pk, int) or isinstance(pk, bool) or pk in inspected:
            raise ValueError("Invalid or duplicated official MLB game identity.")
        inspected.add(pk)
        if game_id is not None and pk != game_id:
            continue
        first_pitch = utc(game.get("gameDate"))
        if first_pitch <= now or first_pitch.astimezone(EASTERN).date() != target:
            continue
        state = game.get("status", {})
        if state.get("abstractGameState") != "Preview" or state.get("detailedState") not in (
                "Scheduled", "Pre-Game"):
            continue
        names = {}
        ids = {}
        for side in ("home", "away"):
            club = game.get("teams", {}).get(side, {}).get("team", {})
            names[side] = club.get("name")
            ids[side] = club.get("id")
            if not isinstance(ids[side], int) or not isinstance(names[side], str):
                raise ValueError("Official MLB schedule team identity missing.")
        if ids["home"] == ids["away"]:
            raise ValueError("Schedule repeats MLB club identity.")
        for side in ("home", "away"):
            if team_key is not None and names[side].strip().casefold() != team_key:
                continue
            roster, roster_source = reader.load("teams/" + str(ids[side]) + "/roster", {
                "rosterType": "active", "date": date})
            players = _roster_people(roster)
            hitters = [p for p in players.values()
                       if p["name"].casefold() == hitter_key and p["position"] != "P"]
            if len(hitters) > 1:
                raise ValueError("Multiple active hitter identities share the name.")
            if not hitters:
                continue
            opponent = "away" if side == "home" else "home"
            feed, feed_source = reader.load("game/" + str(pk) + "/feed/live",
                                             api_version="v1.1")
            gd = feed.get("gameData", {})
            if (feed.get("gamePk") != pk or
                    any(gd.get("teams", {}).get(s, {}).get("id") != ids[s] for s in ("home", "away")) or
                    utc(gd.get("datetime", {}).get("dateTime")) != first_pitch or
                    gd.get("status", {}).get("abstractGameState") != "Preview"):
                raise ValueError("Official game-feed identity or status changed during resolution.")
            listed_starter = gd.get("probablePitchers", {}).get(opponent)
            if not isinstance(listed_starter, dict) or not isinstance(listed_starter.get("id"), int):
                raise ValueError("Opposing probable starter is missing.")
            if starter_key is not None and _name(listed_starter.get("fullName"), "probable starter name") != starter_key:
                continue
            other_roster, other_source = reader.load("teams/" + str(ids[opponent]) + "/roster", {
                "rosterType": "active", "date": date})
            other_players = _roster_people(other_roster)
            starter_id = listed_starter["id"]
            if starter_id not in other_players or other_players[starter_id]["position"] != "P":
                raise ValueError("Opposing starter ID absent from official pitcher roster.")
            relievers = []
            for key in reliever_keys:
                matches = [person for person in other_players.values() if
                           person["name"].casefold() == key and person["position"] == "P" and
                           person["id"] != starter_id]
                if len(matches) != 1:
                    raise ValueError("Named potential reliever is absent or ambiguous.")
                relievers.append(matches[0]["id"])
            candidates.append({
                "game_id": pk,
                "hitter_id": hitters[0]["id"],
                "hitter_name": hitters[0]["name"],
                "hitter_side": side,
                "team_name": names[side],
                "opponent_name": names[opponent],
                "probable_starter_id": starter_id,
                "probable_starter_name": other_players[starter_id]["name"],
                "reliever_ids": relievers,
                "game_start": first_pitch.isoformat(),
                "sources": [roster_source, feed_source, other_source],
            })
    if not candidates:
        raise ValueError("No unique verified pregame match for that hitter/date/team/starter.")
    if len(candidates) != 1:
        raise ValueError("Ambiguous upcoming match (possibly doubleheader); specify an official game_id.")
    result = candidates[0]
    if utc(reader.clock()) >= utc(result["game_start"]):
        raise ValueError("Game began while resolving the matchup.")
    result["schedule_source"] = schedule_source
    result["as_of"] = utc(reader.clock()).isoformat()
    result["status"] = "IDENTITIES VERIFIED - RESEARCH ONLY"
    result["limitations"] = [
        "Only exact official active-roster names are resolved, with no fuzzy matching.",
        "Active roster membership does not prove a player is in the starting batting order.",
        "A probable starter is not a confirmed starter; nominated relievers are not predicted appearances.",
        "Game identity, roster, and probable pitcher must be checked again at analysis time.",
        "No wagering advice, player-prop odds or calibrated probability is produced.",
    ]
    return result
