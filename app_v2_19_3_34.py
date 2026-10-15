"""Read-only, authenticated-chat compatible MLB matchup research handler.

This module extends the existing production runtime but is NOT activated unless
TYLER_APP_MODULE is explicitly changed after review. No bets, model changes,
profile promotion, or historical paper record writes.
"""
import json
import requests

import app_v2_19_3_33 as previous
from sports_mlb_sources import pregame_research

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
LEDGER = previous.LEDGER
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
VALIDATOR, CANDIDATE_VALIDATOR = previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
VERSION, VERSION_SHORT = "2.19.3.34-mlb-research-chat", "v2.19.3.34"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
PREFIX = "sports mlb matchup research ::"


def _reject_duplicate_keys(items):
    data = {}
    for key, value in items:
        if key in data:
            raise ValueError("Duplicate research input key.")
        data[key] = value
    return data


def parse_research_request(message):
    """Fixed command + JSON only; no invented default player IDs or relievers."""
    if not isinstance(message, str) or not message.lower().startswith(PREFIX):
        raise ValueError("Expected sports mlb matchup research :: {JSON}.")
    body = message[len(PREFIX):].strip()
    data = json.loads(body, object_pairs_hook=_reject_duplicate_keys,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Invalid JSON number.")))
    if not isinstance(data, dict) or set(data) - {"game_id", "hitter_id", "hitter_side", "reliever_ids"}:
        raise ValueError("Supply only game_id, hitter_id, hitter_side and optional reliever_ids.")
    if not {"game_id", "hitter_id", "hitter_side"}.issubset(data):
        raise ValueError("Missing required game_id, hitter_id or hitter_side.")
    if "reliever_ids" in data and not isinstance(data["reliever_ids"], list):
        raise ValueError("reliever_ids must be a JSON array.")
    return data["game_id"], data["hitter_id"], data["hitter_side"], data.get("reliever_ids", [])


_OLD_HANDLE = base.handle_message


def handle_message(message):
    text = str(message or "").strip()
    if not text.lower().startswith(PREFIX):
        return _OLD_HANDLE(message)
    tools_used = ["official_mlb_statsapi_research", "pre_event_identity_validation",
                  "historical_batter_pitcher_counts"]
    try:
        game_id, hitter_id, hitter_side, reliever_ids = parse_research_request(text)
        result = pregame_research(game_id, hitter_id, hitter_side, reliever_ids)
    except (ValueError, TypeError, KeyError, RuntimeError, json.JSONDecodeError,
            requests.RequestException) as exc:
        # A failed remote read must not be converted into an invented matchup.
        return base.base_payload("sports_mlb_matchup_research",
                "Research unavailable; no wager or model action. " + str(exc),
                success=False, used_tools=tools_used), 409
    selected = result["starter_matchup"]
    brief = {
        "status": "MLB MATCHUP RESEARCH - NO BET",
        "game_id": result["game_id"], "hitter": result["hitter"],
        "probable_starter": selected,
        "possible_relief_pitchers": result["reliever_matchups"],
        "data_coverage": result["coverage"],
        "no_calibrated_player_prop_probability": True,
        "no_bet_or_wager_execution": True,
        "limitations": result["limitations"],
    }
    reply = json.dumps(brief, indent=2, allow_nan=False)
    return base.base_payload("sports_mlb_matchup_research", reply, success=True,
              used_tools=tools_used) | {"sports_mlb_research": result}, 200


base.handle_message = handle_message

_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_mlb_research_command_supported=True,
                sports_mlb_research_official_data_live_schema_verified=False,
                sports_mlb_player_prop_probabilities_calibrated=False,
                sports_mlb_betting_enabled=False)
    return base.jsonify(data)


app.view_functions["status"] = status

_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {
    "app_v2_19_3_34.py", "sports_mlb_sources.py", "sports_mlb_matchups.py",
    "test_v2_19_3_34_mlb_chat.py", "test_sports_mlb_sources.py", "test_sports_mlb_matchups.py"})
__all__ = previous.__all__ + ["parse_research_request"]
