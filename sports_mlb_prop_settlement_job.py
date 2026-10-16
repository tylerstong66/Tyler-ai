"""One-shot read-only MLB official-final settlement for frozen hitter shadow files.

Writes only *new* settlement records. It never edits or refreshes pregame
predictions, betting records, sportsbook odds or deployed Tyler services.
"""
import argparse
import json
from pathlib import Path

from sports_mlb_prop_prospective import (
    _verify, settle_frozen_hit_props, write_exclusive_json,
    MissingOfficialBattingFieldError,
)
from sports_mlb_sources import OfficialMlbReader, utc

DEFAULT_ROOT="benchmarks/mlb_hitter_props_shadow_v1"


def settle_ready_records(root=DEFAULT_ROOT, *, reader=None, max_files=100):
    root=Path(root)
    if isinstance(max_files,bool) or not isinstance(max_files,int) or not 1<=max_files<=100:
        raise ValueError("At most 100 frozen shadow predictions per settlement run.")
    original_dir=root/"predictions"
    out_dir=root/"settlements"
    if not original_dir.exists():
        return {"discovered":0,"settled":0,"pending":0,"unresolved":0,
                "already_settled":0,"files":[],"unresolved_files":[]}
    pending=0
    unresolved=0
    unresolved_files=[]
    done=0
    existing=0
    discovered=0
    files=[]
    reader=reader or OfficialMlbReader()
    entries=sorted(original_dir.glob("*.json"))
    if len(entries)>max_files:
        raise ValueError("More pregame snapshots exist than allowed; refuse partial silent settlement.")
    for path in entries:
        record=json.loads(path.read_text(encoding="utf-8"))
        core=_verify(record)
        game=core.get("game_id")
        hitter=core.get("hitter_id")
        if path.name!=str(game)+"_"+str(hitter)+".json":
            raise ValueError("Frozen forecast file naming does not match immutable game/player IDs.")
        discovered+=1
        target=out_dir/path.name
        if target.exists():
            previous=json.loads(target.read_text(encoding="utf-8"))
            _verify(previous)
            if previous.get("prediction_digest_sha256")!=record["record_digest_sha256"]:
                raise ValueError("Existing settlement points at the wrong frozen prediction.")
            existing+=1
            continue
        now=utc(reader.clock())
        if now<=utc(core["event_start_utc"]):
            pending+=1
            continue
        official,_=reader.load("game/"+str(game)+"/feed/live",api_version="v1.1")
        status=official.get("gameData",{}).get("status",{})
        if official.get("gamePk")!=game:
            raise ValueError("Official live MLB result gamePk mismatches frozen file.")
        if status.get("abstractGameState")!="Final":
            pending+=1
            continue
        # Re-read through settlement routine, independently verifying final
        # official event time, team IDs, hitter ID and conditional outcome.
        try:
            result=settle_frozen_hit_props(record,reader=reader)
        except MissingOfficialBattingFieldError as error:
            # An absent official count is not a verified zero. Never write an
            # immutable grade that could be contradicted by a later feed.
            # Actual wrong types, impossible counts and identity drift still fail.
            unresolved+=1
            reason=("OFFICIAL_FINAL_AT_BATS_UNAVAILABLE_RETRY"
                    if error.field=="atBats"
                    else "OFFICIAL_FINAL_BATTING_FIELD_UNAVAILABLE_RETRY")
            unresolved_files.append({"game_id":game,"hitter_id":hitter,
                                     "field":error.field,"reason":reason})
            continue
        write_exclusive_json(target,result)
        done+=1
        files.append({"path":str(target),"status":result["status"],
                      "prediction_digest":record["record_digest_sha256"],
                      "settlement_digest":result["record_digest_sha256"]})
    return {
        "discovered":discovered,"settled":done,"pending":pending,
        "unresolved":unresolved,"unresolved_files":unresolved_files,
        "already_settled":existing,"files":files,
        "only_separate_result_files_written":True,"wagers":0,
    }


def main():
    parser=argparse.ArgumentParser(description="Official MLB final settlement; no wagers")
    parser.add_argument("--root",default=DEFAULT_ROOT)
    args=parser.parse_args()
    report=settle_ready_records(args.root)
    print("MLB_SHADOW_OFFICIAL_SETTLEMENT_REPORT="+json.dumps(report,sort_keys=True))
    if report["unresolved"]:
        print("::warning::Official final MLB batting count unresolved for "
              +str(report["unresolved"])+" frozen player-games; no labels fabricated.")


if __name__=="__main__":
    main()
