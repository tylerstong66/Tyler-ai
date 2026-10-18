"""Replay NCAA/ESPN final agreements from hash-linked archives, research only.

Result observations are postgame labels, never pregame features. A receipt
proves retained bytes and chronology, not upstream schedule completeness or
independent publication attestation. No forecast or model eligibility is granted.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import sports_college_dual_source_finals as finals
import sports_expansion_audit as audit
import sports_expansion_observer as espn
import sports_ncaa_espn_crosswalk_receipts as crosswalk
import sports_ncaa_espn_identity as identity
import sports_ncaa_official_source as ncaa

ROOT = espn.ROOT / "college_final_research"


def _manifest(folder):
    raw = (folder / "manifest.json").read_bytes()
    saved = json.loads(raw)
    at = espn.utc(saved["recorded_at_utc"])
    if at.strftime("%Y%m%dT%H%M%S%fZ") != folder.name:
        raise ValueError("Capture folder differs from immutable recorded timestamp")
    return saved, at, hashlib.sha256(raw).hexdigest()


def build(root, stamp):
    """Derive one deterministic dataset from an explicit saved crosswalk capture."""
    root = Path(root)
    # Validate the identifier and replay the complete saved identity report first.
    crosswalk.verify(root, stamp)
    folder = root / identity.ROOT / "captures" / stamp
    saved, recorded, crosswalk_sha = _manifest(folder)
    nf = root / ncaa.ROOT / "captures" / saved["ncaa_capture"]
    ef = root / espn.ROOT / "captures" / saved["espn_capture"]
    ns, nt, nsha = _manifest(nf)
    es, et, esha = _manifest(ef)
    if nt > recorded or et > recorded:
        raise ValueError("Source captured after crosswalk receipt")
    # Full ESPN audit verifies original endpoints, timestamps, closed filenames,
    # response digests, normalization and quarantines, including this capture.
    audit.audit(root)
    if ns.get("source_query_hash") != ncaa.SCOREBOARD_QUERY_HASH:
        raise ValueError("Unexpected NCAA source query identity")
    for snap in ns["snapshots"]:
        league, window = snap["league"], snap["window"]
        if league == "NCAAF_FBS":
            if len(window) != 7 or not window.startswith("week-") or not window[5:].isdigit():
                raise ValueError("Invalid NCAA football source window")
            url = ncaa.graph_url(league, year=2026, week=int(window[5:]))
        else:
            url = ncaa.graph_url(league, year=2026, day=window)
        if snap["source_url"] != url:
            raise ValueError("NCAA source endpoint differs from receipt scope")
    official = identity.verify_ncaa(nf, ns)
    provider = identity.verify_espn(ef, es)
    report = finals.classify(official, provider)
    accepted = []
    pending = list(report["pending"])
    official_by_id = {(r["league"], r["ncaa_game_id"]): r for r in official}
    provider_by_id = {(r["league"], r["espn_game_id"]): r for r in provider}
    for row in report["corroborated_research_only"]:
        # Both final-bearing source observations must follow BOTH saved starts.
        # The later retrieval is availability of corroboration, not game end time.
        n = official_by_id[(row["league"], row["ncaa_game_id"])]
        nstart = espn.utc(datetime.fromtimestamp(
            int(n["source_start_time_epoch"]), timezone.utc).isoformat())
        start = max(nstart, espn.utc(row["scheduled_start_utc"]))
        if min(nt, et) <= start:
            pending.append({"league": row["league"], "espn_game_id": row["espn_game_id"],
                            "ncaa_game_id": row["ncaa_game_id"],
                            "reason": "FINAL_OBSERVED_AT_OR_BEFORE_SAVED_START"})
            continue
        e = provider_by_id[(row["league"], row["espn_game_id"])]
        accepted.append({**row,
            "ncaa_home_school": n["home_name"], "ncaa_away_school": n["away_name"],
            "espn_home_team_id": e["home_team_id"],
            "espn_away_team_id": e["away_team_id"],
            "ncaa_source_observed_at_utc": nt.isoformat(),
            "espn_source_observed_at_utc": et.isoformat(),
            "corroboration_available_at_utc": max(nt, et).isoformat(),
            "ncaa_scheduled_start_utc": nstart.isoformat(),
            "source_archive_sha256_verified": True,
            "result_observation_chronology_verified": True,
            "pregame_feature_chronology_verified": False,
        })
    return {
        "schema": "tyler-college-archived-final-research-v2",
        "crosswalk_capture": stamp, "crosswalk_manifest_sha256": crosswalk_sha,
        "source_pair_observed_at_utc": max(nt, et).isoformat(),
        "ncaa_capture": nf.name, "ncaa_manifest_sha256": nsha,
        "espn_capture": ef.name, "espn_manifest_sha256": esha,
        "ncaa_response_sha256": sorted({s["source_sha256"] for s in ns["snapshots"]}),
        "espn_response_sha256": sorted({s["original_response_sha256"] for s in es["snapshots"]}),
        "two_source_final_agreements": len(accepted),
        "corroborated_research_only": accepted,
        "pending_or_quarantined": len(pending), "pending": pending,
        "source_scope_complete": False,
        "independent_official_final_certification_complete": False,
        "historical_evaluation_enabled": False, "model_training_enabled": False,
        "forecasting_enabled": False, "promotion_allowed": False,
        "NO_BET": True, "actual_wagers": 0,
    }


def publish(root, stamp):
    """Write only reproducible bytes, preserving any existing immutable result."""
    result = build(root, stamp)
    raw = espn.canonical(result)
    dest = Path(root) / ROOT / "captures_v2" / stamp / "manifest.json"
    if dest.exists():
        if dest.read_bytes() != raw:
            raise ValueError("Existing final research receipt differs from replay")
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as stream:
            stream.write(raw)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", required=True)
    args = parser.parse_args()
    result = publish(Path("."), args.capture)
    print(json.dumps({"agreements": result["two_source_final_agreements"],
                      "pending": result["pending_or_quarantined"], "NO_BET": True}))


if __name__ == "__main__":
    main()
