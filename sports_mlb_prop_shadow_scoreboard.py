"""Read-only scoreboard for immutable MLB hitter conditional-prop shadow trials.

Never changes original forecasts or final settlement records. Explicitly
separates pending, ineligible, and scored observations and distinguishes
player-games from independent game events. No market pricing or wager claims.
"""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from sports_mlb_hit_prop_shadow import PRIORS
from sports_mlb_shadow_uncertainty import clustered_brier_difference
from sports_mlb_prop_prospective import _verify
from sports_mlb_sources import utc

DEFAULT_ROOT="benchmarks/mlb_hitter_props_shadow_v1"


def _report_metric(values):
    if not values:
        return {
            "eligible_player_games":0,"brier":None,"fixed_reference_brier":None,
            "log_loss":None,"fixed_reference_log_loss":None,
            "model_improved_over_fixed_reference":None,
            "predictive_edge_established":False,
        }
    n=len(values)
    kind=values[0]["event"]
    baseline=PRIORS[kind]
    def loss(p,y):
        return -y*math.log(max(p,1e-12))-(1-y)*math.log(max(1-p,1e-12))
    return {
        "eligible_player_games":n,
        "brier":round(sum((v["probability"]-v["outcome"])**2 for v in values)/n,6),
        "fixed_reference_brier":round(sum((baseline-v["outcome"])**2 for v in values)/n,6),
        "log_loss":round(sum(loss(v["probability"],v["outcome"]) for v in values)/n,6),
        "fixed_reference_log_loss":round(sum(loss(baseline,v["outcome"]) for v in values)/n,6),
        "model_improved_over_fixed_reference":None,
        "predictive_edge_established":False,
    }


