"""Read-only ESPN provider-source archival for FBS, Division I men's hoops, NBA.

Phase 1 is *source evidence only*: ESPN alone is not an independently verified
official final. It does not issue forecasts, score bets or train any model.
New leagues must not inherit NFL/NHL/MLB weights or blend results.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests
import sports_source_collection_window as collection_window

ROOT = Path("benchmarks/college_nba_source_v1")
LIMIT = 500
LOOKBACK_RECONCILIATION_POLICY = 'STRICT_STAGE_VENUE_PROVIDER_NAMES_V1'
LEAGUES = {
    "NCAAF_FBS": {"path":"football/college-football", "group":"80",
                  "start":"2026-08-01", "end":"2027-01-31",
                  "scope":"FBS-associated ESPN scoreboard games; may include an FCS opponent"},
    "NCAAM_D1": {"path":"basketball/mens-college-basketball", "group":"50",
                 "start":"2026-10-30", "end":"2027-04-07",
                 "scope":"Division I-associated men's basketball games; not a certified census"},
    "NBA": {"path":"basketball/nba", "group":None,
            "start":"2026-10-17", "end":"2027-06-30",
            "scope":"NBA regular season and postseason; preseason is excluded"},
}


def canonical(data):
    return (json.dumps(data,sort_keys=True,separators=(",",":"),allow_nan=False)
            +"\n").encode("utf-8")


def utc(value):
    if not isinstance(value,str):
        raise ValueError("Expected ISO-8601 UTC timestamp")
    try:
        time=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:
        raise ValueError("Malformed source timestamp") from exc
    if time.tzinfo is None:
        raise ValueError("Timezone-free source timestamp")
    return time.astimezone(timezone.utc)


def scoreboard_url(league, day):
    if league not in LEAGUES:
        raise ValueError("Unsupported research league")
    d=date.fromisoformat(day)
    config=LEAGUES[league]
    args={"dates":d.strftime("%Y%m%d"),"limit":str(LIMIT)}
    if config["group"] is not None:
        args["groups"]=config["group"]
    return ("https://site.api.espn.com/apis/site/v2/sports/"
            +config["path"]+"/scoreboard?"+urlencode(args))


def _score(value):
    if isinstance(value,dict):
        value=value.get("value",value.get("displayValue"))
    if type(value) is int and value>=0:
        return value
    if isinstance(value,str) and value.isdigit():
        return int(value)
    raise ValueError("Source final requires an integer score")


def _event(event, payload):
    game_id=str(event["id"])
    if not game_id.isdigit():
        raise ValueError("Non-numeric provider game identity")
    season=event.get("season") or payload.get("season") or {}
    stage=season.get("type")
    if stage not in (2,3): # Never include NBA preseason or college exhibitions.
        return None,"not_confirmed_regular_or_postseason"
    competition=event["competitions"]
    if len(competition)!=1:
        raise ValueError("Expected one unique provider game competition")
    c=competition[0]
    sides={}
    for team in c["competitors"]:
        side=team.get("homeAway")
        if side not in ("home","away") or side in sides:
            raise ValueError("Ambiguous home/away identity")
        ident=str(team["team"]["id"])
        if not ident.isdigit():
            raise ValueError("Non-numeric team identity")
        sides[side]=team
    if set(sides)!=set(("home","away")):
        raise ValueError("Missing opponent")
    if sides["home"]["team"]["id"]==sides["away"]["team"]["id"]:
        raise ValueError("Identical competing teams")
    status=event["status"]["type"]
    state=status.get("state")
    if state not in ("pre","in","post"):
        raise ValueError("Unrecognized game state")
    completed=status.get("completed") is True and state=="post"
    if state=="post" and not completed:
        # ESPN may temporarily report post/incomplete; do not call final.
        state="in"
    start=utc(event["date"]).isoformat()
    scores={}
    if completed:
        scores={side:_score(sides[side].get("score")) for side in ("home","away")}
        if scores["home"]==scores["away"]:
            raise ValueError("Final team-winner source tied or incomplete")
    return {
        "game_id":game_id, "scheduled_start_utc":start,
        "home_team_id":str(sides["home"]["team"]["id"]),
        "away_team_id":str(sides["away"]["team"]["id"]),
        "home_name":sides["home"]["team"].get("displayName") or
                    sides["home"]["team"].get("name"),
        "away_name":sides["away"]["team"].get("displayName") or
                    sides["away"]["team"].get("name"),
        "season_stage":stage,"state":state,
        "provider_completed":completed,
        "home_score":scores.get("home"),
        "away_score":scores.get("away"),
        "provider_final_not_independent_official_verification":completed,
        "neutral_site":c.get("neutralSite"),
    },None


def parse_scoreboard(payload, league):
    if league not in LEAGUES or not isinstance(payload,dict):
        raise ValueError("Unsupported league or malformed scoreboard")
    events=payload.get("events")
    if not isinstance(events,list) or len(events)>=LIMIT:
        raise ValueError("Missing or potentially truncated source event slate")
    if (payload.get("count") is not None
            and (type(payload["count"]) is not int
                 or payload["count"]>len(events))):
        raise ValueError("Provider scoreboard count exceeds returned events")
    records=[];excluded=[];ids=set()
    for e in events:
        identifier=str(e.get("id"))
        if identifier in ids:
            raise ValueError("Repeated game ID in one source response")
        ids.add(identifier)
        row,why=_event(e,payload)
        if why:
            excluded.append({"game_id":identifier,"reason":why})
        else:
            records.append(row)
    return {"league":league,"total_source_events":len(events),
            "eligible_observed":len(records),"excluded":excluded,
            "games":records,"result_trust":"ESPN_PROVIDER_ONLY_UNVERIFIED_OFFICIAL"}


def reconcile(snapshots, *, strict_context=False):
    if type(strict_context) is not bool: raise ValueError('Explicit provider reconciliation mode required')
    """Never choose a different source day by preference or confidence."""
    seen=defaultdict(list)
    for snap in snapshots:
        for row in snap["parsed"]["games"]:
            seen[(snap["league"],row["game_id"])].append(
                {"source_day":snap["day"],"game":row})
    unique=[];disputed=[]
    for (league,game_id),entries in sorted(seen.items()):
        baseline=entries[0]["game"]
        keys=("scheduled_start_utc","home_team_id","away_team_id",
              "state","home_score","away_score","provider_completed")
        if strict_context: keys += ("season_stage","neutral_site","home_name","away_name")
        if any(any(entry["game"][key]!=baseline[key] for key in keys)
               for entry in entries[1:]):
            disputed.append({"league":league,"game_id":game_id,
                             "source_days":[e["source_day"] for e in entries],
                             "observed_game_rows":entries,
                             "action":"QUARANTINE_NOT_A_VERIFIED_RESULT"})
        else:
            unique.append({"league":league,**baseline})
    return unique,disputed


def reconcile_for_manifest(manifest, snapshots):
    if 'collection_window' in manifest:
        collection_window.verify(manifest['collection_window'],utc(manifest['recorded_at_utc']))
        if manifest.get('source_reconciliation_policy')!=LOOKBACK_RECONCILIATION_POLICY:
            raise ValueError('Unknown lookback source reconciliation policy')
        return reconcile(snapshots,strict_context=True)
    if 'source_reconciliation_policy' in manifest:
        raise ValueError('Unexpected context policy in legacy source capture')
    return reconcile(snapshots)


def capture(fetch, *, now=None, base=Path("."), days_ahead=3, days_back=0):
    now=now or datetime.now(timezone.utc)
    collection_window.bounds(days_ahead, days_back)
    if now.tzinfo is None:
        raise ValueError("UTC clock and bounded 0-7 day horizon required")
    base=Path(base)
    anchor=now.astimezone(timezone.utc).date() if days_back else now.date()
    # Only observed provider evidence, no original model scores/predictions.
    stamp=now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder=base/ROOT/"captures"/stamp
    snapshots=[]
    blobs={}
    for league,config in LEAGUES.items():
        for shift in range(-days_back,days_ahead+1):
            day=(anchor+timedelta(days=shift)).isoformat()
            if not config["start"]<=day<=config["end"]:
                continue
            url=scoreboard_url(league,day)
            raw=fetch(url)
            if not isinstance(raw,bytes) or len(raw)>8_000_000:
                raise ValueError("Invalid or oversized provider response")
            payload=json.loads(raw)
            parsed=parse_scoreboard(payload,league)
            filename=league+"_"+day+".json.gz"
            snapshots.append({
                "league":league,"day":day,"url":url,
                "original_response_sha256":hashlib.sha256(raw).hexdigest(),
                "compressed_file":filename,
                "retrieved_at_utc":now.astimezone(timezone.utc).isoformat(),
                "parsed":parsed})
            blobs[filename]=gzip.compress(raw,mtime=0)
    accepted,conflicts=reconcile(snapshots,strict_context=days_back>0)
    if folder.exists():
        raise ValueError("Capture timestamp collision: exclusive append-only snapshots")
    folder.mkdir(parents=True)
    for filename,blob in blobs.items():
        (folder/filename).write_bytes(blob)
    report={
        "schema":"tyler-college-nba-provider-observation-v1",
        "recorded_at_utc":now.astimezone(timezone.utc).isoformat(),
        "source_trust":"ESPN_ONLY_NOT_INDEPENDENT_OFFICIAL_VERIFICATION",
        "enabled_leagues":list(LEAGUES),
        "snapshots":snapshots,
        "undisputed_provider_games":accepted,
        "quarantined_provider_games":conflicts,
        "forecasting_enabled":False,
        "official_final_scoring_enabled":False,
        "model_training_enabled":False,
        "actual_wagers":0,
        "NO_BET":True,
        "promotion_allowed":False,
        "limitations":[
            "College scoreboard grouping may omit games; provider coverage is not certified complete.",
            "ESPN-reported final is a source observation, NOT independently verified NCAA/NBA final.",
            "No sportsbook odds, betting recommendations, frozen predictions, or results grading are produced.",
            "Regular/postseason labels come from provider season stage, not a governing-body roster audit.",
        ],
    }
    if days_back:
        report["collection_window"]=collection_window.policy(now, days_ahead, days_back)
        report["source_reconciliation_policy"]=LOOKBACK_RECONCILIATION_POLICY
    (folder/"manifest.json").write_bytes(canonical(report))
    return report


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days-ahead",type=int,default=3)
    parser.add_argument("--days-back",type=int,default=0)
    args=parser.parse_args()
    def fetch(url):
        reply=requests.get(url,timeout=20,headers={"User-Agent":"TylerAI-Research-Only/1.0"})
        reply.raise_for_status()
        return reply.content
    out=capture(fetch,days_ahead=args.days_ahead,days_back=args.days_back)
    print(json.dumps({"capture_at":out["recorded_at_utc"],
                      "snapshots":len(out["snapshots"]),
                      "observed_undisputed":len(out["undisputed_provider_games"]),
                      "quarantined":len(out["quarantined_provider_games"]),
                      "NO_BET":True},sort_keys=True))


if __name__=="__main__":
    main()
