"""Read-only NCAA-owned GraphQL scoreboard evidence for FBS and D1 men's hoops.

Independent NCAA source uses the published 2026 persisted scoreboard query.
Candidate FBS weeks deliberately do NOT claim complete schedule coverage.
No automatic ESPN identity joining, outcome grading, model training or bets.
"""
import gzip
import hashlib
import json
from collections import defaultdict
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlencode

import requests
import sports_expansion_observer as existing

ROOT=existing.ROOT/"ncaa_official"
ENDPOINT="https://sdataprod.ncaa.com/"
SCOREBOARD_QUERY_HASH="7287cda610a9326931931080cb3a604828febe6fe3c9016a7e4a36db99efdb7c"
MAX_BYTES=6_000_000

SPORTS={
    "NCAAF_FBS":{"code":"MFB","division":11},
    "NCAAM_D1":{"code":"MBB","division":1},
}


def graph_url(sport,*,year,week=None,day=None):
    if sport not in SPORTS or type(year) is not int or not 2024<=year<=2027:
        raise ValueError("Unsupported NCAA sport or season year")
    if (week is None)==(day is None):
        raise ValueError("Choose a NCAA football week or a basketball date")
    config=SPORTS[sport]
    params={"sportCode":config["code"],"division":config["division"],
            "seasonYear":year}
    if week is not None:
        if sport!="NCAAF_FBS" or type(week) is not int or not 1<=week<=21:
            raise ValueError("Unsupported NCAA football week")
        params["week"]=week
    else:
        if sport!="NCAAM_D1":
            raise ValueError("Football NCAA source uses week numbers")
        d=date.fromisoformat(day)
        if d.year not in (year,year+1):
            raise ValueError("NCAA basketball season date mismatch")
        params["contestDate"]=d.strftime("%Y/%m/%d")
    return ENDPOINT+"?"+urlencode({
        "extensions":json.dumps(
            {"persistedQuery":{"version":1,"sha256Hash":SCOREBOARD_QUERY_HASH}},
            separators=(",",":")),
        "variables":json.dumps(params,separators=(",",":")),
    })


class TiedNcaaFinalError(ValueError):
    """The original source claims a final with equal scores; never a result."""


def _positive_id(value,label):
    s=str(value)
    if not s.isdigit() or int(s)<=0:
        raise ValueError("Invalid NCAA "+label)
    return s


def official_scoreboard(raw,sport):
    if sport not in SPORTS:
        raise ValueError("Unknown NCAA league")
    payload=json.loads(raw)
    if payload.get("errors"):
        raise ValueError("NCAA official GraphQL errors are not empty fixtures")
    data=payload.get("data")
    contests=data.get("contests") if isinstance(data,dict) else None
    if not isinstance(contests,list) or len(contests)>=1000:
        raise ValueError("Missing or potentially truncated NCAA scoreboard")
    games=[]
    seen=set()
    for item in contests:
        identifier=_positive_id(item.get("contestId"),"contest ID")
        if identifier in seen:
            raise ValueError("Repeated NCAA contest identity")
        seen.add(identifier)
        competitors=item["teams"]
        if not isinstance(competitors,list) or len(competitors)!=2:
            raise ValueError("NCAA game does not contain exactly two opponents")
        sides={}
        for team in competitors:
            if type(team.get("isHome")) is not bool:
                raise ValueError("Missing NCAA home/away identity")
            name=team.get("nameShort")
            if not isinstance(name,str) or not name.strip():
                raise ValueError("Missing NCAA team name")
            side="home" if team["isHome"] else "away"
            if side in sides:
                raise ValueError("NCAA game has repeated home/away side")
            sides[side]=team
        if set(sides)!={"home","away"} or sides["home"]["nameShort"]==sides["away"]["nameShort"]:
            raise ValueError("Ambiguous NCAA opponent identities")
        state=item.get("gameState")
        if state not in ("F","P","I"):
            raise ValueError("Unrecognized NCAA source game state")
        scores={}
        if state=="F":
            for side,team in sides.items():
                value=team.get("score")
                if type(value) is int and value>=0:
                    scores[side]=value
                elif isinstance(value,str) and value.isdigit():
                    scores[side]=int(value)
                else:
                    raise ValueError("Incomplete final NCAA source score")
            if scores["home"]==scores["away"]:
                raise TiedNcaaFinalError("NCAA final scoreboard cannot imply a tied winner")
        games.append({
            "ncaa_game_id":identifier,
            "home_name":sides["home"]["nameShort"],
            "away_name":sides["away"]["nameShort"],
            "source_start_date":item.get("startDate"),
            "source_start_time_epoch":item.get("startTimeEpoch"),
            "source_state":state,
            "ncaa_home_score":scores.get("home"),
            "ncaa_away_score":scores.get("away"),
            "provider_reported_final":state=="F",
            "final_result_scoring_authorized":False,
        })
    return games


