"""Manual read-only, no-bet MLB hitter 1+ hit/HR retrospective diagnostic.

Uses official present-day gameLog data and intentionally does NOT call this
prospective validation. No odds, placement, stake, or skill promotion.
"""
import argparse
import json
from sports_mlb_hit_prop_shadow import (
    retrieve_game_logs, retrospective_walk_forward, conditional_shadow_forecast
)


def main():
    parser=argparse.ArgumentParser(description="Official MLB hitter frequency shadow, NO BET")
    parser.add_argument("--hitter-id",type=int,required=True)
    parser.add_argument("--season",type=int,required=True,
                        help="Current season for diagnostic evaluation")
    parser.add_argument("--event-start",type=str,required=True,
                        help="Future official event start in timezone-aware ISO8601")
    args=parser.parse_args()
    rows, receipts=retrieve_game_logs(args.hitter_id,[args.season-1,args.season])
    historical=retrospective_walk_forward(rows,evaluation_season=args.season)
    future=conditional_shadow_forecast(rows,args.event_start)
    report={
        "hitter_id":args.hitter_id,"model":future["model"],
        "retrieved_official_sources":receipts,
        "current_shadow_conditional_estimate":future,
        "retrospective_date_block_diagnostic":historical,
        "betting_recommendation":"NONE - NO BET",
        "calibration_claim":False,"proven_edge":False,
        "wager_execution":False,
    }
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
