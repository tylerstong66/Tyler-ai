"""Fail-closed pre-event NHL official/ESPN identity crosswalk from original bytes.

No live collection, betting, model changes or historical quote reconstruction.
The returned identity is for UNQUALIFIED market-source research only.
"""
import json
import re
from zoneinfo import ZoneInfo

from sports_profitability_v1 import ACTIVATION, hash_record, utc, original_bytes

NHL_SCHEDULE = "https://api-web.nhle.com/v1/schedule/"
ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates="
ESPN_ALIAS = {"NJ": "NJD", "SJ": "SJS", "TB": "TBL", "LA": "LAK",
              "UTAH": "UTA"}
MAX_ORIGINAL_BYTES = 4_000_000


def _bytes_json(root, source):
    if not isinstance(source, dict):
        raise ValueError("Original source reference required")
    raw = original_bytes(source, root)
    if len(raw) > MAX_ORIGINAL_BYTES:
        raise ValueError("Original schedule source exceeds size limit")
    try:
        return json.loads(raw)
    except (UnicodeError, ValueError):
        raise ValueError("Source schedule original is not JSON") from None


def _pinned_team(row, side):
    team = row.get(side + "Team")
    if not isinstance(team, dict) or not isinstance(team.get("abbrev"), str) or (
            not team["abbrev"]) or not isinstance(team.get("id"), int) or (
            isinstance(team["id"], bool)) or team["id"] <= 0:
        raise ValueError("Pinned official NHL team abbreviation and ID required")
    return team["abbrev"], team["id"]


def read_pregame_crosswalk(archive_root, official_source, espn_source, game_id, recorded_at):
    """Match original NHL ID/team/start to an original, pre-event ESPN event.

    Must be called only with separately saved, SHA-256-matched raw source bodies.
    Source retrieval and record clocks do not independently prove server publish
    time; the caller must retain that evidence separately before any ROI claims.
    """
    if not isinstance(game_id, str) or not re.fullmatch(r"\d{10}", game_id):
        raise ValueError("Official 10-digit NHL game ID required")
    official_data = _bytes_json(archive_root, official_source)
    espn_data = _bytes_json(archive_root, espn_source)
    if not isinstance(official_data, dict) or not isinstance(espn_data, dict):
        raise ValueError("Original source schedule response object required")
    official_games = official_data.get("games")
    if not isinstance(official_games, list):
        days = official_data.get("gameWeek")
        if not isinstance(days, list):
            raise ValueError("NHL schedule games/gameWeek missing")
        official_games = [game for day in days if isinstance(day, dict)
                          for game in day.get("games", [])]
    candidates = [g for g in official_games if isinstance(g, dict) and
                  str(g.get("id")) == game_id]
    if len(candidates) != 1:
        raise ValueError("Exactly one official NHL game ID required")
    game = candidates[0]
    if game.get("gameType") not in (2, 3) or (
            game.get("gameState") not in ("FUT", "PRE")) or (
            game.get("gameScheduleState") != "OK"):
        raise ValueError("Original NHL game must be a normal pre-event 2-way match")
    home, home_id = _pinned_team(game, "home")
    away, away_id = _pinned_team(game, "away")
    if home == away or home_id == away_id:
        raise ValueError("Official NHL home/away identities coincide")
    kickoff = utc(game.get("startTimeUTC"))
    eastern_date = kickoff.astimezone(ZoneInfo("America/New_York"))
    day = eastern_date.strftime("%Y-%m-%d")
    if official_source.get("source_url") != NHL_SCHEDULE + day or (
            espn_source.get("source_url") !=
            ESPN_SCOREBOARD + eastern_date.strftime("%Y%m%d")):
        raise ValueError("Independent source URL must be pinned to the original Eastern date")
    clock = utc(recorded_at)
    if not (utc(ACTIVATION) <= utc(official_source["retrieved_at"]) <= clock < kickoff
            and utc(ACTIVATION) <= utc(espn_source["retrieved_at"]) <= clock):
        raise ValueError("Crosswalk has no genuine post-activation pre-kickoff sources")
    events = espn_data.get("events")
    if not isinstance(events, list):
        raise ValueError("ESPN scoreboard original events list missing")
    matches = [event for event in events if isinstance(event, dict) and
               event.get("date") is not None and utc(event["date"]) == kickoff]
    confirmed = []
    for event in matches:
        status = event.get("status")
        kind = status.get("type") if isinstance(status, dict) else None
        if not isinstance(kind, dict) or kind.get("state") != "pre" or (
                kind.get("completed") is not False):
            continue
        comps = event.get("competitions")
        if not isinstance(comps, list) or len(comps) != 1 or (
                not isinstance(comps[0], dict)):
            continue
        competitors = comps[0].get("competitors")
        if not isinstance(competitors, list) or len(competitors) != 2:
            continue
        sides = {}
        for row in competitors:
            if not isinstance(row, dict) or row.get("homeAway") not in ("home", "away"):
                break
            team = row.get("team")
            if not isinstance(team, dict) or not isinstance(team.get("abbreviation"), str) or (
                    not isinstance(team.get("displayName"), str)) or (
                    not team["displayName"]) or row["homeAway"] in sides:
                break
            sides[row["homeAway"]] = team
        if set(sides) != {"home", "away"}:
            continue
        if (ESPN_ALIAS.get(sides["home"]["abbreviation"],
                           sides["home"]["abbreviation"]) != home or
            ESPN_ALIAS.get(sides["away"]["abbreviation"],
                           sides["away"]["abbreviation"]) != away):
            continue
        if (isinstance(game.get("neutralSite"), bool) and
                isinstance(comps[0].get("neutralSite"), bool) and
                game["neutralSite"] != comps[0]["neutralSite"]):
            raise ValueError("Official and ESPN original venue neutrality disagree")
        if not isinstance(event.get("id"), str) or not event["id"]:
            raise ValueError("ESPN event ID missing")
        confirmed.append((event["id"], sides))
    if len(confirmed) != 1:
        raise ValueError("Unique exact pre-event official/ESPN time/team identity required")
    event_id, teams = confirmed[0]
    result = {
        "game_id": game_id, "event_id": event_id,
        "home": home, "away": away,
        "home_id": str(home_id), "away_id": str(away_id),
        "home_name": teams["home"]["displayName"],
        "away_name": teams["away"]["displayName"],
        "kickoff": kickoff.isoformat(),
        "crosswalk_recorded_at": clock.isoformat(),
        "official_source_sha256": official_source["sha256"],
        "espn_source_sha256": espn_source["sha256"],
        "NO_BET": True, "actual_wagers": 0,
        "publication_server_attested": False,
        "sportsbook_price_verified": False,
        "qualified_for_paper_roi": False,
    }
    result["sha256"] = hash_record(result)
    return result
