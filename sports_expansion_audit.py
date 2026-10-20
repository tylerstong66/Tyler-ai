"""Independent read-only SHA-linked college football/hoops/NBA source audit."""
import gzip
import io
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import sports_expansion_observer as source

MAX_CAPTURES = 3000
MAX_BLOB_SIZE = 8_500_000


def archive_path(path, *, directory=False, allow_missing=False):
    """Reject static symlinks at every path component before archive access.

    Do not resolve first: that would erase the symlink evidence. This is a
    working-tree integrity check, not protection against concurrent OS mutation.
    """
    path = Path(path).absolute()
    for component in (*reversed(path.parents), path):
        if component.is_symlink():
            raise ValueError('Symlink in source archive path')
    if not path.exists() and allow_missing:
        return path
    if not (path.is_dir() if directory else path.is_file()):
        raise ValueError('Missing or nonregular source archive path')
    return path


def bounded_gzip_read(blob, limit=8_000_000):
    """Reject decompression bombs before allocating beyond the source size limit."""
    output = bytearray()
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(blob), mode="rb") as stream:
            while True:
                chunk = stream.read(min(65536, limit + 1 - len(output)))
                if not chunk:
                    return bytes(output)
                output.extend(chunk)
                if len(output) > limit:
                    raise ValueError("Decompressed source exceeds maximum response size")
    except (OSError, EOFError) as exc:
        raise ValueError("Corrupt or incomplete compressed source archive") from exc


def audit_capture(file):
    """Replay one closed source capture with all original audit safeguards."""
    file = archive_path(file)
    if file.stat().st_size > MAX_BLOB_SIZE:
        raise ValueError('Oversized source manifest')
    manifest=json.loads(file.read_text())
    recorded=source.utc(manifest["recorded_at_utc"])
    expected=recorded.strftime("%Y%m%dT%H%M%S%fZ")
    if file.parent.name!=expected:
        raise ValueError("Capture folder differs from immutable recorded timestamp")
    if (manifest.get("schema")!="tyler-college-nba-provider-observation-v1"
            or manifest.get("source_trust")!="ESPN_ONLY_NOT_INDEPENDENT_OFFICIAL_VERIFICATION"
            or manifest.get("forecasting_enabled") is not False
            or manifest.get("official_final_scoring_enabled") is not False
            or manifest.get("model_training_enabled") is not False
            or manifest.get("promotion_allowed") is not False
            or manifest.get("NO_BET") is not True
            or manifest.get("actual_wagers")!=0):
        raise ValueError("Expansion safety or immutable protocol flag mismatch")
    if 'collection_window' in manifest:
        window=source.collection_window.verify(manifest['collection_window'],recorded)
        anchor=recorded.date()
        expected=[(league,(anchor+timedelta(days=shift)).isoformat())
                  for league,config in source.LEAGUES.items()
                  for shift in range(-window['days_back'],window['days_ahead']+1)
                  if config['start']<=(anchor+timedelta(days=shift)).isoformat()<=config['end']]
        if [(snap['league'],snap['day']) for snap in manifest['snapshots']]!=expected:
            raise ValueError('Lookback capture does not match declared bounded source dates')
    rebuilt=[]
    expected_names={"manifest.json"}
    for snap in manifest["snapshots"]:
        league=snap["league"];day=snap["day"]
        if league not in source.LEAGUES:
            raise ValueError("Unknown independent league in source audit")
        url=source.scoreboard_url(league,day)
        if snap["url"]!=url:
            raise ValueError("Source endpoint scope or date does not match declared league")
        if source.utc(snap["retrieved_at_utc"])!=recorded:
            raise ValueError("Source receipt timestamp differs from capture")
        filename=league+"_"+day+".json.gz"
        if snap["compressed_file"]!=filename or filename in expected_names:
            raise ValueError("Source blob name collision or identity mismatch")
        expected_names.add(filename)
        blob=archive_path(file.parent/filename)
        if not blob.exists() or blob.stat().st_size>MAX_BLOB_SIZE:
            raise ValueError("Missing or oversized retained source archive")
        raw=bounded_gzip_read(blob.read_bytes())
        if (len(raw)>8_000_000 or
                hashlib.sha256(raw).hexdigest()!=snap["original_response_sha256"]):
            raise ValueError("Compressed source did not reproduce archived response SHA256")
        parsed=source.parse_scoreboard(json.loads(raw),league)
        if parsed!=snap["parsed"]:
            raise ValueError("Provider normalized game observations differ from raw archive")
        rebuilt.append(snap)
    if set(x.name for x in file.parent.iterdir())!=expected_names:
        raise ValueError("Untracked source file in supposed closed immutable capture")
    accepted,conflicts=source.reconcile_for_manifest(manifest,rebuilt)
    if (accepted!=manifest["undisputed_provider_games"]
            or conflicts!=manifest["quarantined_provider_games"]):
        raise ValueError("Stored provider quarantine and game selection differ from source evidence")
    return manifest, rebuilt, conflicts


def audit(base=Path(".")):
    root=Path(base)/source.ROOT
    captures=archive_path(root/"captures", directory=True, allow_missing=True)
    manifests=sorted(captures.glob("*/manifest.json"))
    if not manifests or len(manifests)>MAX_CAPTURES:
        raise ValueError("Missing or unexpectedly many expansion source captures")
    leagues=defaultdict(lambda:{"captures":0,"snapshot_days":0,"provider_games_observed":0,
                                "provider_finals_not_independently_verified":0,
                                "most_recent_capture_utc":None})
    completed=[]
    for file in manifests:
        manifest, rebuilt, conflicts = audit_capture(file)
        recorded = source.utc(manifest["recorded_at_utc"])
        for snap in rebuilt:
            league = snap["league"]
            parsed = snap["parsed"]
            record=leagues[league]
            record["snapshot_days"]+=1
            record["provider_games_observed"]+=parsed["eligible_observed"]
            record["provider_finals_not_independently_verified"]+=sum(
                game["provider_completed"] for game in parsed["games"])
            record["most_recent_capture_utc"]=recorded.isoformat()
        for name in {snap["league"] for snap in rebuilt}:
            leagues[name]["captures"]+=1
        completed.append({"capture":file.parent.name,"source_snapshots":len(rebuilt),
                          "independent_replay_verified":True,"provider_conflicts":len(conflicts)})
    report={
        "schema":"tyler-college-nba-saved-source-audit-v1",
        "captures_verified":len(manifests),
        "source_responses_verified":sum(x["source_snapshots"] for x in completed),
        "cohort_source_coverage":{name:leagues[name] for name in sorted(source.LEAGUES)},
        "latest_capture":completed[-1],
        "total_provider_conflicts_in_captures":sum(x["provider_conflicts"] for x in completed),
        "no_official_independent_final_claim":True,
        "not_yet_eligible_for_prediction":True,
        "NO_BET":True,"actual_wagers":0,"promotion_allowed":False,
        "limitation":"This replays archived ESPN evidence only. It cannot establish completeness of external schedules, official NCAA/NBA finals, or independent model skill.",
    }
    return report


def main():
    report=audit()
    dest=source.ROOT/"COVERAGE.latest.json"
    dest.write_bytes(source.canonical(report))
    print(json.dumps({
        "verified_captures":report["captures_verified"],
        "provider_source_receipts":report["source_responses_verified"],
        "independent_official_scores_available":False,
        "NO_BET":True,
    }))


if __name__=="__main__":
    main()