def requested_windows(today,days_ahead=3):
    if not 0<=days_ahead<=7:
        raise ValueError("Source horizon exceeds one week")
    requested=[]
    if date(2026,8,1)<=today<=date(2027,1,31):
        # Conservative estimated adjacent football week candidates from the
        # 2026 late-August week 0; NOT a complete governing-body week index.
        midpoint=max(1,1+((today-date(2026,8,29)).days//7))
        for week in range(max(1,midpoint-2),min(21,midpoint+2)+1):
            requested.append(("NCAAF_FBS",f"week-{week:02d}",
                              graph_url("NCAAF_FBS",year=2026,week=week)))
    for shift in range(days_ahead+1):
        day=today+timedelta(days=shift)
        if date(2026,10,30)<=day<=date(2027,4,7):
            requested.append(("NCAAM_D1",day.isoformat(),
                              graph_url("NCAAM_D1",year=2026,day=day.isoformat())))
    return requested


def run(fetch,*,base=Path("."),now=None,days_ahead=3):
    base=Path(base)
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Aware observation time required")
    windows=requested_windows(now.date(),days_ahead)
    if not windows:
        raise ValueError("Outside all NCAA seasonal query windows")
    snapshots=[]
    blobs={}
    same_game=defaultdict(list)
    for league,window,url in windows:
        raw=fetch(url)
        if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:
            raise ValueError("NCAA official response unavailable or oversized")
        games=official_scoreboard(raw,league)
        name=league+"_"+window+".json.gz"
        blobs[name]=gzip.compress(raw,mtime=0)
        snapshots.append({
            "league":league,"window":window,"source_url":url,
            "source_sha256":hashlib.sha256(raw).hexdigest(),
            "source_file":name,"observed_games":len(games),
            "observed_finals_not_yet_grading_authorized":sum(
                x["provider_reported_final"] for x in games),
        })
        for game in games:
            same_game[(league,game["ncaa_game_id"])].append({
                "window":window,"game":game})
    unambiguous=[]
    quarantined=[]
    for (sport,identifier),entries in sorted(same_game.items()):
        source=entries[0]["game"]
        if any(entry["game"]!=source for entry in entries[1:]):
            quarantined.append({
                "league":sport,"ncaa_game_id":identifier,
                "source_observations":entries,
                "reason":"DIFFERING_OFFICIAL_NCAA_SOURCE_WINDOWS_NO_GRADE"})
        else:
            unambiguous.append({"league":sport,**source})
    stamp=now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    dest=base/ROOT/"captures"/stamp
    if dest.exists():
        raise ValueError("Immutable NCAA capture timestamp collision")
    report={
        "schema":"ncaa-owned-2026-source-observations-v1",
        "recorded_at_utc":now.astimezone(timezone.utc).isoformat(),
        "source":"sdataprod.ncaa.com NCAA GraphQL persisted source query",
        "source_query_hash":SCOREBOARD_QUERY_HASH,
        "snapshots":snapshots,
        "unambiguous_ncaa_contests":unambiguous,
        "quarantined_ncaa_contests":quarantined,
        "college_to_espn_identity_map_verified":False,
        "fbs_source_week_completeness_verified":False,
        "official_final_scoring_enabled":False,
        "forecasting_enabled":False,"model_training_enabled":False,
        "NO_BET":True,"actual_wagers":0,"promotion_allowed":False,
    }
    dest.mkdir(parents=True)
    for name,blob in blobs.items():
        (dest/name).write_bytes(blob)
    (dest/"manifest.json").write_bytes(existing.canonical(report))
    return report


def main():
    def fetch(url):
        response=requests.get(url,timeout=17,headers={
            "Accept":"application/json",
            "User-Agent":"TylerAI-CollegeResearch/1.0"})
        response.raise_for_status()
        return response.content
    report=run(fetch)
    print(json.dumps({
        "captured":len(report["snapshots"]),
        "games":len(report["unambiguous_ncaa_contests"]),
        "quarantined":len(report["quarantined_ncaa_contests"]),
        "NO_BET":True,
    },sort_keys=True))


if __name__=="__main__":
    main()
