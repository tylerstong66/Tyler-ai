"""Manual-only NHL odds ORIGINAL-BODY capture, unqualified for betting claims.

Does not forecast, grade, wager, activate schedules or claim book availability.
A GitHub Actions manual workflow may retain these source bytes when a user
separately configures an API key. No credentials are logged or persisted.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

from sports_profitability_v1 import utc
from sports_expansion_audit import archive_path, strict_json_loads

ENDPOINT = "https://api.the-odds-api.com/v4/sports/icehockey_nhl/odds"
SAFE_PARAMS = {
    "regions": "us",
    "markets": "h2h",
    "bookmakers": "draftkings",
    "oddsFormat": "american",
}
ROOT = Path("benchmarks/nhl_price_source_observations_v1")
MAX_RESPONSE_BYTES = 3_000_000


def observe_source(api_key, *, root=ROOT, get=None, clock=None):
    """Retain exact decoded HTTP response body with sanitized provenance.

    Does NOT turn external aggregator prices into executable sportsbook odds.
    """
    if not isinstance(api_key, str) or not api_key or any(
            char.isspace() for char in api_key):
        raise ValueError("An API key must be configured as a secret")
    root = Path(root)
    for folder in (root, root / "originals", root / "captures"):
        archive_path(folder, directory=True, allow_missing=True)
    get = get or requests.get
    clock = clock or (lambda: datetime.now(timezone.utc))
    requested = {**SAFE_PARAMS, "apiKey": api_key}
    try:
        response = get(ENDPOINT, params=requested, timeout=20,
                       allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError("NHL odds provider returned a non-200 response")
        raw = response.content
    except requests.RequestException:
        raise RuntimeError("NHL odds provider request failed; nothing archived") from None
    # Never log the request URL, exception object, headers, response text or key.
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("NHL odds original response missing or beyond bounded size")
    if api_key.encode() in raw:
        raise ValueError("Provider response contains confidential token; not archiving")
    try:
        events = strict_json_loads(raw)
    except (UnicodeError, ValueError):
        raise ValueError("Provider original NHL odds response is not valid JSON") from None
    if not isinstance(events, list):
        raise ValueError("Provider NHL odds event array missing")
    now = utc(clock().isoformat())
    future, already_started, ids = 0, 0, set()
    for event in events:
        if not isinstance(event, dict) or event.get("sport_key") != "icehockey_nhl":
            raise ValueError("Odds response mixed or malformed sport rows")
        identifier = event.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError("Missing or duplicate event identifier")
        ids.add(identifier)
        start = utc(event.get("commence_time"))
        if start > now:
            future += 1
        else:
            already_started += 1
        if not isinstance(event.get("bookmakers"), list):
            raise ValueError("Bookmaker observations are not an array")
    digest = hashlib.sha256(raw).hexdigest()
    original = root / "originals" / (digest + ".json")
    stamp = now.strftime("%Y%m%dT%H%M%S%fZ")
    manifest_path = root / "captures" / (stamp + ".json")
    archive_path(original, allow_missing=True)
    archive_path(manifest_path, allow_missing=True)
    original.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    if original.exists():
        if original.read_bytes() != raw:
            raise ValueError("Content-addressed source collision")
    else:
        with original.open("xb") as stream:
            stream.write(raw)
    archived_at = utc(clock().isoformat())
    if archived_at < now or (archived_at - now).total_seconds() > 300:
        raise ValueError("Original NHL source archive lag exceeds five minutes")
    manifest = {
        "schema": "nhl-research-provider-original-v1",
        "archived_at": archived_at.isoformat(),
        "source_url": ENDPOINT,
        "request_parameters": SAFE_PARAMS,
        "retrieved_at": now.isoformat(),
        "raw_entity_body_sha256": digest,
        "original_path": original.as_posix(),
        "event_rows_returned": len(events),
        "still_future_events_at_retrieval": future,
        "already_started_events_at_retrieval": already_started,
        "exact_crosswalk_with_official_nhl": False,
        "sportsbook_offer_executability_verified": False,
        "bookmaker_publication_time_verified": False,
        "last_pre_start_offering_verified": False,
        "qualified_for_paper_roi": False,
        "NO_BET": True, "actual_wagers": 0,
        "limitation": (
            "Raw-body research observation only. Provider feed last_update is "
            "not independently certified sportsbook offering time, and "
            "GitHub server publication chronology is not attested here."),
    }
    # Exclusive manifests prevent silent timestamp/source replacement.
    with manifest_path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    return {
        "status": "unqualified_source_only",
        "manifest_path": manifest_path.as_posix(),
        "original_sha256": digest,
        "future_events": future,
        "started_events": already_started,
        "NO_BET": True,
        "actual_wagers": 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Manual NHL original odds evidence archive, no bets")
    parser.add_argument("--capture", action="store_true",
                        help="Explicitly use configured secret; default NEVER fetches")
    args = parser.parse_args()
    if not args.capture:
        print(json.dumps({"status": "inactive_no_network",
                          "NO_BET": True, "actual_wagers": 0}))
        return
    key = os.environ.get("THE_ODDS_API_KEY")
    if not key:
        raise SystemExit("No NHL research odds API secret configured; no collection performed")
    print(json.dumps(observe_source(key), sort_keys=True))


if __name__ == "__main__":
    main()
