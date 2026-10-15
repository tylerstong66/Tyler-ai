"""Official MLB pregame identity and historical hitter-vs-pitcher evidence adapter.

Research only: never executes wagers or supplies calibrated player-prop probabilities.
Uses an injected reader for offline tests; default reader is the public MLB StatsAPI.
"""
import hashlib
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from urllib.parse import urlencode

import requests

from sports_mlb_matchups import analyze

ORIGIN = "https://statsapi.mlb.com/api/v1/"
ALLOWED_TYPES = {"R", "F", "D", "L", "W"}


def utc(value):
    if isinstance(value, datetime):
        instant = value
    elif isinstance(value, str):
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("Missing or invalid timestamp.")
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Timestamp must be timezone-aware.")
    return instant.astimezone(timezone.utc)


def positive_id(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(name + " must be a positive MLB integer ID.")
    return value


def official_counts(data):
    """Choose an *explicit* total, never add individual season/game splits twice."""
    groups = data.get("stats")
    if not isinstance(groups, list):
        raise ValueError("Malformed MLB player statistics.")
    candidates = [split.get("stat") for group in groups if
                  group.get("type", {}).get("displayName", "").lower() == "vsplayertotal"
                  and group.get("group", {}).get("displayName", "").lower() == "hitting"
                  for split in group.get("splits", [])]
    if not candidates:
        return None
    if len(candidates) != 1 or not isinstance(candidates[0], dict):
        raise ValueError("Ambiguous MLB vsPlayerTotal statistical splits.")
    row = candidates[0]
    fields = ["plateAppearances", "atBats", "hits", "homeRuns"]
    if any(not isinstance(row.get(field), int) or isinstance(row.get(field), bool) or row[field] < 0
           for field in fields):
        raise ValueError("Incomplete or invalid MLB vs-player counting statistics.")
    pa, ab, hits, hr = [row[field] for field in fields]
    if not 0 <= hr <= hits <= ab <= pa:
        raise ValueError("Inconsistent MLB vs-player statistics.")
    return {"pa": pa, "ab": ab, "hits": hits, "home_runs": hr}


class OfficialMlbReader:
    """Fixed-origin, bounded-HTTP transport; caller cannot supply arbitrary URLs."""
    def __init__(self, *, get=None, clock=None):
        self.get = get or requests.get
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.audit = []

    def load(self, path, params=None):
        if not isinstance(path, str) or not path or any(c not in
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/-."
                for c in path) or ".." in path or path.startswith("/"):
            raise ValueError("Invalid fixed-origin MLB path.")
        params = params or {}
        url = ORIGIN + path
        response = self.get(url, params=params, timeout=12, allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError("MLB StatsAPI HTTP " + str(response.status_code))
        if len(response.content) > 3_000_000:
            raise ValueError("MLB source response exceeds bounded size.")
        final_url = getattr(response, "url", url)
        if not isinstance(final_url, str) or not final_url.startswith(url):
            raise ValueError("Unexpected MLB response origin.")
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Malformed MLB source JSON.")
        captured = utc(self.clock()).isoformat()
        normalized = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
        evidence = {"source_url": url + ("?" + urlencode(sorted(params.items())) if params else ""),
                    "retrieved_at": captured,
                    "data_through": captured,  # observed availability, NOT verified publication time
                    "response_sha256": hashlib.sha256(normalized.encode()).hexdigest()}
        self.audit.append(evidence)
        return data, evidence


def _roster_people(payload):
    entries = payload.get("roster")
    if not isinstance(entries, list):
        raise ValueError("Official roster response absent.")
    people = {}
    for entry in entries:
        person = entry.get("person", {})
        pid, name = person.get("id"), person.get("fullName")
        if not isinstance(pid, int) or isinstance(pid, bool) or not isinstance(name, str) or not name.strip():
            continue
        if pid in people:
            raise ValueError("Duplicate official roster player ID.")
        people[pid] = {"id": pid, "name": name.strip(),
                       "position": entry.get("position", {}).get("abbreviation")}
    return people


def _counts_for_pair(reader, hitter_id, pitcher_id, seasons):
    totals, urls = [], []
    for season in seasons:
        data, evidence = reader.load("people/" + str(hitter_id) + "/stats", {
            "stats": "vsPlayer", "group": "hitting", "opposingPlayerId": pitcher_id,
            "season": season, "gameType": "R"})
        counts = official_counts(data)
        if counts:
            totals.append(counts)
            urls.append(evidence)
    if not totals:
        return None
    # Never combine independent game types, overlapping season sets, or summary rows.
    merged = {key: sum(row[key] for row in totals) for key in ("pa", "ab", "hits", "home_runs")}
    # Source chain is separately returned in audit. The last source URI alone is
    # NOT complete provenance when multiple seasons contributed.
    merged["source_url"] = urls[-1]["source_url"]
    merged["retrieved_at"] = urls[-1]["retrieved_at"]
    merged["data_through"] = urls[-1]["data_through"]
    merged["source_years"] = list(seasons)
    merged["source_count"] = len(urls)
    return merged


def pregame_research(game_id, hitter_id, hitter_side, reliever_ids=(), *, reader=None):
    """Build a sourced research object or fail closed, with no model or wager action.

    Relievers must appear on the opponent's *official active roster* but actual
    availability and likelihood of facing the hitter remain unknown.
    """
    game_id = positive_id(game_id, "game_id")
    hitter_id = positive_id(hitter_id, "hitter_id")
    if hitter_side not in ("home", "away"):
        raise ValueError("hitter_side must be home or away.")
    if not isinstance(reliever_ids, (list, tuple)) or len(reliever_ids) > 4:
        raise ValueError("Up to four optional relief pitchers may be requested.")
    reliever_ids = [positive_id(pid, "reliever ID") for pid in reliever_ids]
    if len(set(reliever_ids)) != len(reliever_ids):
        raise ValueError("Duplicate relief pitcher IDs.")
    reader = reader or OfficialMlbReader()
    game, event_evidence = reader.load("game/" + str(game_id) + "/feed/live")
    gd = game.get("gameData", {})
    if (game.get("gamePk") != game_id or gd.get("game", {}).get("type") not in ALLOWED_TYPES
            or gd.get("status", {}).get("abstractGameState") != "Preview"
            or gd.get("status", {}).get("detailedState") not in ("Scheduled", "Pre-Game")):
        raise ValueError("MLB identity or pregame state not verified.")
    start = utc(gd.get("datetime", {}).get("dateTime"))
    if utc(reader.clock()) >= start:
        raise ValueError("Game already started or cutoff is not pregame.")
    opponents = "away" if hitter_side == "home" else "home"
    teams = gd.get("teams", {})
    if not all(isinstance(teams.get(side, {}).get("id"), int) for side in ("home", "away")):
        raise ValueError("Official participating team identities missing.")
    hitter_team_id = teams[hitter_side]["id"]
    pitcher_team_id = teams[opponents]["id"]
    if hitter_team_id == pitcher_team_id:
        raise ValueError("Same team listed on both sides.")
    pp = gd.get("probablePitchers", {}).get(opponents)
    if not isinstance(pp, dict) or not isinstance(pp.get("id"), int):
        raise ValueError("No verified official probable opposing pitcher; no fake starter.")
    starter_id = positive_id(pp["id"], "probable pitcher")
    if starter_id in reliever_ids or hitter_id == starter_id or hitter_id in reliever_ids:
        raise ValueError("Role collision among MLB player IDs.")
    date = start.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    team_roster, _ = reader.load("teams/" + str(hitter_team_id) + "/roster", {
        "rosterType": "active", "date": date})
    opponent_roster, _ = reader.load("teams/" + str(pitcher_team_id) + "/roster", {
        "rosterType": "active", "date": date})
    hitters = _roster_people(team_roster)
    pitchers = _roster_people(opponent_roster)
    if hitter_id not in hitters:
        raise ValueError("Hitter not present on independently fetched official active roster.")
    if starter_id not in pitchers or pitchers[starter_id]["position"] != "P":
        raise ValueError("Probable pitcher absent from official active pitcher roster.")
    for pid in reliever_ids:
        if pid not in pitchers or pitchers[pid]["position"] != "P":
            raise ValueError("Reliever not present on opponent official active pitcher roster.")
    if utc(reader.clock()) >= start:
        raise ValueError("Game started during evidence collection.")
    seasons = (start.year - 1, start.year)
    matchups = []
    for pid in (starter_id, *reliever_ids):
        counts = _counts_for_pair(reader, hitter_id, pid, seasons)
        if counts:
            matchups.append({"hitter_id": hitter_id, "pitcher_id": pid,
                             **{key: counts[key] for key in
                                ("pa", "ab", "hits", "home_runs", "source_url", "retrieved_at", "data_through")}})
    as_of = utc(reader.clock())
    if as_of >= start:
        raise ValueError("Collection crossed first pitch; research invalid.")
    snapshot = {
        "game_id": str(game_id), "as_of": as_of.isoformat(), "event_start": start.isoformat(),
        "hitter": {key: hitters[hitter_id][key] for key in ("id", "name")},
        "starter": {**{key: pitchers[starter_id][key] for key in ("id", "name")}, "status": "probable"},
        "bullpen_candidates": [
            {**{key: pitchers[pid][key] for key in ("id", "name")}, "availability": "unknown"}
            for pid in reliever_ids],
        "matchups": matchups}
    result = analyze(snapshot)
    # Own payload plus complete unedited capture receipts; never claim data source
    # proves who will actually start/relieve or what the sportsbook offers.
    result["official_data"] = {
        "api_origin": ORIGIN, "game_feed_capture": event_evidence,
        "capture_receipts": list(reader.audit),
        "historical_seasons": list(seasons), "stat_game_type": "R",
        "rosters_are_active_not_confirmed_lineups": True,
        "historical_stats_are_observed_at_retrieval_not_archived_as_of_event": True}
    result["limitations"].append(
        "Only regular-season historical batter matchups from the previous and current seasons are included; postseason/spring data excluded.")
    result["limitations"].append(
        "Official active roster confirms listing, not batting order, starter certainty, reliever role or availability.")
    result["limitations"].append(
        "StatsAPI totals have no historical publication timestamp; do not use live pulls for retrospective backtesting.")
    return result


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Official MLB pregame matchup lookup; research only, NO BET")
    p.add_argument("game_id", type=int)
    p.add_argument("hitter_id", type=int)
    p.add_argument("--hitter-side", choices=("home", "away"), required=True)
    p.add_argument("--reliever-id", type=int, action="append", default=[])
    a = p.parse_args()
    print(json.dumps(pregame_research(a.game_id, a.hitter_id, a.hitter_side, a.reliever_id),
                     indent=2, allow_nan=False))
