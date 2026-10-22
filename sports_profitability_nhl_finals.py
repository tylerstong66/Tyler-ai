"""Replay two distinct RAW NHL final provider responses before paper settlement.

No collection, network, odds, real bets or backfills. The source pairs are
required to demonstrate exact original ID/teams/start/final scores, not just
that two arbitrary byte blobs were saved from different hostnames.
"""
import json
import re
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from sports_profitability_v1 import utc, original_bytes

ALIASES = {"NJ": "NJD", "SJ": "SJS", "TB": "TBL", "LA": "LAK", "UTAH": "UTA"}


def _scores(home, away):
    for s in (home, away):
        if isinstance(s, bool) or not isinstance(s, (int, str)):
            raise ValueError("Original NHL final score must be an integer")
        if not re.fullmatch(r"[0-9]+", str(s)):
            raise ValueError("Original NHL final score is malformed")
    return {"home": int(home), "away": int(away)}


def _read(source, root):
    raw = original_bytes(source, root)
    try:
        return json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("Archived original final response is not JSON") from exc


def _nhl_official(data, pred):
    if not isinstance(data, dict) or str(data.get("id")) != pred["game_id"]:
        raise ValueError("Original official NHL game ID differs")
    if (data.get("gameType") not in (2, 3)
            or data.get("gameState") not in ("OFF", "FINAL")
            or data.get("gameScheduleState") != "OK"):
        raise ValueError("Original NHL official response does not confirm normal final")
    if utc(data.get("startTimeUTC")) != utc(pred["kickoff"]):
        raise ValueError("Original NHL final start differs from frozen kickoff")
    teams = {}
    for side in ("home", "away"):
        side_data = data.get(side + "Team")
        if not isinstance(side_data, dict):
            raise ValueError("Original NHL final team is missing")
        if side_data.get("abbrev") != pred[side]:
            raise ValueError("Original NHL final team identity differs")
        teams[side] = side_data.get("score")
    return _scores(teams["home"], teams["away"])


def _espn(data, pred):
    if not isinstance(data, dict) or not isinstance(data.get("events"), list):
        raise ValueError("Original ESPN NHL scoreboard events missing")
    rows = [e for e in data["events"] if isinstance(e, dict)
            and str(e.get("id")) == pred["event_id"]]
    if len(rows) != 1:
        raise ValueError("Exactly one pinned ESPN NHL event required")
    event = rows[0]
    status = event.get("status")
    status_type = status.get("type") if isinstance(status, dict) else None
    if not isinstance(status_type, dict) or status_type.get("state") != "post" or (
            status_type.get("completed") is not True):
        raise ValueError("Original ESPN event is not a confirmed final")
    if utc(event.get("date")) != utc(pred["kickoff"]):
        raise ValueError("Original ESPN start differs from frozen kickoff")
    comps = event.get("competitions")
    if not isinstance(comps, list) or len(comps) != 1:
        raise ValueError("Exactly one NHL ESPN competition required")
    competitors = comps[0].get("competitors") if isinstance(comps[0], dict) else None
    if not isinstance(competitors, list) or len(competitors) != 2:
        raise ValueError("Exactly two NHL ESPN competitors required")
    sides = {}
    for row in competitors:
        if not isinstance(row, dict) or row.get("homeAway") not in ("home", "away"):
            raise ValueError("ESPN team orientation missing")
        side = row["homeAway"]
        if side in sides:
            raise ValueError("Duplicate ESPN team orientation")
        team = row.get("team")
        if not isinstance(team, dict):
            raise ValueError("ESPN team metadata missing")
        abbr = team.get("abbreviation")
        if not isinstance(abbr, str) or ALIASES.get(abbr, abbr) != pred[side]:
            raise ValueError("Pinned ESPN NHL opponent/orientation differs")
        sides[side] = row.get("score")
    if set(sides) != {"home", "away"}:
        raise ValueError("Missing NHL ESPN home/away side")
    return _scores(sides["home"], sides["away"])


def verify_final_sources(pred, result, evidence, root):
    """Verify supplied original responses with strict source/identity chronology."""
    if not isinstance(evidence, list) or len(evidence) != 2:
        raise ValueError("Two independent original NHL final responses required")
    official = espn = None
    seen_urls = set()
    for source in evidence:
        link = urlsplit(source["source_url"])
        if link.scheme != "https" or link.fragment or link.username or link.password or (
                link.port is not None):
            raise ValueError("NHL source must have exact HTTPS origin")
        if source["source_url"] in seen_urls:
            raise ValueError("Repeated final source is not independent")
        seen_urls.add(source["source_url"])
        observed = utc(source["retrieved_at"])
        if not (utc(pred["kickoff"]) < observed <= utc(result["verified_at"])):
            raise ValueError("Final source was not obtained after kickoff and before verification")
        if link.hostname == "api-web.nhle.com":
            if official is not None or link.query or (
                    link.path != "/v1/gamecenter/" + pred["game_id"] + "/landing"):
                raise ValueError("Pinned official NHL final endpoint/ID required")
            official = _nhl_official(_read(source, root), pred)
        elif link.hostname == "site.api.espn.com":
            expected_day = utc(pred["kickoff"]).astimezone(
                ZoneInfo("America/New_York")).strftime("%Y%m%d")
            if espn is not None or link.path != (
                    "/apis/site/v2/sports/hockey/nhl/scoreboard") or (
                    parse_qs(link.query, strict_parsing=True) != {"dates": [expected_day]}):
                raise ValueError("Pinned original ESPN NHL scoreboard date/route required")
            espn = _espn(_read(source, root), pred)
        else:
            raise ValueError("Unrecognized original NHL final host")
    if official is None or espn is None:
        raise ValueError("Both independent official NHL and ESPN originals required")
    if official != espn:
        raise ValueError("Official NHL and ESPN original final scores disagree")
    if result.get("scores") != official:
        raise ValueError("Paper final scores do not match two independent originals")
    if official["home"] == official["away"]:
        raise ValueError("Two-way NHL moneyline final cannot be tied")
    expected_outcome = "home" if official["home"] > official["away"] else "away"
    if result.get("outcome") != expected_outcome:
        raise ValueError("Paper winner does not match original independent final scores")
    return True
