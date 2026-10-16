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


def _pending_time_audit(examples, total_pending, as_of):
    """Clock-relative timing of DISPLAYED saved player-games, not live MLB status.

    No network lookups, no presumed final outcomes and no retroactive grading.
    When a public feed is capped at 25, don't infer timings for hidden records.
    """
    if examples is None:
        return {
            "available":False,"as_of_utc":as_of.isoformat(),
            "shown":0,"unshown_pending":total_pending,
            "scheduled_first_pitch_future":None,
            "scheduled_first_pitch_reached":None,
            "events":[],"official_game_state_verified":False,
        }
    timed=[]
    future=reached=0
    for entry in examples:
        first_pitch=utc(entry["scheduled_first_pitch_utc"])
        status=("SAVED_FIRST_PITCH_FUTURE" if first_pitch>as_of
                else "SAVED_FIRST_PITCH_REACHED_UNSETTLED")
        future+=int(first_pitch>as_of)
        reached+=int(first_pitch<=as_of)
        timed.append({
            "game_id":str(entry["game_id"]),
            "hitter_id":str(entry["hitter_id"]),
            "hitter_name":entry.get("hitter_name"),
            "saved_first_pitch_utc":first_pitch.isoformat(),
            "time_state":status,
            "no_verified_player_outcome":True,
        })
    return {
        "available":True,"as_of_utc":as_of.isoformat(),
        "shown":len(timed),"unshown_pending":total_pending-len(timed),
        "scheduled_first_pitch_future":future,
        "scheduled_first_pitch_reached":reached,
        "events":timed,
        "official_game_state_verified":False,
        "limitation":("This compares the original saved first-pitch time with the reader clock. "
                      "It neither verifies actual start/final status nor assigns a player outcome."),
    }


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
    examples=report.get("pending_player_game_examples")
    truncated=report.get("pending_examples_truncated")
    if examples is not None:
        if (not isinstance(examples,list) or len(examples)>25
                or len(examples)>pending or type(truncated) is not bool
                or truncated!=(pending>len(examples))):
            raise ValueError("Published pending hitter audit count is inconsistent.")
        seen=set()
        for item in examples:
            if (not isinstance(item,dict)
                    or item.get("status")!="NO_SEALED_OFFICIAL_SETTLEMENT_YET"
                    or not str(item.get("game_id") or "").isdigit()
                    or not str(item.get("hitter_id") or "").isdigit()):
                raise ValueError("Invalid pending hitter identity in published benchmark.")
            try:
                utc(item["scheduled_first_pitch_utc"])
            except (TypeError, ValueError, KeyError, OverflowError) as exc:
                raise ValueError("Invalid saved first pitch in pending hitter audit.") from exc
            key=(str(item["game_id"]),str(item["hitter_id"]))
            if key in seen:
                raise ValueError("Repeated pending player-game identity in benchmark.")
            seen.add(key)
    elif truncated is not None:
        raise ValueError("Pending hitter truncation metadata without examples.")
    published=utc(payload.get("published_at_utc"))
    last_change=utc(payload.get("benchmark_last_changed_at_utc")
                    or payload.get("published_at_utc"))
    if last_change>published:
        raise ValueError("Benchmark evidence change timestamp exceeds feed publication.")
    refresh_kind=payload.get("source_refresh_kind","legacy_no_refresh_kind")
    if refresh_kind not in (
            "benchmark_changed","unchanged_saved_evidence_heartbeat",
            "legacy_no_refresh_kind"):
        raise ValueError("Unrecognized research snapshot refresh kind.")
    now=utc(clock())
    age=(now-published).total_seconds()
    if age< -120:
        raise ValueError("Published scoreboard timestamp is unexpectedly in the future.")
    if payload.get("source")!="public_github_main_scheduled_snapshot":
        raise ValueError("Published scoreboard is not the expected source.")
    return {
        "source":FEED_URL,"published_at_utc":published.isoformat(),
        "snapshot_age_hours":round(max(age,0)/3600,2),
        "may_be_stale":age>4*3600,
        "benchmark_last_changed_at_utc":last_change.isoformat(),
        "benchmark_age_hours":round(max((now-last_change).total_seconds(),0)/3600,2),
        "refresh_kind":refresh_kind,
        "refresh_proves_new_official_MLB_data":False,
        "last_source_commit":payload.get("source_git_revision"),
        "frozen_player_game_forecasts":count,
        "distinct_official_games":distinct,
        "pending":pending,"scored":scored,"ineligible":ineligible,
        "pending_player_game_examples":examples if examples is not None else [],
        "pending_examples_truncated":truncated if examples is not None else None,
        "pending_player_ids_available":examples is not None,
        "pending_saved_schedule_audit":_pending_time_audit(examples,pending,now),
        "metrics":report.get("metrics"),
        "per_game":report.get("per_game"),
        "no_wagers":True,
        "proven_betting_edge":False,
        "probabilities_condition":"at_least_one_official_at_bat",
        "limitations":payload.get("limitations",[]),
    }
