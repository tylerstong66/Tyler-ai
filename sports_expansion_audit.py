"""Independent read-only SHA-linked college football/hoops/NBA source audit."""
import gzip
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import sports_expansion_observer as source

MAX_CAPTURES = 3000
MAX_BLOB_SIZE = 8_500_000


def audit(base=Path(".")):
    root=Path(base)/source.ROOT
    manifests=sorted((root/"captures").glob("*/manifest.json"))
    if not manifests or len(manifests)>MAX_CAPTURES:
        raise ValueError("Missing or unexpectedly many expansion source captures")
    leagues=defaultdict(lambda:{"captures":0,"snapshot_days":0,"provider_games_observed":0,
                                "provider_finals_not_independently_verified":0,
                                "most_recent_capture_utc":None})
    completed=[]
    for file in manifests:
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
            blob=file.parent/filename
            if not blob.exists() or blob.stat().st_size>MAX_BLOB_SIZE:
                raise ValueError("Missing or oversized retained source archive")
            raw=gzip.decompress(blob.read_bytes())
            if (len(raw)>8_000_000 or
                    hashlib.sha256(raw).hexdigest()!=snap["original_response_sha256"]):
                raise ValueError("Compressed source did not reproduce archived response SHA256")
            parsed=source.parse_scoreboard(json.loads(raw),league)
            if parsed!=snap["parsed"]:
                raise ValueError("Provider normalized game observations differ from raw archive")
            rebuilt.append(snap)
            record=leagues[league]
            record["snapshot_days"]+=1
            record["provider_games_observed"]+=parsed["eligible_observed"]
            record["provider_finals_not_independently_verified"]+=sum(
                game["provider_completed"] for game in parsed["games"])
            record["most_recent_capture_utc"]=recorded.isoformat()
        if set(x.name for x in file.parent.iterdir())!=expected_names:
            raise ValueError("Untracked source file in supposed closed immutable capture")
        accepted,conflicts=source.reconcile(rebuilt)
        if (accepted!=manifest["undisputed_provider_games"]
                or conflicts!=manifest["quarantined_provider_games"]):
            raise ValueError("Stored provider quarantine and game selection differ from source evidence")
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
