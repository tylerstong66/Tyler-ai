"""Harden MLB shadow forecast publication: ONLY newly-added, sealed pregame files.

The scheduled capture workflow must reject staged modifications, deletions,
renames and non-prediction changes rather than silently replacing an old record.
No sportsbooks, wagers or Tyler production API calls.
"""
import argparse
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sports_mlb_prop_prospective import _verify
from sports_mlb_sources import utc

PREDICTION_DIR="benchmarks/mlb_hitter_props_shadow_v1/predictions/"


def inspect_staged_pregame_additions(*, repo=".", now=None, margin_seconds=180):
    if (isinstance(margin_seconds,bool) or not isinstance(margin_seconds,int)
            or not 120<=margin_seconds<=3600):
        raise ValueError("Publication window must be between 2 and 60 minutes.")
    current=utc(now if now is not None else datetime.now(timezone.utc))
    output=subprocess.check_output(
        ["git","diff","--cached","--name-status","-z"],cwd=repo)
    entries=output.split(b"\x00")
    if entries[-1:] == [b""]:
        entries.pop()
    if len(entries)%2:
        raise ValueError("Unexpected git staged filename/status encoding.")
    verified=[]
    for i in range(0,len(entries),2):
        status=entries[i].decode("ascii")
        name=entries[i+1].decode("utf-8")
        # Rename/copy formats carry an extra filename; rejecting the status
        # before trying to interpret it is intentional.
        if status!="A":
            raise ValueError("Blocked existing forecast mutation or non-addition: "+status)
        if (not name.startswith(PREDICTION_DIR) or
                not name.endswith(".json") or
                "/" in name[len(PREDICTION_DIR):]):
            raise ValueError("Blocked staged file outside immutable forecast directory.")
        p=Path(repo)/name
        obj=json.loads(p.read_text(encoding="utf-8"))
        record=_verify(obj)
        if name != PREDICTION_DIR+str(record.get("game_id"))+"_"+str(record.get("hitter_id"))+".json":
            raise ValueError("Staged forecast filename is not its official game/hitter ID.")
        if (record.get("status")!="IMMUTABLE_PREGAME_SHADOW_NO_BET" or
                record.get("model_calibrated") is not False or
                record.get("sportsbook_wager_eligible") is not False or
                record.get("actual_wager")!=0):
            raise ValueError("Only experimental no-wager shadow predictions may be staged.")
        frozen=utc(record.get("frozen_at_utc"))
        scheduled=utc(record.get("event_start_utc"))
        if frozen>=scheduled or frozen>current:
            raise ValueError("Forecast freeze timestamp is outside valid pregame chronology.")
        if current+timedelta(seconds=margin_seconds)>=scheduled:
            raise ValueError("Too late to safely publish an MLB forecast before first pitch.")
        verified.append({
            "game_id":record["game_id"],"hitter_id":record["hitter_id"],
            "path":name,"record_digest_sha256":obj["record_digest_sha256"],
            "scheduled_first_pitch_utc":scheduled.isoformat()
        })
    if not verified:
        raise ValueError("No new pregame forecast additions staged for publication.")
    return {
        "publishable_new_immutable_files":len(verified),
        "checked_utc":current.isoformat(),"margin_seconds":margin_seconds,
        "staged_additions_only":True,
        "records":verified,"no_wagers":True,
    }


def main():
    p=argparse.ArgumentParser(description="Require new, never-updated MLB pregame files")
    p.add_argument("--repo",default=".")
    args=p.parse_args()
    print("MLB_PREGAME_PUBLICATION_GUARD="+json.dumps(
        inspect_staged_pregame_additions(repo=args.repo),sort_keys=True))


if __name__=="__main__":
    main()
