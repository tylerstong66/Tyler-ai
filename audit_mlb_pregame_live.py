"""Live public MLB pregame audit; does not place wagers or mutate production."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sports_mlb_sources import OfficialMlbReader, pregame_research, utc
from sports_mlb_combined import complete_matchup_research


def run():
    reader = OfficialMlbReader()
    now = datetime.now(timezone.utc)
    local = now.astimezone(ZoneInfo("America/New_York")).date()
    data, receipt = reader.load("schedule", {
        "sportId": 1, "startDate": local.isoformat(),
        "endDate": (local + timedelta(days=3)).isoformat(), "gameTypes": "R,F,D,L,W"})
    entries = [game for day in data.get("dates", []) for game in day.get("games", [])]
    print("PREGAME_AUDIT schedule_count", len(entries),
          "retrieved", receipt["retrieved_at"])
    reasons = []
    for event in entries[:20]:
        pk = event.get("gamePk")
        if not isinstance(pk, int):
            continue
        start = utc(event["gameDate"])
        if start <= now + timedelta(minutes=30):
            continue
        if event.get("status", {}).get("abstractGameState") != "Preview":
            continue
        try:
            game, _ = reader.load("game/" + str(pk) + "/feed/live", api_version="v1.1")
            gd = game.get("gameData", {})
            probable = gd.get("probablePitchers", {}).get("home")
            if not probable or not isinstance(probable.get("id"), int):
                reasons.append(str(pk) + ": no home probable starter");continue
            away_id = gd.get("teams", {}).get("away", {}).get("id")
            if not isinstance(away_id, int):
                reasons.append(str(pk) + ": no official away ID"); continue
            roster, _ = reader.load("teams/" + str(away_id) + "/roster", {
                "rosterType": "active",
                "date": start.astimezone(ZoneInfo("America/New_York")).date().isoformat()})
            nonpitchers = [p.get("person", {}).get("id") for p in roster.get("roster", [])
                if p.get("position", {}).get("abbreviation") not in ("P", None)]
            if not nonpitchers:
                reasons.append(str(pk) + ": no active hitter");continue
            hitter_id = nonpitchers[0]
            result = pregame_research(pk, hitter_id, "away", [], reader=reader)
            print("END_TO_END_SUCCESS", "gamePk", pk, "hitter", result["hitter"]["name"],
                  "probable_starter", result["starter_matchup"]["pitcher"]["name"],
                  "h2h_pa", result["starter_matchup"]["plate_appearances"],
                  "source_receipts", len(result["official_data"]["capture_receipts"]),
                  "no_bet", result["decision"])
            if result["decision"] != "RESEARCH ONLY - NO BET":
                raise RuntimeError("Unexpected wagering decision")
            home_id = gd["teams"]["home"]["id"]
            home_roster, _ = reader.load("teams/" + str(home_id) + "/roster", {
                "rosterType": "active",
                "date": start.astimezone(ZoneInfo("America/New_York")).date().isoformat()})
            pitchers = [r.get("person", {}).get("id") for r in home_roster.get("roster", [])
                if r.get("position", {}).get("abbreviation") == "P"
                and r.get("person", {}).get("id") != probable["id"]]
            if not pitchers:
                reasons.append(str(pk) + ": no distinct pitcher roster candidate"); continue
            candidate_id = pitchers[0]
            full = complete_matchup_research(pk, hitter_id, "away", [candidate_id], reader=reader)
            candidate = full["recent_bullpen_research"]["candidates"][0]
            print("FULL_WORKFLOW_SUCCESS", "gamePk", pk, "candidate_id", candidate_id,
                  "pitcher_workload_games", candidate["recorded_appearances"],
                  "pitches_in_window", candidate["pitches_thrown_observed"],
                  "recent_coverage_complete", candidate["coverage_complete"],
                  "matching_source_ids", full["coverage"]["historical_pitcher_matchups"],
                  "no_wager", not full["wager_executed"])
            if full["decision"] != "RESEARCH ONLY - NO BET" or full["wager_executed"]:
                raise RuntimeError("Full research unexpectedly attempted wagering")
            return
        except Exception as exc:
            reasons.append(str(pk) + ": " + type(exc).__name__ + " " + str(exc)[:150])
    print("AUDIT_NO_ELIGIBLE_SUCCESS", "; ".join(reasons[:15]))
    raise RuntimeError("No tested upcoming MLB matchup completed end-to-end.")


if __name__ == "__main__":
    run()
