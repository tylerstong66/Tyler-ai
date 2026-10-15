"""Bounded, deterministic MLB pregame shadow batch capture (NO BET).

Selects official active-roster nonpitchers by fixed numeric ID order, without
using market prices or future outcomes. Historical hit/HR estimates remain
experimental and conditional on 1+ official AB. Files use exclusive creation
and never replace an earlier signed prediction.
"""
import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sports_mlb_sources import OfficialMlbReader, _roster_people, positive_id, utc
from sports_mlb_prop_prospective import (
    _verify, freeze_pregame_hit_props, write_exclusive_json
)

EASTERN=ZoneInfo("America/New_York")
DEFAULT_ROOT="benchmarks/mlb_hitter_props_shadow_v1"


def capture_current_day(date_string=None, *, reader=None, root=DEFAULT_ROOT,
                        per_side=3, max_games=20):
    if isinstance(per_side,bool) or not isinstance(per_side,int) or not 1<=per_side<=4:
        raise ValueError("Select between one and four active-roster hitters per team.")
    if isinstance(max_games,bool) or not isinstance(max_games,int) or not 1<=max_games<=20:
        raise ValueError("Bound the official schedule to 1-20 games.")
    reader=reader or OfficialMlbReader()
    start_run=utc(reader.clock())
    local_day=start_run.astimezone(EASTERN).date()
    if date_string is None:
        day=local_day
    else:
        if not isinstance(date_string,str):
            raise ValueError("Date must be an Eastern YYYY-MM-DD string.")
        try:
            day=date.fromisoformat(date_string)
        except ValueError:
            raise ValueError("Invalid Eastern YYYY-MM-DD date.") from None
        if day.isoformat()!=date_string or day!=local_day:
            raise ValueError("Automated capture only supports the current Eastern calendar day.")
    schedule,receipt=reader.load("schedule",{
        "sportId":1,"startDate":day.isoformat(),"endDate":day.isoformat(),
        "gameTypes":"R,F,D,L,W"})
    dates=schedule.get("dates",[])
    if not isinstance(dates,list):
        raise ValueError("Official schedule dates missing.")
    entries=[game for node in dates for game in node.get("games",[])]
    if len(entries)>max_games:
        raise ValueError("Too many official MLB games; refusing incomplete batch.")
    indexed=set()
    games=[]
    for g in entries:
        pk=positive_id(g.get("gamePk"),"official schedule gamePk")
        if pk in indexed:
            raise ValueError("Duplicate scheduled MLB game ID.")
        indexed.add(pk)
        games.append((utc(g.get("gameDate")),pk,g))
    games.sort(key=lambda row:(row[0],row[1]))
    root=Path(root)
    records=[]
    existing=0
    skipped=[]
    for start,pk,event in games:
        # Do not initiate high-latency player captures close to first pitch.
        if start-utc(reader.clock())<=timedelta(minutes=45):
            skipped.append({"game_id":pk,"reason":"under_45_minutes_until_first_pitch"})
            continue
        status=event.get("status",{})
        if (status.get("abstractGameState")!="Preview" or
                status.get("detailedState") not in ("Scheduled","Pre-Game")):
            skipped.append({"game_id":pk,"reason":"not_officially_pregame"})
            continue
        game,_=reader.load("game/"+str(pk)+"/feed/live",api_version="v1.1")
        gd=game.get("gameData",{})
        if (game.get("gamePk")!=pk or utc(gd.get("datetime",{}).get("dateTime"))!=start
                or gd.get("status",{}).get("abstractGameState")!="Preview"):
            raise ValueError("Official schedule and detailed game identity/time mismatch.")
        teams=gd.get("teams",{})
        if (not isinstance(teams.get("home",{}).get("id"),int) or
                not isinstance(teams.get("away",{}).get("id"),int) or
                teams["home"]["id"]==teams["away"]["id"]):
            raise ValueError("MLB game does not have two verified teams.")
        for side in ("home","away"):
            team_id=positive_id(teams[side]["id"],"team_id")
            roster,_=reader.load("teams/"+str(team_id)+"/roster",{
                "rosterType":"active","date":day.isoformat()})
            hitters=sorted(
                (p for p in _roster_people(roster).values() if p["position"]!="P"),
                key=lambda player:player["id"])[:per_side]
            if not hitters:
                skipped.append({"game_id":pk,"team_id":team_id,"reason":"no_active_nonpitchers"})
            for hitter in hitters:
                player=hitter["id"]
                path=root/"predictions"/(str(pk)+"_"+str(player)+".json")
                if path.exists():
                    prior=json.loads(path.read_text(encoding="utf-8"))
                    _verify(prior)
                    if prior.get("game_id")!=pk or prior.get("hitter_id")!=player:
                        raise ValueError("Existing immutable forecast file identity conflict.")
                    existing+=1
                    continue
                try:
                    frozen=freeze_pregame_hit_props(pk,player,side,reader=reader)
                except ValueError as error:
                    skipped.append({"game_id":pk,"hitter_id":player,
                                    "reason":"ineligible_or_unverified",
                                    "detail":str(error)[:160]})
                    continue
                if utc(reader.clock())>=utc(frozen["event_start_utc"]):
                    raise ValueError("Predictions cannot be created after a game has begun.")
                write_exclusive_json(path,frozen)
                records.append({
                    "game_id":pk,"hitter_id":player,"hitter_name":hitter["name"],
                    "path":str(path),"frozen_at_utc":frozen["frozen_at_utc"],
                    "scheduled_first_pitch_utc":frozen["event_start_utc"],
                    "digest":frozen["record_digest_sha256"]})
    return {
        "status":"MLB_CONDITIONAL_HITTER_SHADOW_BATCH_NO_BET",
        "current_eastern_date":day.isoformat(),
        "run_started_utc":start_run.isoformat(),
        "schedule_source":receipt,
        "scheduled_games":len(games),
        "new_frozen_predictions":len(records),
        "already_existing_predictions":existing,
        "records":records,"skipped":skipped,
        "wagers":0,
        "source_population":"fixed_numeric_id_active_roster_not_confirmed_lineup",
        "proven_edge":False,
    }


def ensure_publishable_before_events(records, *, now=None, safety_seconds=120):
    """Fail if any staged prediction is too near or after scheduled first pitch."""
    stamp=utc(now if now is not None else datetime.now(timezone.utc))
    if not isinstance(records,list):
        raise ValueError("Expect a list of prospective predictions.")
    for row in records:
        obj=json.loads(Path(row["path"]).read_text(encoding="utf-8"))
        _verify(obj)
        if obj.get("actual_wager")!=0 or obj.get("sportsbook_wager_eligible") is not False:
            raise ValueError("No-wager research records only.")
        if stamp+timedelta(seconds=safety_seconds)>=utc(obj["event_start_utc"]):
            raise ValueError("Too close to scheduled first pitch for reliable publication.")
    return True


def main():
    p=argparse.ArgumentParser(description="Freeze MLB game-day shadow props from public source")
    p.add_argument("--root",default=DEFAULT_ROOT)
    p.add_argument("--per-side",type=int,default=3)
    p.add_argument("--date",default=None)
    args=p.parse_args()
    report=capture_current_day(args.date,root=args.root,per_side=args.per_side)
    ensure_publishable_before_events(report["records"])
    print("MLB_BATCH_CAPTURE_REPORT="+json.dumps(report,sort_keys=True))


if __name__=="__main__":
    main()
