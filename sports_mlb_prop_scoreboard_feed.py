"""Publish a compact read-only snapshot of the frozen MLB hitter shadow ledger.

Only scoreboard.latest.json is overwritten; immutable predictions and separate
official settlements are never modified. This snapshot is NOT guaranteed
instantaneous: GitHub Actions cron may be delayed.
"""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from sports_mlb_prop_shadow_scoreboard import official_shadow_scoreboard
from sports_mlb_sources import utc

FEED_SCHEMA="tyler_mlb_shadow_public_scoreboard_v1"
FEED_RELATIVE="benchmarks/mlb_hitter_props_shadow_v1/scoreboard.latest.json"


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)


def publish_readonly_shadow_feed(root="benchmarks/mlb_hitter_props_shadow_v1",
                                  *, repository=".", now=None):
    current=utc(now if now is not None else datetime.now(timezone.utc))
    report=official_shadow_scoreboard(root=root)
    if report.get("no_wagers") is not True or report.get("frozen_player_game_forecasts",0)<0:
        raise ValueError("Only read-only no-wager official shadow reports may be published.")
    stable={k:v for k,v in report.items() if k!="report_created_utc"}
    digest=hashlib.sha256(_canonical(stable).encode("utf-8")).hexdigest()
    target=Path(repository)/FEED_RELATIVE
    if target.exists():
        prior=json.loads(target.read_text(encoding="utf-8"))
        if prior.get("schema")!=FEED_SCHEMA:
            raise ValueError("Existing public scoreboard feed has unknown schema.")
        if prior.get("benchmark_sha256")==digest and prior.get("benchmark")==stable:
            return {
                "status":"UNCHANGED","destination":FEED_RELATIVE,
                "forecast_count":stable.get("frozen_player_game_forecasts"),
                "benchmark_sha256":digest,"wagers":0
            }
        if utc(prior.get("published_at_utc"))>current:
            raise ValueError("Existing published scoreboard timestamp is in the future.")
    git_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repository,
                                     stderr=subprocess.PIPE).decode().strip()
    if len(git_head)!=40 or any(ch not in "0123456789abcdef" for ch in git_head):
        raise ValueError("Cannot verify publication input Git commit.")
    snapshot={
        "schema":FEED_SCHEMA,"published_at_utc":current.isoformat(),
        "source_git_revision":git_head,
        "source":"public_github_main_scheduled_snapshot",
        "source_is_not_live_official_MLB_api":True,
        "benchmark_sha256":digest,
        "benchmark":stable,
        "no_wagers":True,
        "limitations":[
            "The feed reports only the GitHub repository snapshot as of its publication time.",
            "GitHub scheduled jobs may run late, so actual final results may appear later.",
            "It is NOT a live sportsbook feed or a validated profitable betting model.",
            "Probability scoring is conditional on at least one official at-bat.",
            "Git commit metadata is not independent proof of publication timestamp."
        ]
    }
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(snapshot,sort_keys=True,indent=2,allow_nan=False)+"\n",
                      encoding="utf-8")
    return {
        "status":"CREATED_OR_UPDATED","destination":FEED_RELATIVE,
        "forecast_count":stable.get("frozen_player_game_forecasts"),
        "benchmark_sha256":digest,"wagers":0
    }


def main():
    parser=argparse.ArgumentParser(description="Publish read-only MLB shadow scoreboard snapshot")
    parser.add_argument("--repo",default=".")
    parser.add_argument("--root",default="benchmarks/mlb_hitter_props_shadow_v1")
    args=parser.parse_args()
    print("MLB_SHADOW_FEED_PUBLICATION="+json.dumps(
        publish_readonly_shadow_feed(root=args.root,repository=args.repo),
        sort_keys=True,allow_nan=False))


if __name__=="__main__":
    main()
