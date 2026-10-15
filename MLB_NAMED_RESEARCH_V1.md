# Tyler MLB name-based research (gated v2.19.3.36)

**Research-only, NO BET.** When \`TYLER_APP_MODULE=app_v2_19_3_36\` is selected and independently verified, authenticated Tyler chat can accept official names instead of requiring manually found MLB IDs.

\`\`\`text
sports mlb full research by name :: {"date":"2026-10-15","hitter_name":"Andrew Vaughn","team_name":"Milwaukee Brewers","starter_name":"Tyler Glasnow"}
\`\`\`

All names above are an illustrative verified identity from an October 15 audit, not a current betting selection; scheduled games must still be upcoming when called.

It retrieves the official pregame schedule for the Eastern local game date and uses exact name matching against the official active roster, plus the listed *probable* opposing starter. Optional \`reliever_names\` (array of up to four exact official names) are individually verified as listed pitchers on the opponent's active roster but **are not inferred to be likely to enter**. If a doubleheader creates multiple possible events, include the optional numeric official \`game_id\`; no arbitrary first-game pick is allowed.

The selected identity is separately rechecked by \`complete_matchup_research\` before the answer is returned. If team, game, hitter, starter, or nominated reliever identities disagree, the whole request fails without a forecast or wager. Current/probable/active labels are not confirmations of the final batting order or pitcher appearances.

The new command does not parse all conversational betting questions, find prices on FanDuel, estimate player-prop or correlated parlay win probabilities, or place bets. It is the verified name-to-ID lookup stage of that future workflow.

\`\`\`bash
python -m unittest -v test_sports_mlb_name_lookup test_v2_19_3_36_mlb_named_http
\`\`\`

Production selection remains v2.19.3.35 until this release is separately reviewed, deployed, and live-smoke-tested. Existing paper records and model/profile stay unchanged.
