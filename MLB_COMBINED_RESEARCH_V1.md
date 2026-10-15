# Combined MLB batter/starter/bullpen research — inactive v2.19.3.35

**NO BET. No calibrated player prop, parlay, reliever appearance, or expected-value model.** The module is committed behind a versioned launch gate and is not active in production unless Render \`TYLER_APP_MODULE\` is separately changed to \`app_v2_19_3_35\` after independent live-source compatibility testing.

When activated, the new authenticated Tyler chat command is:

\`\`\`text
sports mlb full research :: {"game_id":849831,"hitter_id":10001,"hitter_side":"away","reliever_ids":[30001]}
\`\`\`

IDs above are synthetic fixtures, not verified upcoming MLB participants.

The command uses the existing official-source reader twice to validate a pregame game, historical hitter vs. probable starter and nominated relievers, and recent pitch workloads from verified completed game boxscores. It cross-checks the official event start, game ID and nominated reliever IDs; any mismatch aborts the combined report.

The response includes prose summaries tied to the counts, source receipts, provenance, unknown reliever availability, and incomplete coverage. It never interprets a batter's historical average as the probability of a hit tonight or sums individual bet probabilities into a parlay probability.

Required checks:

\`\`\`bash
python -m unittest -v test_sports_mlb_combined test_v2_19_3_35_mlb_full_chat
\`\`\`

Next steps: run a real-data StatsAPI schema audit with publicly accessible records; benchmark source completeness and latency; validate sportsbook quote/market data and develop separate player-prop models. Do not promote to production until live compatibility and authentication are confirmed.
