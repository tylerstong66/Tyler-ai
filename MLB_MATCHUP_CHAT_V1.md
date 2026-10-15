# Tyler MLB matchup research — chat command (inactive until deployment)

This release extends \`app_v2_19_3_33\` with a guarded, **read-only** command. It is not automatically activated by merely merging code: deployment must explicitly set \`TYLER_APP_MODULE=app_v2_19_3_34\` after reviewing live MLB StatsAPI compatibility.

Example for a *future* pregame game, with real MLB player IDs:

\`\`\`text
sports mlb matchup research :: {"game_id":849831,"hitter_id":10001,"hitter_side":"away","reliever_ids":[30001]}
\`\`\`

The IDs above are **synthetic placeholders** for demonstration, not a current valid game/player recommendation. The exact input must include official MLB gamePk, hitter MLB ID, batter side and optionally up to four separately identified relief-pitcher IDs. This command does not search players by name because ungrounded name matching could misidentify players. It does not assume any relief pitcher is likely to appear.

The command:
1. Uses official pregame game state, teams, rosters and probable opposing starter;
2. Fetches and validates the supported historical batter/pitcher totals;
3. Returns structured source receipts, missing-data flags, small-sample warnings, and research-only comparisons;
4. Does not call the predictive language model or write paper/wager records;
5. Rejects malformed, ambiguous, after-first-pitch, or unavailable data.

The active production version and frozen prospective sports cohorts are unchanged unless deployment is separately authorized and verified. Player prop probabilities, EV, odds feeds, likely bullpen sequences and wager execution are **not** enabled.

Tests: \`python -m unittest -v test_v2_19_3_34_mlb_chat test_sports_mlb_sources test_sports_mlb_matchups\`.
