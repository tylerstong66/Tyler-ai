"""Read-only archived-source receipt validation for NCAA/NBA research.

An authentic SHA-256-linked ESPN source proves only the retained provider
bytes; it does not independently verify a game result or certify completeness.
"""
import hashlib
import json
from pathlib import Path

import sports_expansion_observer as source
from sports_expansion_audit import bounded_gzip_read

def verify_espn_receipt(capture_dir, league, game_id):
    """Derive provider evidence from original archived bytes, never caller flags."""
    if league not in source.LEAGUES:
        raise ValueError("Unsupported league")
    game_id=str(game_id)
    if not game_id.isdigit():
        raise ValueError("Invalid game identity")
    folder=Path(capture_dir)
    manifest=json.loads((folder/"manifest.json").read_text())
    if (manifest.get("schema")!="tyler-college-nba-provider-observation-v1"
            or manifest.get("NO_BET") is not True
            or manifest.get("actual_wagers") != 0
            or manifest.get("forecasting_enabled") is not False):
        raise ValueError("Invalid saved provider receipt")
    found=[]
    for snap in manifest["snapshots"]:
        if snap["league"]!=league:
            continue
        filename=snap["compressed_file"]
        expected=league+"_"+snap["day"]+".json.gz"
        if filename!=expected:
            raise ValueError("Archived filename does not match receipt")
        path=folder/filename
        if not path.is_file() or path.stat().st_size>8_500_000:
            raise ValueError("Missing or oversized source archive")
        raw=bounded_gzip_read(path.read_bytes())
        if hashlib.sha256(raw).hexdigest()!=snap["original_response_sha256"]:
            raise ValueError("Source response digest mismatch")
        parsed=source.parse_scoreboard(json.loads(raw),league)
        if parsed!=snap["parsed"]:
            raise ValueError("Archived source normalization changed")
        found.extend(row for row in parsed["games"] if row["game_id"]==game_id)
    if not found:
        raise ValueError("Game absent from verified original source")
    keys=("scheduled_start_utc","home_team_id","away_team_id",
          "state","home_score","away_score","provider_completed")
    if any(any(row[key]!=found[0][key] for key in keys) for row in found[1:]):
        raise ValueError("Conflicting saved game evidence")
    return {
        "schema":"tyler-espn-original-source-receipt-v1",
        "league":league,"game_id":game_id,
        "provider_observations_verified":len(found),
        "source_archive_sha256_verified":True,
        "independent_official_final_verified":False,
        "identity_crosswalk_verified":False,
        "source_scope_complete":False,
        "eligible_for_historical_evaluation":False,
        "forecasting_enabled":False,"NO_BET":True,"actual_wagers":0,
    }
