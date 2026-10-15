"""v2.19.3.38: season-contextual MLB hitter, starter and bullpen research.

Read-only, authenticated, source checked. No estimated next-game prop
probabilities, FanDuel prices, correlation models, or wager execution.
"""
import json
import requests

import app_v2_19_3_37 as previous
from sports_mlb_contextual import contextual_mlb_research
from sports_mlb_name_lookup import resolve_named_pregame
from sports_mlb_sources import OfficialMlbReader

base, app, ENGINE=previous.base,previous.app,previous.ENGINE
LEDGER, SKILL_LAB, TRAINER, EXECUTOR=previous.LEDGER,previous.SKILL_LAB,previous.TRAINER,previous.EXECUTOR
provider,harness=previous.provider,previous.harness
VERSION, VERSION_SHORT="2.19.3.38-mlb-season-context","v2.19.3.38"
base.VERSION,base.VERSION_SHORT=VERSION,VERSION_SHORT
PREFIX=previous.PREFIX


_OLD_HANDLE=base.handle_message


def handle_message(message):
    text=str(message or "").strip()
    if not text.lower().startswith(PREFIX):
        return _OLD_HANDLE(message)
    used=["official_pregame_identity","recorded_relief_appearances",
          "mlb_official_hitter_season_totals","official_handedness","no_bet_research"]
    try:
        named,auto=previous.parse_auto_request(text)
        reader=OfficialMlbReader()
        resolved=resolve_named_pregame(reader=reader,**named)
        research=contextual_mlb_research(
            resolved["game_id"],resolved["hitter_id"],resolved["hitter_side"],
            auto_select=auto,manual_reliever_ids=resolved["reliever_ids"],reader=reader)
        if (research["game_id"]!=str(resolved["game_id"]) or
                research["hitter"]["id"]!=resolved["hitter_id"] or
                research["probable_starter"]["id"]!=resolved["probable_starter_id"] or
                research["matchup_research"]["event_start"]!=resolved["game_start"]):
            raise ValueError("Official MLB identity changed across name resolution and research.")
        if research["estimated_hit_probability"] is not None or research["estimated_home_run_probability"] is not None:
            raise ValueError("Uncalibrated player-prop probabilities must remain null.")
        if research["wager_executed"]:
            raise ValueError("Research cannot execute wagers.")
    except (ValueError,TypeError,KeyError,RuntimeError,requests.RequestException) as exc:
        return base.base_payload("mlb_contextual_research",
             "Sourced MLB research unavailable; no betting action. "+str(exc),
             success=False,used_tools=used),409
    player=research["hitter_season_context"]
    response={
        "status":research["decision"],
        "game_id":research["game_id"],
        "hitter":research["hitter"],
        "teams":{"hitter_team":resolved["team_name"],"opponent":resolved["opponent_name"]},
        "probable_starter":research["probable_starter"],
        "official_handedness":{
            "hitter_bats":player["hitter"]["hand"],
            "probable_starter_throws":player["opposing_probable_starter"]["hand"]},
        "regular_season_hitter_context":player["season_statistics"],
        "starter_matchup":research["matchup_research"]["starter_matchup"],
        "potential_relief_pitcher_matchups":research["matchup_research"]["reliever_matchups"],
        "recent_bullpen_coverage":research["coverage"],
        "summary":research["summary"],
        "limitations":[
            "Season AVG and pitcher head-to-head AVG are not a calibrated probability of a hit tonight.",
            "Bullpen shortlist ranks historical relief usage, not probability of entering this game.",
            "No quoted sportsbook lines, next-game player prop probabilities, EV or correlated parlay estimates.",
        ],
        "no_calibrated_player_prop_probability":True,
        "no_wager":True,
    }
    return base.base_payload("mlb_contextual_research",
             json.dumps(response,indent=2,allow_nan=False),
             success=True,used_tools=used) | {"sports_mlb_contextual_research":research},200


base.handle_message=handle_message
_OLD_STATUS=app.view_functions["status"]


def status():
    data=dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION,version_short=VERSION_SHORT,
                sports_mlb_official_season_context_supported=True,
                sports_mlb_official_handedness_supported=True,
                sports_mlb_player_prop_probabilities_calibrated=False,
                sports_mlb_contextual_wager_execution_enabled=False)
    return base.jsonify(data)


app.view_functions["status"]=status
_OLD_SAFE_FILES=EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn=lambda:sorted(set(_OLD_SAFE_FILES()) | {
    "app_v2_19_3_38.py","sports_mlb_hitter_context.py","sports_mlb_contextual.py",
    "test_sports_mlb_hitter_context.py","test_sports_mlb_contextual.py",
    "test_v2_19_3_38_mlb_context_http.py"})
__all__=previous.__all__
