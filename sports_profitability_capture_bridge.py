"""Read-only bridge from an archived manual provider capture to the NHL quote parser.

This is not sportsbook offer verification, future-capture trigger, odds polling,
forecast generation, or eligibility for paper ROI. It checks the saved byte
archive and manifest against the parser's original-source contract.
"""
import hashlib
import json
import re
from datetime import timedelta
from pathlib import Path

from sports_profitability_capture import ENDPOINT, ROOT, SAFE_PARAMS
from sports_profitability_price_source import ODDS_ENDPOINT, REQUEST, observe
from sports_profitability_v1 import hash_record, utc, verify_record

SOURCE_SCHEMA = "nhl-research-provider-original-v1"


def parse_archived_capture(repo_root, manifest_path, official):
    """Convert one previously archived original into an unqualified observation.

    The official identity must independently originate from original NHL/ESPN
    schedule evidence; this function does NOT independently certify it.
    Local timestamps and hashes never prove GitHub publication or that a
    sportsbook offered an executable bet.
    """
    root = Path(repo_root).resolve()
    stored = (root / manifest_path).resolve()
    captures = (root / ROOT / "captures").resolve()
    if stored.parent != captures or not re.fullmatch(
            r"\d{8}T\d{12}Z\.json", stored.name):
        raise ValueError("Manifest must have the pinned NHL capture path/name")
    if not stored.is_file():
        raise ValueError("Original source capture manifest is missing")
    raw_manifest = stored.read_bytes()
    if len(raw_manifest) > 100_000:
        raise ValueError("Unreasonably large source manifest")
    try:
        manifest = json.loads(raw_manifest)
    except (UnicodeError, ValueError):
        raise ValueError("Archived NHL capture manifest is invalid JSON") from None
    if not isinstance(manifest, dict) or (
            manifest.get("schema") != SOURCE_SCHEMA or
            manifest.get("source_url") != ENDPOINT or
            ENDPOINT != ODDS_ENDPOINT or
            manifest.get("request_parameters") != SAFE_PARAMS or
            SAFE_PARAMS != REQUEST):
        raise ValueError("Original provider capture contract not pinned to safe request")
    if (manifest.get("NO_BET") is not True or
            type(manifest.get("actual_wagers")) is not int or
            manifest["actual_wagers"] != 0 or
            any(manifest.get(k) is not False for k in (
                "exact_crosswalk_with_official_nhl",
                "sportsbook_offer_executability_verified",
                "bookmaker_publication_time_verified",
                "last_pre_start_offering_verified",
                "qualified_for_paper_roi"))):
        raise ValueError("Cannot promote an unverified research capture")
    digest = manifest.get("raw_entity_body_sha256")
    if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
        raise ValueError("Source SHA-256 is missing or malformed")
    archive = (ROOT / "originals" / (digest + ".json")).as_posix()
    # Default workflow stores repo-relative paths. Explicit-root offline tests
    # store the same pinned archive as an absolute path; neither can escape.
    if manifest.get("original_path") not in (archive, str(root / archive)):
        raise ValueError("Raw body source is not the original content-addressed file")
    retrieved = utc(manifest.get("retrieved_at"))
    archived = utc(manifest.get("archived_at"))
    if not retrieved <= archived or archived - retrieved > timedelta(minutes=5):
        raise ValueError("Source retrieval/archive time ordering or freshness invalid")
    # Filenames are NOT server clocks but must not contradict local capture time.
    if stored.stem != retrieved.strftime("%Y%m%dT%H%M%S%fZ"):
        raise ValueError("Original capture filename disagrees with retrieval time")
    raw = (root / archive).resolve()
    if not raw.is_relative_to((root / ROOT / "originals").resolve()) or (
            not raw.is_file()):
        raise ValueError("Original NHL bytes absent from pinned archive directory")
    source_bytes = raw.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != digest:
        raise ValueError("Saved original NHL response bytes differ from SHA-256")
    try:
        saved_events = json.loads(source_bytes)
    except (UnicodeError, ValueError):
        raise ValueError("Original source is not valid JSON") from None
    if not isinstance(saved_events, list) or manifest.get("event_rows_returned") != len(saved_events):
        raise ValueError("Manifest event count disagrees with original response")
    count_future = sum(utc(e["commence_time"]) > retrieved for e in saved_events)
    if (manifest.get("still_future_events_at_retrieval") != count_future or
            manifest.get("already_started_events_at_retrieval") != len(saved_events) - count_future):
        raise ValueError("Provider event coverage disagrees with preserved bytes")
    source = {
        "path": archive,
        "source_url": ENDPOINT,
        "request_parameters": dict(SAFE_PARAMS),
        "sha256": digest,
        "retrieved_at": manifest["retrieved_at"],
    }
    quote = observe(root, source, official, manifest["archived_at"])
    quote["source_manifest_path"] = stored.relative_to(root).as_posix()
    quote["source_manifest_sha256"] = hashlib.sha256(raw_manifest).hexdigest()
    quote["qualified_for_paper_roi"] = False
    quote["publication_server_attested"] = False
    quote["sha256"] = hash_record({k: v for k, v in quote.items() if k != "sha256"})
    verify_record(quote)
    return quote
