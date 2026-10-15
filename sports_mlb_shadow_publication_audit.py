"""Audit original git publication history for immutable MLB pregame forecasts.

Git commit author/committer timestamps are Git metadata, NOT an independent
server receipt or a cryptographic proof of when a push became visible.
Identifies changed forecasts, mismatched committed bytes and after-event
commit metadata without falsely calling this independently attested.
"""
import argparse
import json
import subprocess
from pathlib import Path
from datetime import timedelta
from sports_mlb_prop_prospective import _verify
from sports_mlb_sources import utc

PREDICTION_DIR="benchmarks/mlb_hitter_props_shadow_v1/predictions/"


def _git(repo, *args):
    return subprocess.check_output(["git",*args],cwd=repo,stderr=subprocess.PIPE)


def audit_forecast_publication(*, repo="."):
    root=Path(repo)
    paths=sorted((root/PREDICTION_DIR).glob("*.json"))
    if not paths:
        return {
            "status":"NO_FROZEN_FORECASTS","checked_records":0,
            "git_metadata_pregame":0,"verified_unchanged_git_blobs":0,
            "independently_attested_publish_times":0,"prospective_proof_established":False,
            "records":[]
        }
    records=[]
    passed=0
    problems=[]
    for path in paths:
        relative=PREDICTION_DIR+path.name
        obj=json.loads(path.read_text(encoding="utf-8"))
        core=_verify(obj)
        if relative!=PREDICTION_DIR+str(core.get("game_id"))+"_"+str(core.get("hitter_id"))+".json":
            raise ValueError("MLB published forecast has mismatched player/game ID filename.")
        if (core.get("status")!="IMMUTABLE_PREGAME_SHADOW_NO_BET" or
                core.get("actual_wager")!=0 or
                core.get("sportsbook_wager_eligible") is not False):
            raise ValueError("An unexpected betting-capable record is in the shadow directory.")
        frozen=utc(core["frozen_at_utc"])
        event=utc(core["event_start_utc"])
        changes=_git(repo,"log","--format=%H","HEAD","--",relative).decode().split()
        if len(changes)!=1:
            problems.append(relative+": expected exactly one Git addition, found "+str(len(changes))+" changes.")
            records.append({"path":relative,"status":"MODIFIED_OR_NO_FULL_GIT_HISTORY",
                            "change_count":len(changes),"metadata_pregame":False})
            continue
        sha=changes[0]
        change=_git(repo,"diff-tree","--root","--no-commit-id","--name-status","-r",sha,
                    "--",relative).decode("utf-8").splitlines()
        if change!=["A\t"+relative]:
            problems.append(relative+": original commit did not add this path.")
            records.append({"path":relative,"status":"NOT_ORIGINAL_ADDITION",
                            "first_commit_sha":sha,"metadata_pregame":False})
            continue
        committed=_git(repo,"show",sha+":"+relative)
        if committed!=path.read_bytes():
            problems.append(relative+": current content differs from original committed blob.")
            records.append({"path":relative,"status":"ORIGINAL_BLOB_MISMATCH",
                            "first_commit_sha":sha,"metadata_pregame":False})
            continue
        timestamp=_git(repo,"show","-s","--format=%aI%n%cI",sha).decode().splitlines()
        if len(timestamp)!=2:
            raise ValueError("Missing author/committer timestamp metadata.")
        author,committer=(utc(ts) for ts in timestamp)
        # Git commit dates have second precision; preserve ambiguous subsecond
        # ordering instead of treating it as definite pre/post freeze evidence.
        precise_order_unresolved = frozen > author or frozen > committer
        chronological=(frozen<event and author<event and committer<event
                       and frozen<committer+timedelta(seconds=1)
                       and frozen<author+timedelta(seconds=1))
        records.append({
            "path":relative,"game_id":core["game_id"],"hitter_id":core["hitter_id"],
            "first_commit_sha":sha,"change_count":1,"status":
                "GIT_COMMIT_METADATA_PREGAME_SUBSECOND_ORDER_UNKNOWN" if chronological and precise_order_unresolved
                else "GIT_COMMIT_METADATA_PREGAME_NOT_INDEPENDENTLY_ATTESTED" if chronological
                else "GIT_METADATA_NOT_PREGAME",
            "frozen_at_utc":frozen.isoformat(),
            "author_date_utc":author.isoformat(),
            "committer_date_utc":committer.isoformat(),
            "event_start_utc":event.isoformat(),
            "metadata_pregame":chronological,
            "subsecond_order_not_resolved":precise_order_unresolved,
            "original_committed_blob_unchanged":True,
        })
        if chronological:
            passed+=1
        else:
            problems.append(relative+": freeze/commit metadata did not precede event.")
    return {
        "status":"GIT_HISTORY_REVIEW_PASS_NOT_SERVER_ATTESTED" if not problems
                 else "GIT_HISTORY_REVIEW_FOUND_PROBLEMS",
        "checked_records":len(paths),
        "git_metadata_pregame":passed,
        "verified_unchanged_git_blobs":sum(x.get("original_committed_blob_unchanged") is True for x in records),
        "distinct_official_games":len({x["game_id"] for x in records if "game_id" in x}),
        "independently_attested_publish_times":0,
        "subsecond_metadata_order_uncertain":sum(x.get("subsecond_order_not_resolved") is True for x in records),
        "prospective_proof_established":False,
        "limitations":[
            "Git author/committer timestamps can be set by the committer; they are not independent GitHub server push receipts.",
            "Git commit timestamps have whole-second resolution, making the subsecond ordering of freeze and commit dates uncertain.",
            "Full repository history is required; a shallow checkout cannot establish no modifications.",
            "Event time is the official first pitch scheduled at freeze, not independently verified actual first pitch.",
            "Original content hashes and Git history preserve a useful auditable trail, but do not alone certify a prospective betting edge."
        ],
        "problems":problems,
        "records":records,
    }


def main():
    p=argparse.ArgumentParser(description="Review original Git publication metadata for pregame hitter research")
    p.add_argument("--repo",default=".")
    args=p.parse_args()
    report=audit_forecast_publication(repo=args.repo)
    print(json.dumps(report,indent=2,sort_keys=True,allow_nan=False))
    if report["problems"]:
        raise SystemExit("Frozen MLB forecast publication history has unresolved problems.")


if __name__=="__main__":
    main()
