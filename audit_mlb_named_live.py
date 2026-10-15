"""One-shot read-only, public MLB name-to-matchup source audit."""
from sports_mlb_name_lookup import resolve_named_pregame
from sports_mlb_combined import complete_matchup_research


def main():
    resolved = resolve_named_pregame(
        "2026-10-15", "Andrew Vaughn",
        team_name="Milwaukee Brewers",
        starter_name="Tyler Glasnow",
        game_id=849810,
    )
    print("NAMED_LOOKUP", {k: resolved[k] for k in (
        "game_id", "hitter_id", "hitter_name", "hitter_side",
        "team_name", "opponent_name", "probable_starter_name")}, flush=True)
    research = complete_matchup_research(
        resolved["game_id"], resolved["hitter_id"], resolved["hitter_side"], [])
    assert research["decision"] == "RESEARCH ONLY - NO BET"
    assert research["probable_starter"]["id"] == resolved["probable_starter_id"]
    assert research["hitter"]["id"] == resolved["hitter_id"]
    assert research["wager_executed"] is False
    print("NAMED_TO_RESEARCH_SUCCESS",
          research["game_id"], research["hitter"]["name"],
          research["probable_starter"]["name"],
          research["coverage"]["historical_pitcher_matchups"],
          "no_wager", not research["wager_executed"], flush=True)


if __name__ == "__main__":
    main()
