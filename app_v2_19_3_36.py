"""Versioned, gated research-by-name command for authenticated Tyler AI chat.

No name guessing, blind player-ID substitution, model promotion, sportsbook
pricing, or wager execution. The previous command remains supported.
"""
import json
import requests

import app_v2_19_3_35 as previous
from app_v2_19_3_34 import _reject_duplicate_keys
from sports_mlb_combined import complete_matchup_research
from sports_mlb_name_lookup import resolve_named_pregame

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
LEDGER, SKILL_LAB, TRAINER, EXECUTOR = previous.LEDGER, previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
provider, harness = previous.provider, previous.harness
VERSION, VERSION_SHORT = "2.19.3.36-mlb-name-research", "v2.19.3.36"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
PREFIX = "sports mlb full research by name ::"


def parse_named_request(message):
    if not isinstance(message, str) or not message.lower().startswith(PREFIX):
        raise ValueError("Expected sports mlb full research by name :: {JSON}.")
    payload = json.loads(message[len(PREFIX):].strip(), object_pairs_hook=_reject_duplicate_keys,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON number.")))
    required = {"date", "hitter_name"}
    allowed = required | {"team_name", "starter_name", "reliever_names", "game_id"}
    if not isinstance(payload, dict) or not required <= set(payload) or set(payload) - allowed:
        raise ValueError("Name request needs date and hitter_name; optional team_name, starter_name, reliever_names, game_id.")
    return payload


_OLD_HANDLE = base.handle_message


def handle_message(message):
    text = str(message or "").strip()
    if not text.lower().startswith(PREFIX):
        return _OLD_HANDLE(message)
    used = ["official_mlb_schedule", "official_roster_name_resolution",
            "pregame_batter_pitcher_stats", "past_bullpen_boxscore_counts", "no_wager_execution"]
    try:
        raw = parse_named_request(text)
        resolved = resolve_named_pregame(**raw)
        researched = complete_matchup_research(
            resolved["game_id"], resolved["hitter_id"], resolved["hitter_side"], resolved["reliever_ids"])
        if (researched["game_id"] != str(resolved["game_id"]) or
                researched["hitter"]["id"] != resolved["hitter_id"] or
                researched["probable_starter"]["id"] != resolved["probable_starter_id"] or
                [item["pitcher"]["id"] for item in researched["matchup_research"]["reliever_matchups"]]
                    != resolved["reliever_ids"]):
            raise ValueError("Official identity changed between name resolution and independent research.")
    except (ValueError, TypeError, KeyError, RuntimeError, requests.RequestException) as exc:
        return base.base_payload("sports_mlb_name_research",
            "Name-based research unavailable; no wager or model action. " + str(exc),
            success=False, used_tools=used), 409
    result = {"identity": resolved, "research": researched,
              "no_wager": True, "calibrated_hit_probability": None,
              "calibrated_home_run_probability": None, "parlay_joint_probability": None}
    response = json.dumps({
        "status": researched["decision"], "hitter": researched["hitter"],
        "game_id": researched["game_id"], "teams": {
            "hitter_team": resolved["team_name"], "opponent": resolved["opponent_name"]},
        "probable_starter": researched["probable_starter"],
        "summary": researched["summary"], "data_coverage": researched["coverage"],
        "named_relief_candidates": resolved["reliever_ids"],
        "limitations": resolved["limitations"],
        "no_calibrated_prop_probability": True, "actual_wager": 0,
    }, indent=2, allow_nan=False)
    return base.base_payload("sports_mlb_name_research", response, success=True,
              used_tools=used) | {"sports_mlb_name_research": result}, 200


base.handle_message = handle_message
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_mlb_named_research_command_supported=True,
                sports_mlb_named_research_fuzzy_matching_enabled=False,
                sports_mlb_named_research_predictive_edge_proven=False,
                sports_mlb_named_research_wager_execution_enabled=False)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {
    "app_v2_19_3_36.py", "sports_mlb_name_lookup.py",
    "test_v2_19_3_36_mlb_named_http.py", "test_sports_mlb_name_lookup.py"})
__all__ = previous.__all__ + ["parse_named_request"]
