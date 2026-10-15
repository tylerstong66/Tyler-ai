"""Reproducible public MLB retrospective cohort audit from one game's rosters.

Chooses the lowest numeric official hitter IDs per side *before* reading their
historical outcomes. This convenience cohort is not a random MLB sample and
does not establish prospective betting value.
"""
import argparse
import json
from zoneinfo import ZoneInfo

from sports_mlb_sources import OfficialMlbReader, _roster_people, positive_id, utc
from sports_mlb_hit_prop_shadow import retrieve_game_logs
from sports_mlb_prop_cohort import summarize_hitter_cohort

EASTERN=ZoneInfo("America/New_York")


def roster_review(game_id, year, *, reader=None, hitters_per_team=5):
    game_id=positive_id(game_id,"game_id")
    if isinstance(year,bool) or not isinstance(year,int) or not 2000<=year<=2100:
        raise ValueError("Invalid season year.")
    if isinstance(hitters_per_team,bool) or not isinstance(hitters_per_team,int) or not 1<=hitters_per_team<=8:
        raise ValueError("Hitters per team must be between 1 and 8.")
    reader=reader or OfficialMlbReader()
    data,feed_source=reader.load("game/"+str(game_id)+"/feed/live",api_version="v1.1")
    gd=data.get("gameData",{})
    if (data.get("gamePk")!=game_id or gd.get("status",{}).get("abstractGameState")!="Preview"):
        raise ValueError("Cohort game is not currently verified as upcoming MLB pregame.")
    start=utc(gd.get("datetime",{}).get("dateTime"))
    if utc(reader.clock())>=start:
        raise ValueError("Cohort selection must occur before scheduled first pitch.")
    if start.year!=year:
        raise ValueError("Event and evaluation season disagree.")
    target_date=start.astimezone(EASTERN).date().isoformat()
    picked=[]
    roster_sources=[]
    for side in ("home","away"):
        team=gd.get("teams",{}).get(side,{})
        tid=positive_id(team.get("id"),side+"_team_id")
        raw,src=reader.load("teams/"+str(tid)+"/roster",{
            "rosterType":"active","date":target_date})
        roster_sources.append(src)
        people=_roster_people(raw)
        selected=sorted((p for p in people.values() if p["position"]!="P"),
                        key=lambda p:p["id"])[:hitters_per_team]
        if not selected:
            raise ValueError("Official active roster has no eligible hitters on "+side+".")
        for hitter in selected:
            rows,receipts=retrieve_game_logs(hitter["id"],[year-1,year],reader=reader)
            picked.append({"hitter_id":hitter["id"],"hitter_name":hitter["name"],
                           "game_logs":rows,"team_id":tid,"selection_side":side,
                           "receipt_count":len(receipts)})
    report=summarize_hitter_cohort(picked,season=year)
    report["roster_selection"]={
        "game_id":game_id,"game_start":start.isoformat(),
        "hitter_selection_rule":"lowest_official_numeric_player_ids_per_side",
        "requested_hitters_per_side":hitters_per_team,
        "game_source":feed_source,"roster_sources":roster_sources,
        "population":"Players on current active rosters, not a random historical population",
    }
    report["selected_players"]=[{
        "hitter_id":p["hitter_id"],"name":p["hitter_name"],"team_id":p["team_id"],
        "side":p["selection_side"],"fetched_game_rows":len(p["game_logs"])}
        for p in picked]
    report["warnings"]=[
        "Historical outcomes were downloaded after the fact; this is NOT a frozen prospective betting benchmark.",
        "Current postseason roster membership may select healthier/surviving players; observed sample is biased.",
        "Conditional hit and HR events require at least one at-bat; no real betting market odds were observed.",
        "Reference prior comparison is not a statistically established predictive edge.",
    ]
    return report


def main():
    parser=argparse.ArgumentParser(description="Read-only retrospective MLB cohort")
    parser.add_argument("--game-id",type=int,required=True)
    parser.add_argument("--season",type=int,required=True)
    parser.add_argument("--per-side",type=int,default=5)
    a=parser.parse_args()
    result=roster_review(a.game_id,a.season,hitters_per_team=a.per_side)
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