def official_shadow_scoreboard(root=DEFAULT_ROOT):
    root=Path(root)
    pre=root/"predictions"
    results=root/"settlements"
    if not pre.exists():
        return {
            "status":"NO_FROZEN_PREDICTIONS",
            "frozen_player_game_forecasts":0,
            "distinct_official_game_ids":0,
            "pending":0,"ineligible":0,"scored":0,
            "metrics":{k:_report_metric([]) for k in PRIORS},
            "no_wagers":True,
        }
    frozen={}
    by_game={}
    if len(list(pre.glob("*.json")))>30000:
        raise ValueError("Unexpectedly many prediction files to audit.")
    for path in sorted(pre.glob("*.json")):
        record=json.loads(path.read_text(encoding="utf-8"))
        core=_verify(record)
        game=core.get("game_id")
        hitter=core.get("hitter_id")
        if (path.name!=str(game)+"_"+str(hitter)+".json" or
                core.get("status")!="IMMUTABLE_PREGAME_SHADOW_NO_BET" or
                core.get("actual_wager")!=0 or
                core.get("sportsbook_wager_eligible") is not False):
            raise ValueError("Unexpected immutable prediction identity or wagering content.")
        freeze=utc(core["frozen_at_utc"])
        event=utc(core["event_start_utc"])
        if freeze>=event:
            raise ValueError("Prediction was not frozen before scheduled first pitch.")
        key=(game,hitter)
        if key in frozen:
            raise ValueError("Duplicate frozen player-game prediction.")
        frozen[key]=record
        by_game.setdefault(game,{"predictions":0,"pending":0,"ineligible":0,"scored":0})
        by_game[game]["predictions"]+=1
    if results.exists() and len(list(results.glob("*.json")))>30000:
        raise ValueError("Unexpectedly many settlement files.")
    settled={}
    for path in sorted(results.glob("*.json")) if results.exists() else []:
        record=json.loads(path.read_text(encoding="utf-8"))
        core=_verify(record)
        key=(core.get("game_id"),core.get("hitter_id"))
        if (path.name!=str(key[0])+"_"+str(key[1])+".json" or
                core.get("schema")!="mlb_hit_prop_shadow_settlement_v1" or
                core.get("actual_wager")!=0):
            raise ValueError("Unrecognized sealed shadow settlement record.")
        if key not in frozen or key in settled:
            raise ValueError("Orphan or duplicate final result for MLB player-game.")
        if core.get("prediction_digest_sha256")!=frozen[key]["record_digest_sha256"]:
            raise ValueError("Final settlement does not refer to original frozen forecast digest.")
        if utc(core["settled_at_utc"])<=utc(frozen[key]["event_start_utc"]):
            raise ValueError("Final settlement timestamp is not after scheduled game time.")
        settled[key]=record
    pending=0
    eligible=0
    ineligible=0
    outcomes={"hit":[],"hr":[]}
    for key,forecast in frozen.items():
        game=key[0]
        result=settled.get(key)
        if result is None:
            pending+=1
            by_game[game]["pending"]+=1
            continue
        if result["status"] in ("INELIGIBLE_ZERO_AB","INELIGIBLE_NOT_IN_FINAL_BOXSCORE"):
            ineligible+=1
            by_game[game]["ineligible"]+=1
            if result["conditional_binary_scoring"] is not None:
                raise ValueError("Ineligible game must not count as scored loss.")
            continue
        if result["status"]!="SETTLED_CONDITIONAL":
            raise ValueError("Unknown conditional settlement status.")
        scores=result.get("conditional_binary_scoring")
        if not isinstance(scores,dict) or set(scores)!={"hit","hr"}:
            raise ValueError("Incomplete official conditional hit/HR outcomes.")
        eligible+=1
        by_game[game]["scored"]+=1
        for kind in ("hit","hr"):
            label=scores[kind]["observed_binary_event"]
            p=scores[kind]["frozen_probability"]
            expected_p=forecast["conditional_at_bat_probabilities"][kind]
            if isinstance(label,bool) or label not in (0,1) or p!=expected_p:
                raise ValueError("Result label or probability conflicts with original freeze.")
            if abs(scores[kind]["brier_error"]-(p-label)**2)>1e-7:
                raise ValueError("Recorded Brier loss does not match frozen event forecast.")
            outcomes[kind].append({"event":kind,"game_id":game,"probability":p,"outcome":label})
    metrics={kind:_report_metric(outcomes[kind]) for kind in outcomes}
    for kind in metrics:
        item=metrics[kind]
        if item["eligible_player_games"]>0:
            item["model_improved_over_fixed_reference"]=item["brier"]<item["fixed_reference_brier"]
        item["game_cluster_uncertainty"]=clustered_brier_difference(
            outcomes[kind],reference_probability=PRIORS[kind])
    return {
        "status":"PROSPECTIVE_FREEZE_SCORING_DIAGNOSTIC_NO_BET",
        "report_created_utc":datetime.now(timezone.utc).isoformat(),
        "frozen_player_game_forecasts":len(frozen),
        "distinct_official_game_ids":len(by_game),
        "distinct_official_game_ids_with_eligible_settlements":sum(g["scored"]>0 for g in by_game.values()),
        "pending":pending,"ineligible":ineligible,"scored":eligible,
        "per_game":{str(k):v for k,v in sorted(by_game.items())},
        "metrics":metrics,
        "model_is_calibrated":False,
        "market_odds_available":False,
        "independent_github_commit_time_attestation_included":False,
        "proven_betting_edge":False,
        "no_wagers":True,
        "limitations":[
            "A sealed content digest is not independently verified publication time: check GitHub server commit timestamps for genuine prospective evidence.",
            "Player-game outcomes from the same MLB game share conditions and cannot be treated as independent games.",
            "Scores apply only when official at-bats are positive; actual bookmaker prop void rules are not represented.",
            "Current model is a fixed conditional baseline, not validated or compared with any real sportsbook odds.",
            "A small score advantage over exploratory priors does not prove significant calibration or profitability.",
            "Game-cluster uncertainty intervals require 30 distinct final MLB games and 150 eligible player-games per prop event.",
        ],
    }


def main():
    ap=argparse.ArgumentParser(description="Read-only MLB player-game shadow benchmark scoreboard")
    ap.add_argument("--root",default=DEFAULT_ROOT)
    args=ap.parse_args()
    print(json.dumps(official_shadow_scoreboard(args.root),indent=2,allow_nan=False))


if __name__=="__main__":
    main()
