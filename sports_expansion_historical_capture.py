"""Bounded provider-only historical acquisition for three separate sports.

Historical games fetched TODAY cannot be presented as previously published
pregame forecasts. This ledger is data for later season-split offline
development only; it cannot generate live predictions, grade wagers or
enable training before coverage and leakage tests are independently approved.
"""
import gzip
import hashlib
import json
from datetime import date,datetime,timedelta,timezone
from pathlib import Path

import requests
import sports_expansion_observer as observer
from sports_expansion_audit import bounded_gzip_read, MAX_BLOB_SIZE

ROOT=Path("benchmarks/college_nba_history_v1")
# Explicit complete-date REQUEST windows, not a declaration that every event
# within them is available in ESPN. Train on 2024 start, holdout 2025 start.
SEASONS={
    "NBA":{
        "train":("2024-10-22","2025-06-22"),
        "validation":("2025-10-21","2026-06-23"),
    },
    "NCAAF_FBS":{
        "train":("2024-08-24","2025-01-21"),
        "validation":("2025-08-23","2026-01-20"),
    },
    "NCAAM_D1":{
        "train":("2024-11-04","2025-04-08"),
        "validation":("2025-11-03","2026-04-07"),
    },
}
ORDER=("NBA","NCAAF_FBS","NCAAM_D1")


def calendar(start,end):
    first=date.fromisoformat(start);last=date.fromisoformat(end)
    if last<first:
        raise ValueError("Historical season range inverted")
    return [(first+timedelta(days=n)).isoformat()
            for n in range((last-first).days+1)]


def dates_by_league():
    return {sport:{
        split:calendar(*SEASONS[sport][split])
        for split in ("train","validation")}
        for sport in ORDER}


def verify_existing(base, sport, split, day, *, as_of=None):
    prefix=Path(base)/ROOT/"sources"/sport/split
    artifact=prefix/(day+".json.gz")
    receipt=prefix/(day+".receipt.json")
    if not artifact.exists() and not receipt.exists():
        return False
    if not artifact.exists() or not receipt.exists():
        raise ValueError("Historical source missing one sealed archive component")
    r=json.loads(receipt.read_text())
    if as_of is not None and (observer.utc(r["recorded_at_utc"]) > as_of.astimezone(timezone.utc)):
        raise ValueError("Saved historical receipt has future observation timestamp")
    if (r.get("schema")!="college-nba-history-provider-day-v1"
            or r.get("league")!=sport or r.get("split")!=split
            or r.get("source_date")!=day
            or r.get("source_url")!=observer.scoreboard_url(sport,day)
            or r.get("NO_BET") is not True
            or type(r.get("actual_wagers")) is not int or r.get("actual_wagers") != 0
            or r.get("promotion_allowed") is not False
            or r.get("independently_verified_official_scores") is not False
            or r.get("historical_results_are_not_pregame_forecasts") is not True):
        raise ValueError("Historical source identity, split or safety metadata changed")
    if artifact.stat().st_size > MAX_BLOB_SIZE:
        raise ValueError("Historical compressed source exceeds maximum archive size")
    raw=bounded_gzip_read(artifact.read_bytes())
    if hashlib.sha256(raw).hexdigest()!=r["original_response_sha256"]:
        raise ValueError("Original historical source bytes no longer match receipt")
    parsed=observer.parse_scoreboard(json.loads(raw),sport)
    if parsed!=r["parsed_provider_scoreboard"]:
        raise ValueError("Historical parsed ESPN records differ from retained source")
    return True


