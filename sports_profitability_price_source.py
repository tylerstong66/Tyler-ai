"""Read-only parsing of ORIGINAL archived NHL sportsbook market observations.

This is not an executable sportsbook quote, a final closing line, or a paper
selection. It must never promote ESPN 'close' values or aggregation timestamps
into a verified offering. No network calls, API key handling, or wagering.
"""
import json
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from sports_profitability_v1 import (
    BOOK, MARKET, decimal_odds, hash_record, utc, verify_original,
)

ODDS_ENDPOINT = "https://api.the-odds-api.com/v4/sports/icehockey_nhl/odds"
REQUEST = {"sport": "icehockey_nhl", "markets": "h2h",
           "bookmakers": BOOK, "odds_format": "american"}


def observe(original_root, source, official, archived_at):
    """Return an UNQUALIFIED but immutable exact-market observation.

    Caller supplies a freshly archived original response and independently
    crosswalked official schedule identity. We verify every byte and identity,
    but the caller/aggregator cannot certify a DraftKings execution.
    """
    if not isinstance(source, dict) or source.get("source_url") != ODDS_ENDPOINT or (
            source.get("request_parameters") != REQUEST):
        raise ValueError("Only sanitized pinned NHL h2h American odds requests")
    if (urlsplit(source["source_url"]).query or
            urlsplit(source["source_url"]).fragment):
        raise ValueError("API secrets or query strings must never be archived")
    verify_original(source, original_root)
    if not isinstance(official, dict) or any(
            not isinstance(official.get(k), str) or not official[k]
            for k in ("game_id", "event_id", "home", "away", "home_name",
                      "away_name", "kickoff")):
        raise ValueError("Complete independently crosswalked official identity required")
    at = utc(source["retrieved_at"])
    saved = utc(archived_at)
    start = utc(official["kickoff"])
    if not at <= saved < start or saved - at > timedelta(minutes=5):
        raise ValueError("Market observation must be archived before kickoff")
    try:
        data = json.loads((Path(original_root) / source["path"]).read_bytes())
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Malformed preserved odds JSON") from exc
    if not isinstance(data, list):
        raise ValueError("NHL odds endpoint must return an event array")
    matches = [
        event for event in data
        if isinstance(event, dict)
        and event.get("sport_key") == "icehockey_nhl"
        and event.get("home_team") == official["home_name"]
        and event.get("away_team") == official["away_name"]
        and event.get("commence_time") is not None
        and utc(event["commence_time"]) == start
    ]
    if len(matches) != 1:
        raise ValueError("Exactly one NHL event must match full team names and original start")
    event = matches[0]
    if not isinstance(event.get("id"), str) or not event["id"]:
        raise ValueError("Aggregator event identifier required")
    books = event.get("bookmakers")
    if not isinstance(books, list):
        raise ValueError("Bookmaker list missing")
    matched_books = [b for b in books if isinstance(b, dict) and b.get("key") == BOOK]
    if len(matched_books) != 1:
        raise ValueError("Exactly one DraftKings quote required")
    markets = matched_books[0].get("markets")
    if not isinstance(markets, list):
        raise ValueError("Market list missing")
    selected = [m for m in markets if isinstance(m, dict) and m.get("key") == "h2h"]
    if len(selected) != 1:
        raise ValueError("Exactly one full-game h2h market required")
    market = selected[0]
    if "last_update" not in market:
        raise ValueError("Market-specific update timestamp missing; do not use bookmaker timestamp")
    updated = utc(market["last_update"])
    if updated > at or at - updated > timedelta(minutes=10):
        raise ValueError("Market price observation is future-dated or older than ten minutes")
    outcomes = market.get("outcomes")
    if not isinstance(outcomes, list) or len(outcomes) != 2:
        raise ValueError("NHL full-game two-way moneyline requires exactly two sides")
    by_name = {}
    for outcome in outcomes:
        if not isinstance(outcome, dict) or "point" in outcome or (
                "description" in outcome) or not isinstance(outcome.get("name"), str):
            raise ValueError("No alternative period, handicap or outcome descriptions")
        name = outcome["name"]
        if name in by_name:
            raise ValueError("Duplicated market selection")
        decimal_odds(outcome.get("price"))
        by_name[name] = outcome["price"]
    if set(by_name) != {official["home_name"], official["away_name"]}:
        raise ValueError("Selection names disagree with official original teams")
    quote = {
        **{k: official[k] for k in ("game_id", "event_id", "home", "away", "kickoff")},
        "provider_event_id": event["id"], "book_id": BOOK,
        "market": MARKET, "provider_market_key": "h2h", "line": None,
        "quote_phase": "entry", "prices": {
            "home": by_name[official["home_name"]],
            "away": by_name[official["away_name"]]},
        "observed_at": source["retrieved_at"],
        "aggregator_market_last_seen_at": market["last_update"],
        "provider_updated_at": None,  # Aggregator metadata is NOT a sportsbook timestamp
        "recorded_at": archived_at, "source_snapshot": source,
        "available_to_paper": False, "last_pre_start_offering_verified": False,
        "unverified_reason": (
            "Aggregator market.last_update is not evidence that the precise "
            "sportsbook offer was executable or that this was the last quote."),
        "NO_BET": True, "actual_wagers": 0,
    }
    quote["sha256"] = hash_record(quote)
    return quote
