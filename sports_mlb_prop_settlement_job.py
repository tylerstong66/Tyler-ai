"""One-shot read-only MLB official-final settlement for frozen hitter shadow files.

Writes only *new* settlement records. It never edits or refreshes pregame
predictions, betting records, sportsbook odds or deployed Tyler services.
"""
import argparse
import json
from pathlib import Path

from sports_mlb_prop_prospective import (
    _verify, settle_frozen_hit_props, write_exclusive_json,
    MissingOfficialBattingFieldError, OfficialStartTimeConflictError,
)
from sports_mlb_sources import OfficialMlbReader, utc

DEFAULT_ROOT="benchmarks/mlb_hitter_props_shadow_v1"


def settle_ready_records(root=DEFAULT_ROOT, *, reader=None, max_files=100):
    """Validate all saved evidence; rotate up to max_files official final checks.

    The inventory may grow beyond the per-run network budget. Selecting an
    explicit 3-hour rotating window from as-yet-unsettled, past-scheduled-start
    forecasts prevents permanently starving newer or older player-games.
    Previously settled records are never changed.
    """
    root=Path(root)
    if isinstance(max_files,bool) or not isinstance(max_files,int) or not 1<=max_files<=100:
        raise ValueError("At most 100 official MLB player-game checks per settlement run.")
    original_dir=root/"predictions"
    out_dir=root/"settlements"
    if not original_dir.exists():
        return {"discovered":0,"settled":0,"pending":0,"unresolved":0,
                "already_settled":0,"files":[],"unresolved_files":[],
                "eligible_unsettled":0,"attempted_official_checks":0,
                "deferred_due_to_batch_cap":0,"batch_window":None,
                "batch_window_count":0}
    reader=reader or OfficialMlbReader()
    now=utc(reader.clock())
    entries=sorted(original_dir.glob("*.json"))
    if len(entries)>30000:
        raise ValueError("Unexpectedly many sealed MLB predictions; refuse unbounded inventory.")
    candidates=[]
    existing=0
    pregame=0
    # FIRST preflight all predictions, settlement hashes and identities before
    # writing even one new immutable official result. No silent partial batch.
    for path in entries:
        record=json.loads(path.read_text(encoding="utf-8"))
        core=_verify(record)
        game=core.get("game_id")
        hitter=core.get("hitter_id")
        if path.name!=str(game)+"_"+str(hitter)+".json":
            raise ValueError("Frozen forecast file naming does not match immutable game/player IDs.")
        target=out_dir/path.name
        if target.exists():
            previous=json.loads(target.read_text(encoding="utf-8"))
            sealed=_verify(previous)
            if (sealed.get("game_id")!=game or sealed.get("hitter_id")!=hitter
                    or previous.get("prediction_digest_sha256")!=record["record_digest_sha256"]):
                raise ValueError("Existing settlement identity or original forecast link is invalid.")
            existing+=1
            continue
        kickoff=utc(core["event_start_utc"])
        if now<=kickoff:
            pregame+=1
            continue
        candidates.append((kickoff,game,hitter,path,record,target))
    candidates.sort(key=lambda entry:(entry[0],entry[1],entry[2]))
    window_count=(len(candidates)+max_files-1)//max_files
    # Scheduled workflow runs at most every three hours; the bounded,
    # deterministic slice cycles through ALL remaining eligible windows.
    slot=int(now.timestamp())//(3*3600)
    window=slot%window_count if window_count else None
    selected=(candidates[window*max_files:(window+1)*max_files]
              if window is not None else [])
    deferred=len(candidates)-len(selected)
    pending=pregame+deferred
    unresolved=0
    unresolved_files=[]
    done=0
    files=[]
    for kickoff,game,hitter,path,record,target in selected:
        official,_=reader.load("game/"+str(game)+"/feed/live",api_version="v1.1")
        status=official.get("gameData",{}).get("status",{})
        if official.get("gamePk")!=game:
            raise ValueError("Official live MLB result gamePk mismatches frozen file.")
        if status.get("abstractGameState")!="Final":
            pending+=1
            continue
        try:
            # Independently verifies MLB final source, team/player identity,
            # counts and timestamp against the saved pregame forecast.
            result=settle_frozen_hit_props(record,reader=reader)
        except OfficialStartTimeConflictError as error:
            # The direct settlement validator has already rejected this exact
            # player-game after checking strict final status and both teams.
            # Preserve its original; retry later without blocking other games.
            unresolved+=1
            unresolved_files.append({"game_id":game,"hitter_id":hitter,
                "field":"scheduledStart",
                "reason":"OFFICIAL_FINAL_START_DIFFERS_FROM_FROZEN_RETRY",
                "frozen_start_utc":error.frozen_start,
                "official_start_utc":error.official_start,
                "prediction_digest_sha256":record["record_digest_sha256"],
                "official_final_source":error.source})
            continue
        except MissingOfficialBattingFieldError as error:
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
        "discovered":len(entries),"settled":done,"pending":pending,
        "unresolved":unresolved,"unresolved_files":unresolved_files,
        "already_settled":existing,"files":files,
        "eligible_unsettled":len(candidates),
        "attempted_official_checks":len(selected),
        "deferred_due_to_batch_cap":deferred,
        "batch_window":window,"batch_window_count":window_count,
        "only_separate_result_files_written":True,"wagers":0,
    }


def main():
    parser=argparse.ArgumentParser(description="Official MLB final settlement; no wagers")
    parser.add_argument("--root",default=DEFAULT_ROOT)
    args=parser.parse_args()
    report=settle_ready_records(args.root)
    print("MLB_SHADOW_OFFICIAL_SETTLEMENT_REPORT="+json.dumps(report,sort_keys=True))
    if report["unresolved"]:
        print("::warning::Official final MLB source fields unresolved for "
              +str(report["unresolved"])+" frozen player-games; no labels fabricated.")


if __name__=="__main__":
    main()