def capture(fetch,*,base=Path("."),now=None,per_league=20,date_plan=None):
    if type(per_league) is not int or not 1<=per_league<=30:
        raise ValueError("Historical per-league fetch budget must be 1..30")
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Source observation clock must be aware")
    base=Path(base)
    plan=date_plan if date_plan is not None else dates_by_league()
    if set(plan)!=set(ORDER):
        raise ValueError("Historical source plan cannot change sport cohort")
    new=[]
    counts={}
    # Unknown, orphaned, or cross-season source files fail the WHOLE run.
    # Auditing the complete existing archive precedes all network requests.
    known=set()
    for league in ORDER:
        if set(plan[league])!={"train","validation"}:
            raise ValueError("Historical split labels must remain separate")
        per_split=[]
        for split in ("train","validation"):
            selected=plan[league][split]
            if (not isinstance(selected,list) or
                    len(set(selected))!=len(selected) or
                    selected!=sorted(selected)):
                raise ValueError("Historical dates must be sorted and unique per split")
            per_split+=selected
            for day in selected:
                if not isinstance(day,str) or date.fromisoformat(day).isoformat()!=day:
                    raise ValueError("Historical plan requires canonical ISO dates")
                for extension in (".json.gz",".receipt.json"):
                    known.add((league,split,day+extension))
        if (not plan[league]["train"] or not plan[league]["validation"]
                or len(set(per_split))!=len(per_split)
                or max(plan[league]["train"])>=min(plan[league]["validation"])):
            raise ValueError("Training and validation historical days overlap or misorder")
    files_root=base/ROOT/"sources"
    if files_root.exists():
        for item in files_root.rglob("*"):
            if not item.is_file():
                continue
            relative=item.relative_to(files_root).parts
            if len(relative)!=3 or tuple(relative) not in known:
                raise ValueError("Unknown or misplaced historical source archive file")
    # Full receipt verification before any outbound fetch or append-only writes
    for sport in ORDER:
        if set(plan[sport])!={"train","validation"}:
            raise ValueError("Historical split labels must remain separate")
        chosen=[]
        total=existing_count=0
        for split in ("train","validation"):
            for day in plan[sport][split]:
                if date.fromisoformat(day)>now.date():
                    raise ValueError("Historical source request is future-dated")
                total+=1
                if verify_existing(base,sport,split,day,as_of=now):
                    existing_count+=1
                elif len(chosen)<per_league:
                    chosen.append((sport,split,day))
        counts[sport]={"expected_dates":total,"retained_before":existing_count,
                       "selected_new":len(chosen)}
        new+=chosen
    prepared=[]
    for sport,split,day in new:
        url=observer.scoreboard_url(sport,day)
        raw=fetch(url)
        if not isinstance(raw,bytes) or not raw or len(raw)>8_000_000:
            raise ValueError("Historical provider source unavailable or oversized")
        parsed=observer.parse_scoreboard(json.loads(raw),sport)
        receipt={
            "schema":"college-nba-history-provider-day-v1",
            "league":sport,"split":split,"source_date":day,
            "source_url":url,
            "recorded_at_utc":now.astimezone(timezone.utc).isoformat(),
            "original_response_sha256":hashlib.sha256(raw).hexdigest(),
            "parsed_provider_scoreboard":parsed,
            "historical_results_are_not_pregame_forecasts":True,
            "independently_verified_official_scores":False,
            "NO_BET":True,"actual_wagers":0,"promotion_allowed":False,
        }
        prepared.append((sport,split,day,gzip.compress(raw,mtime=0),receipt))
    # No partial writes on invalid provider data or mismatched earlier receipts.
    for sport,split,day,blob,receipt in prepared:
        prefix=base/ROOT/"sources"/sport/split
        prefix.mkdir(parents=True,exist_ok=True)
        artifact=prefix/(day+".json.gz")
        saved=prefix/(day+".receipt.json")
        if artifact.exists() or saved.exists():
            raise ValueError("History source already exists (no overwrite allowed)")
        artifact.write_bytes(blob)
        saved.write_bytes(observer.canonical(receipt))
    output={
        "schema":"college-nba-time-split-historical-provider-source-v1",
        "as_of_utc":now.astimezone(timezone.utc).isoformat(),
        "training_start_season":2024,
        "validation_start_season":2025,
        "sport_day_status":{},
        "source_provider":"ESPN_MEDIA_DATA_NOT_INDEPENDENT_OFFICIAL",
        "training_allowed":False,
        "live_forecasts_allowed":False,
        "historical_backfilled_forecasts":0,
        "NO_BET":True,"actual_wagers":0,"promotion_allowed":False,
        "limitations":[
            "Requesting all calendar days does not prove the source returned every official event.",
            "Historical schedule and final records retrieved now are not immutable pregame forecasts.",
            "NBA, college FBS and men's D1 must use separate model weights and test cohorts.",
            "No future official game results may enter training or validation as a pregame feature.",
        ],
    }
    for sport in ORDER:
        previous=counts[sport]
        n=previous["retained_before"]+previous["selected_new"]
        output["sport_day_status"][sport]={
            "expected_source_dates":previous["expected_dates"],
            "archived_source_dates":n,
            "remaining_source_dates":previous["expected_dates"]-n,
            "all_declared_dates_retrieved":n==previous["expected_dates"],
            "official_result_completeness_verified":False,
        }
    dest=base/ROOT/"COVERAGE.latest.json"
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(observer.canonical(output))
    return output


def main():
    def fetch(url):
        r=requests.get(url,timeout=18,headers={
            "User-Agent":"TylerAI-Historical-Research-NoBets/1.0",
            "Accept":"application/json"})
        r.raise_for_status()
        return r.content
    result=capture(fetch)
    print(json.dumps({"as_of":result["as_of_utc"],
                      "status":result["sport_day_status"],
                      "train_enabled":False,"NO_BET":True},sort_keys=True))


if __name__=="__main__":
    main()
