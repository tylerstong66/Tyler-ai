# Official MLB bullpen workload research v1

This component fetches **recent, completed official MLB game boxscores** to show descriptive workload for up to four nominated relievers on a specified upcoming game's pitching team.

It checks: official upcoming pregame status and team, active-roster pitcher identities, bounded past-game schedule, unique game IDs, final statuses and exact match of official final game identity/start time/team. It then reads pitch counts for appearances listed in the official boxscore. Missing or unverified finals/pitch counts remain explicitly incomplete; future games and the upcoming event do not become past-game evidence.

Only evidence available **before** the upcoming first pitch is accepted. Last recorded start, appearances and summed pitches thrown do **not** prove who is available tonight. No relief-appearance probability, hit probability, home-run probability, EV or wager recommendation is produced. Bullpen roles, availability, current medical/injury status and warmup information remain unknown.

This is **not** a live Tyler chat integration, model upgrade, or proof of a betting edge. Tests use synthetic fixtures and mocked official responses, not independently verified live historical captures.

Tests:

\`\`\`bash
python -m unittest -v test_sports_mlb_bullpen_usage
\`\`\`

For future integration: call \`recent_pitcher_usage(upcoming_game_id, pitching_side, candidate_ids, reader=...)\` only with a verified upcoming official MLB game and player IDs, and preserve all source receipts and coverage gaps in the rendered answer. Never promote this usage history to a forecast without separate calibration and out-of-sample checks.
