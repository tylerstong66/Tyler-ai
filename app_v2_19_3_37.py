"""v2.19.3.37: named MLB research automatically discovers recent relief usage.

Does not infer actual bullpen appearances, probabilities, FanDuel quotes, or
wager instructions. Existing commands delegate to previous version modules.
"""
import json
import requests

import app_v2_19_3_36 as previous
from app_v2_19_3_34 import _reject_duplicate_keys
from sports_mlb_auto_bullpen import auto_bullpen_matchup
from sports_mlb_name_lookup import resolve_named_pregame
from sports_mlb_sources import OfficialMlbReader

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
LEDGER, SKILL_LAB, TRAINER, EXECUTOR = previous.LEDGER, previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
provider, harness = previous.provider, previous.harness
VERSION, VERSION_SHORT = "2.19.3.37-mlb-auto-bullpen", "v2.19.3.37"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
PREFIX = previous.PREFIX


def parse_auto_request(text):
    if not isinstance(text, str) or not text.lower().startswith(PREFIX):
        raise ValueError("Expected sports mlb full research by name :: JSON.")
    data = json.loads(text[len(PREFIX):].strip(), object_pairs_hook=_reject_duplicate_keys,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Invalid JSON number.")))
    if not isinstance(data, dict):
        raise ValueError("Named research must be a JSON object.")
    auto = data.pop("auto_bullpen", None)
    if auto is not None and not isinstance(auto, bool):
        raise ValueError("auto_bullpen must be true or false.")
    previous.parse_named_request(PREFIX + json.dumps(data, allow_nan=False))
    named = data.get("reliever_names") or []
    if auto is None:
        auto = not bool(named)
    if auto and named:
        raise ValueError("Specify explicit reliever_names or auto_bullpen, not both.")
    return data, auto


_OLD_HANDLE = base.handle_message


def handle_message(message):
    text = str(message or "").strip()
    if not text.lower().startswith(PREFIX):
        return _OLD_HANDLE(message)
    used = ["mlb_official_name_resolution", "prior_final_relief_roles",
            "mlb_batter_vs_pitcher_source_records", "research_only_no_wager"]
    try:
        named, auto = parse_auto_request(text)
        reader = OfficialMlbReader()
        resolved = resolve_named_pregame(reader=reader, **named)
        report = auto_bullpen_matchup(
            resolved["game_id"], resolved["hitter_id"], resolved["hitter_side"],
            manual_reliever_ids=resolved["reliever_ids"], auto_select=auto, reader=reader)
        selected = report["reliever_ids_analyzed"]
        if (report["game_id"] != str(resolved["game_id"]) or
                report["hitter"]["id"] != resolved["hitter_id"] or
                report["probable_starter"]["id"] != resolved["probable_starter_id"] or
                report["matchup_research"]["event_start"] != resolved["game_start"]):
            raise ValueError("Official game/hitter/starter identity or first pitch changed.")
        if not auto and selected != resolved["reliever_ids"]:
            raise ValueError("Manual relief identities changed between resolution and research.")
        if report["wager_executed"] or report["estimated_home_run_probability"] is not None:
            raise ValueError("Research must not claim wagers or prop probabilities.")
    except (ValueError, KeyError, TypeError, RuntimeError, requests.RequestException) as exc:
        return base.base_payload("mlb_auto_bullpen_research",
            "Source-backed MLB research unavailable; no betting action. " + str(exc),
            success=False, used_tools=used), 409
    summary = {
        "status": "RESEARCH ONLY - NO BET",
        "game_id": report["game_id"], "hitter": report["hitter"],
        "teams": {"hitter_team": resolved["team_name"], "opponent": resolved["opponent_name"]},
        "probable_starter": report["probable_starter"],
        "summary": report["summary"],
        "relief_candidates": [{
            "pitcher": row["pitcher"], "historical_plate_appearances": row["plate_appearances"],
            "historical_batting_average": row["historical_batting_average"],
            "workload": next(({
                "recorded_appearances": x["recorded_appearances"],
                "pitches_thrown_observed": x["pitches_thrown_observed"],
                "availability": x["availability"]
            } for x in report["recent_bullpen_research"]["candidates"]
              if x["pitcher_id"] == row["pitcher"]["id"]), None)
        } for row in report["matchup_research"]["reliever_matchups"]],
        "auto_bullpen_selected": report["auto_bullpen_enabled"],
        "historical_bullpen_selection_complete": (
            report["auto_bullpen_discovery"]["historical_game_coverage_complete"]
            if report["auto_bullpen_discovery"] is not None else None),
        "coverage": report["coverage"],
        "limitations": [
            "Relief candidates come from recent historical appearances, not a validated next-game appearance forecast.",
            "Active roster does not establish a lineup or guarantee that a probable starter or reliever appears.",
            "No MLB player-prop probabilities, no sportsbook quotes, no correlated parlay estimates or wager execution.",
        ],
        "no_calibrated_player_probabilities": True,
        "actual_wager": 0,
    }
    return base.base_payload("mlb_auto_bullpen_research",
                             json.dumps(summary, indent=2, allow_nan=False),
                             success=True, used_tools=used) | {"sports_mlb_auto_research": report}, 200


base.handle_message = handle_message
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_mlb_auto_bullpen_research_supported=True,
                sports_mlb_auto_bullpen_probabilities_calibrated=False,
                sports_mlb_auto_bullpen_wager_execution_enabled=False)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {
    "app_v2_19_3_37.py", "sports_mlb_reliever_candidates.py", "sports_mlb_auto_bullpen.py",
    "test_sports_mlb_reliever_candidates.py", "test_sports_mlb_auto_bullpen.py",
    "test_v2_19_3_37_mlb_auto_http.py"})
__all__ = previous.__all__ + ["parse_auto_request"]
