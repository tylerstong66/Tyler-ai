"""v2.19.3.39: read-only GitHub MLB prospective research scorecard in Tyler chat.

The command fetches a signed-structure public GitHub snapshot from the latest
scheduled run; it does not treat local Render checkout as live or issue wagers.
"""
import json
import requests

import app_v2_19_3_38 as previous
from sports_mlb_prop_scoreboard_reader import load_published_shadow_scoreboard

base,app,ENGINE=previous.base,previous.app,previous.ENGINE
LEDGER,SKILL_LAB,TRAINER,EXECUTOR=previous.LEDGER,previous.SKILL_LAB,previous.TRAINER,previous.EXECUTOR
provider,harness=previous.provider,previous.harness
VERSION,VERSION_SHORT="2.19.3.39-mlb-shadow-scoreboard","v2.19.3.39"
base.VERSION,base.VERSION_SHORT=VERSION,VERSION_SHORT
COMMAND="sports mlb shadow scoreboard"
_OLD_HANDLE=base.handle_message


def handle_message(message):
    text=str(message or "").strip().casefold()
    if text!=COMMAND:
        return _OLD_HANDLE(message)
    tools=["read_current_github_shadow_benchmark_snapshot","verify_snapshot_sha256",
           "verify_no_bet_publication_summary"]
    try:
        snapshot=load_published_shadow_scoreboard()
    except (ValueError,TypeError,KeyError,RuntimeError,requests.RequestException) as exc:
        return base.base_payload(
            "mlb_shadow_scoreboard",
            "Official shadow benchmark snapshot unavailable; no wagering action. "+str(exc),
            success=False,used_tools=tools),503
    response={
        "status":"READ-ONLY PROSPECTIVE MLB SHADOW BENCHMARK — NO BET",
        "snapshot_published_at_utc":snapshot["published_at_utc"],
        "snapshot_age_hours":snapshot["snapshot_age_hours"],
        "snapshot_may_be_stale":snapshot["may_be_stale"],
        "source_url":snapshot["source"],
        "frozen_player_game_forecasts":snapshot["frozen_player_game_forecasts"],
        "distinct_official_games":snapshot["distinct_official_games"],
        "pending":snapshot["pending"],"scored":snapshot["scored"],
        "ineligible":snapshot["ineligible"],
        "metrics":snapshot["metrics"],
        "proven_betting_edge":False,
        "player_prop_probability_calibrated":False,
        "probabilities_condition":snapshot["probabilities_condition"],
        "no_wagers":True,
        "limitations":snapshot["limitations"],
    }
    return base.base_payload("mlb_shadow_scoreboard",
           json.dumps(response,indent=2,allow_nan=False),
           success=True,used_tools=tools) | {"sports_mlb_shadow_scoreboard":snapshot},200


base.handle_message=handle_message
_OLD_STATUS=app.view_functions["status"]


def status():
    data=dict(_OLD_STATUS().get_json() or {})
    data.update(
        version=VERSION,version_short=VERSION_SHORT,
        sports_mlb_shadow_scoreboard_command_supported=True,
        sports_mlb_shadow_scoreboard_source="published_github_snapshot",
        sports_mlb_shadow_scoreboard_automated_snapshot_not_guaranteed_instant=True,
        sports_mlb_shadow_scoreboard_wager_execution_enabled=False)
    return base.jsonify(data)


app.view_functions["status"]=status
_OLD_SAFE_FILES=EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn=lambda:sorted(set(_OLD_SAFE_FILES())|{
    "app_v2_19_3_39.py","sports_mlb_prop_scoreboard_feed.py",
    "sports_mlb_prop_scoreboard_reader.py",
    "test_sports_mlb_prop_scoreboard_feed.py",
    "test_v2_19_3_39_mlb_scoreboard_http.py",
})
__all__=previous.__all__
