"""Read-only external Tyler AI deployment smoke check; no credentials or wagers."""
import os
import sys

import requests

BASE = "https://tyler-ai.onrender.com"
EXPECTED = os.environ.get("EXPECTED_VERSION", "2.19.3.33")


def get(path, timeout=120):
    response = requests.get(BASE + path, timeout=timeout, allow_redirects=False,
                            headers={"User-Agent": "tyler-render-smoke/1.0"})
    print(path, response.status_code, "bytes", len(response.content), flush=True)
    return response


def main():
    status = get("/status")
    status.raise_for_status()
    obj = status.json()
    print("STATUS_SUMMARY", {k: obj.get(k) for k in (
        "status", "version", "version_short", "secured",
        "sports_paper_supported_sports", "sports_mlb_full_research_command_supported",
        "sports_mlb_full_research_betting_enabled")}, flush=True)
    if obj.get("status") != "online":
        raise RuntimeError("Unexpected status response.")
    if not str(obj.get("version", "")).startswith(EXPECTED):
        raise RuntimeError("Deployment is not expected version " + EXPECTED)
    if obj.get("secured") is not True:
        raise RuntimeError("Tyler API-key security appears disabled.")
    if obj.get("sports_wager_execution_enabled") is not False:
        raise RuntimeError("Sports wager execution must remain disabled.")
    if EXPECTED == "2.19.3.35":
        if obj.get("sports_mlb_full_research_command_supported") is not True:
            raise RuntimeError("Research command absent from deployed module.")
        if obj.get("sports_mlb_full_research_betting_enabled") is not False:
            raise RuntimeError("Sports betting must remain disabled.")
    if EXPECTED in ("2.19.3.36", "2.19.3.37", "2.19.3.38"):
        if obj.get("sports_mlb_named_research_command_supported") is not True:
            raise RuntimeError("Named MLB research command not active.")
        if obj.get("sports_mlb_named_research_predictive_edge_proven") is not False:
            raise RuntimeError("Named MLB research must not claim proven predictive edge.")
        if obj.get("sports_mlb_named_research_wager_execution_enabled") is not False:
            raise RuntimeError("Named MLB research must not execute wagers.")
    if EXPECTED in ("2.19.3.37", "2.19.3.38"):
        if obj.get("sports_mlb_auto_bullpen_research_supported") is not True:
            raise RuntimeError("MLB auto-bullpen research not registered.")
        if obj.get("sports_mlb_auto_bullpen_probabilities_calibrated") is not False:
            raise RuntimeError("MLB auto-bullpen must not claim calibrated probabilities.")
        if obj.get("sports_mlb_auto_bullpen_wager_execution_enabled") is not False:
            raise RuntimeError("MLB auto-bullpen wager execution must be disabled.")
    if EXPECTED == "2.19.3.38":
        if obj.get("sports_mlb_official_season_context_supported") is not True:
            raise RuntimeError("Hitter season context not active.")
        if obj.get("sports_mlb_official_handedness_supported") is not True:
            raise RuntimeError("MLB handedness source data not registered.")
        if obj.get("sports_mlb_player_prop_probabilities_calibrated") is not False:
            raise RuntimeError("App must not claim player-prop calibration.")
        if obj.get("sports_mlb_contextual_wager_execution_enabled") is not False:
            raise RuntimeError("Wager execution must stay disabled.")
    health = get("/health")
    health.raise_for_status()
    if health.json().get("status") != "healthy":
        raise RuntimeError("Health endpoint not healthy.")
    protected = get("/ui/paper-results")
    if protected.status_code != 401:
        raise RuntimeError("Protected paper-results page unexpectedly accessible.")
    unauthorized = requests.post(BASE + "/chat",
        json={"message": 'sports mlb full research :: {"game_id":849810,"hitter_id":605141,"hitter_side":"away"}'},
        timeout=30, allow_redirects=False,
        headers={"User-Agent": "tyler-render-smoke/1.0"})
    print("/chat unauthenticated", unauthorized.status_code, flush=True)
    if unauthorized.status_code != 401:
        raise RuntimeError("New MLB research chat command is not protected.")
    if EXPECTED in ("2.19.3.36", "2.19.3.37", "2.19.3.38"):
        named = requests.post(BASE + "/chat",
            json={"message": 'sports mlb full research by name :: {"date":"2026-10-15","hitter_name":"Andrew Vaughn","team_name":"Milwaukee Brewers"}'},
            timeout=30, allow_redirects=False,
            headers={"User-Agent": "tyler-render-smoke/1.0"})
        print("/chat named unauthenticated", named.status_code, flush=True)
        if named.status_code != 401:
            raise RuntimeError("Named MLB research command is not protected.")
    print("READ_ONLY_SMOKE_PASS", EXPECTED, flush=True)


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        print("READ_ONLY_SMOKE_FAIL", type(exc).__name__, str(exc)[:350], flush=True)
        sys.exit(1)
