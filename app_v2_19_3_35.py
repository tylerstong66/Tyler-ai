"""Combined read-only MLB research Tyler chat option, inactive until deployed."""
import json

import requests
import app_v2_19_3_34 as previous
from sports_mlb_combined import complete_matchup_research

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
LEDGER, SKILL_LAB, TRAINER, EXECUTOR = previous.LEDGER, previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
provider, harness = previous.provider, previous.harness
VERSION, VERSION_SHORT = "2.19.3.35-mlb-full-research", "v2.19.3.35"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
PREFIX = "sports mlb full research ::"


def parse_full_request(text):
    if not isinstance(text, str) or not text.lower().startswith(PREFIX):
        raise ValueError("Expected sports mlb full research :: {JSON}.")
    return previous.parse_research_request(previous.PREFIX + text[len(PREFIX):])


_OLD_HANDLE = base.handle_message


def handle_message(message):
    text = str(message or "").strip()
    if not text.lower().startswith(PREFIX):
        return _OLD_HANDLE(message)
    used = ["mlb_official_pregame_identity", "historical_hitter_vs_pitcher",
            "official_recent_bullpen_workload", "no_bet_research"]
    try:
        game_id, hitter_id, hitter_side, reliever_ids = parse_full_request(text)
        result = complete_matchup_research(game_id, hitter_id, hitter_side, reliever_ids)
    except (ValueError, TypeError, KeyError, RuntimeError, requests.RequestException) as exc:
        return base.base_payload("mlb_full_matchup_research",
            "Complete MLB research unavailable; no betting action. " + str(exc),
            success=False, used_tools=used), 409
    response = json.dumps({
        "status": result["decision"], "game_id": result["game_id"],
        "hitter": result["hitter"], "probable_starter": result["probable_starter"],
        "summary": result["summary"], "coverage": result["coverage"],
        "estimated_hit_probability": None, "estimated_home_run_probability": None,
        "projected_relief_probability": None, "joint_parlay_probability": None,
        "actual_wager": 0, "note": "Research only; bullpen availability and live FanDuel prices not verified."
    }, indent=2, allow_nan=False)
    return base.base_payload("mlb_full_matchup_research", response,
        success=True, used_tools=used) | {"sports_mlb_full_research": result}, 200


base.handle_message = handle_message
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_mlb_full_research_command_supported=True,
                sports_mlb_full_research_live_api_verified=False,
                sports_mlb_full_research_probabilities_validated=False,
                sports_mlb_full_research_betting_enabled=False)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {
    "app_v2_19_3_35.py", "sports_mlb_bullpen_usage.py", "sports_mlb_combined.py",
    "test_v2_19_3_35_mlb_full_chat.py", "test_sports_mlb_combined.py",
    "test_sports_mlb_bullpen_usage.py"})
__all__ = previous.__all__ + ["parse_full_request"]
