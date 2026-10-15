"""One-shot public StatsAPI contract audit with printed schema, no wagers/credentials.

Should run only in a trusted CI job. Does not mutate Tyler data or service.
"""
import json
import requests

BASE = "https://statsapi.mlb.com/api/v1/"


def pull(path, params=None):
    url = BASE + path
    result = requests.get(url, params=params or {}, timeout=15, allow_redirects=False)
    print("HTTP", path, result.status_code, "length", len(result.content))
    result.raise_for_status()
    if len(result.content) > 4_000_000:
        raise RuntimeError("Unexpectedly large MLB API response.")
    value = result.json()
    if not isinstance(value, dict):
        raise RuntimeError("Unexpected non-object MLB response.")
    return value


def main():
    sample = pull("people/605141/stats", {
        "stats": "vsPlayer", "group": "hitting",
        "opposingPlayerId": 543037, "season": 2024, "gameType": "P"})
    groups = sample.get("stats", [])
    if not isinstance(groups, list):
        raise RuntimeError("No stats array")
    print("vsPlayer objects", json.dumps([{
        "type": s.get("type", {}).get("displayName"),
        "group": s.get("group", {}).get("displayName"),
        "splits": len(s.get("splits", [])),
        "stat_keys": sorted(set().union(
            *(set(x.get("stat", {})) for x in s.get("splits", []) if isinstance(x.get("stat"), dict))))[:45]
    } for s in groups]))
    for group in groups:
        print("SPLIT_META", group.get("type", {}).get("displayName"), json.dumps([
            {"season": x.get("season"), "team": x.get("team"),
             "opponent": x.get("opponent"), "gameType": x.get("gameType"),
             "stat": {k: x.get("stat", {}).get(k) for k in
                      ("plateAppearances", "atBats", "hits", "homeRuns")}}
            for x in group.get("splits", [])][:8]))
    team = pull("teams/119/roster", {"rosterType": "active", "date": "2026-10-15"})
    print("roster count", len(team.get("roster", [])))
    if team.get("roster"):
        print("roster sample keys", list(team["roster"][0]),
              "person keys", list(team["roster"][0].get("person", {})),
              "position", team["roster"][0].get("position"))
    schedule = pull("schedule", {"sportId": 1, "teamId": 119,
                 "startDate": "2024-10-25", "endDate": "2024-10-25", "gameTypes": "W"})
    events = [g for d in schedule.get("dates", []) for g in d.get("games", [])]
    print("postseason schedule games", len(events))
    if not events:
        raise RuntimeError("Expected 2024 World Series game but schedule returned no games.")
    event = events[0]
    game_id = event.get("gamePk")
    print("schedule gamePk", game_id, "gameDate", event.get("gameDate"),
          "status", event.get("status", {}))
    feed = None
    for version in ("v1", "v1.1"):
        url = "https://statsapi.mlb.com/api/" + version + "/game/" + str(game_id) + "/feed/live"
        response = requests.get(url, timeout=15, allow_redirects=False)
        print("HISTORICAL_FEED", version, response.status_code, len(response.content))
        if response.status_code == 200:
            feed = response.json()
            break
    if feed is None:
        fallback = pull("game/" + str(game_id) + "/boxscore")
        print("FALLBACK_BOXSCORE_TOP", sorted(fallback.keys()),
              "home player count", len(fallback.get("teams", {}).get("home", {}).get("players", {})))
        print("AUDIT_PARTIAL - historic feed unavailable, boxscore fallback inspected")
        return
    print("feed gamePk", feed.get("gamePk"),
          "game type", feed.get("gameData", {}).get("game", {}).get("type"),
          "status", feed.get("gameData", {}).get("status", {}))
    home = feed.get("liveData", {}).get("boxscore", {}).get("teams", {}).get("home", {})
    print("boxscore pitchers", len(home.get("pitchers", [])), "player entries", len(home.get("players", {})))
    ids = home.get("pitchers", [])
    if ids:
        row = home.get("players", {}).get("ID" + str(ids[0]), {})
        print("first pitcher stat keys", sorted(row.get("stats", {}).get("pitching", {})))
    if feed.get("gamePk") != game_id:
        raise RuntimeError("Schedule/feed game identity mismatch.")
    print("AUDIT_COMPLETE")


if __name__ == "__main__":
    main()
