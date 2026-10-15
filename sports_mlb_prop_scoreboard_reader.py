"""Fetch Tyler's public GitHub-hosted, scheduled MLB shadow scoreboard snapshot.

Fixed HTTPS URL, bounded response, integrity hash, as-of age and structural
validation. A scheduled snapshot is not live MLB final data or betting advice.
"""
import hashlib
import json
from datetime import datetime, timezone

import requests

from sports_mlb_prop_scoreboard_feed import _canonical, FEED_SCHEMA
from sports_mlb_sources import utc

FEED_URL=("https://raw.githubusercontent.com/tylerstong66/Tyler-ai/main/"
          "benchmarks/mlb_hitter_props_shadow_v1/scoreboard.latest.json")


def load_published_shadow_scoreboard(*, get=None, clock=None):
    get=get or requests.get
    clock=clock or (lambda:datetime.now(timezone.utc))
    response=get(FEED_URL,timeout=12,allow_redirects=False,
                 headers={"User-Agent":"TylerAI-MLB-Shadow-Scoreboard-ReadOnly/1.0"})
    if response.status_code!=200 or len(response.content)>1_000_000:
        raise RuntimeError("Published GitHub MLB scoreboard unavailable or too large.")
    address=getattr(response,"url",FEED_URL)
    if address!=FEED_URL:
        raise ValueError("Public scoreboard response came from unexpected URL.")
    payload=response.json()
    if not isinstance(payload,dict) or payload.get("schema")!=FEED_SCHEMA:
        raise ValueError("Unrecognized published MLB scoreboard feed.")
    report=payload.get("benchmark")
    if not isinstance(report,dict):
        raise ValueError("Published scoreboard missing benchmark.")
    digest=payload.get("benchmark_sha256")
    actual=hashlib.sha256(_canonical(report).encode("utf-8")).hexdigest()
    if digest!=actual:
        raise ValueError("Published scoreboard content hash does not match.")
    if payload.get("no_wagers") is not True or report.get("no_wagers") is not True:
        raise ValueError("Published scoreboard must be explicitly no-wager.")
    for flag in ("proven_betting_edge","model_is_calibrated","market_odds_available"):
        if report.get(flag) is True:
            raise ValueError("Unsupported prediction or sports-market claims.")
    count=report.get("frozen_player_game_forecasts")
    pending=report.get("pending")
    scored=report.get("scored")
    ineligible=report.get("ineligible")
    distinct=report.get("distinct_official_game_ids")
    for num in (count,pending,scored,ineligible,distinct):
        if isinstance(num,bool) or not isinstance(num,int) or num<0:
            raise ValueError("Published scoreboard has invalid outcome counts.")
    if count!=pending+scored+ineligible or distinct>count:
        raise ValueError("Published scoreboard counts are inconsistent.")
    published=utc(payload.get("published_at_utc"))
    age=(utc(clock())-published).total_seconds()
    if age< -120:
        raise ValueError("Published scoreboard timestamp is unexpectedly in the future.")
    if payload.get("source")!="public_github_main_scheduled_snapshot":
        raise ValueError("Published scoreboard is not the expected source.")
    return {
        "source":FEED_URL,"published_at_utc":published.isoformat(),
        "snapshot_age_hours":round(max(age,0)/3600,2),
        "may_be_stale":age>4*3600,
        "last_source_commit":payload.get("source_git_revision"),
        "frozen_player_game_forecasts":count,
        "distinct_official_games":distinct,
        "pending":pending,"scored":scored,"ineligible":ineligible,
        "metrics":report.get("metrics"),
        "per_game":report.get("per_game"),
        "no_wagers":True,
        "proven_betting_edge":False,
        "probabilities_condition":"at_least_one_official_at_bat",
        "limitations":payload.get("limitations",[]),
    }
