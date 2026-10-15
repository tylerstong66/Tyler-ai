# MLB bullpen research auto-shortlist — v2.19.3.37

**Research-only / NO BET.** This release fixes the most visible omission in the first successful authenticated production response: when no potential relievers were supplied, Tyler returned *"No prospective relievers were supplied or verified."*

Once v2.19.3.37 is deliberately activated, the **same** named research command automatically identifies **up to four** pitchers with recent verified **relief appearances** from public MLB completed-game boxscores:

\`\`\`text
sports mlb full research by name :: {"date":"2026-10-15","hitter_name":"Andrew Vaughn","team_name":"Milwaukee Brewers","starter_name":"Tyler Glasnow"}
\`\`\`

This sample is an October 15, 2026 pregame illustration; it will not run after first pitch.

If \`reliever_names\` is provided, its exact official names are used and automatic selection is disabled by default. To suppress auto-selection when names are omitted, add \`"auto_bullpen": false\`. Providing a nonempty \`reliever_names\` list together with \`"auto_bullpen": true\` is rejected.

## Evidence restrictions

- Only verified **Final** MLB games within the prior seven calendar days are inspected. A team's recent schedule and each selected final are independently checked against official game identity, team side, and first-pitch time.
- The pitcher must be on the upcoming opponent's official active roster, recorded as a **reliever** in a historical boxscore (\`gamesStarted=0\`), and be different from the listed probable starter. Past starts cannot be counted as relief appearances.
- Records with unknown starter/reliever role or missing pitch counts are **omitted as incomplete**, not counted as zero. The response includes coverage warnings.
- Candidates are ordered by the **number of documented relief appearances**, with recency breaking ties. This ranking **is not a predictive reliever-appearance model** and must not be presented as one. It says nothing definitive about injury, rest status, bullpen decision-making, leverage role, handedness or suitability for tonight.
- The historical candidate IDs are sent back through the independently validated batter-vs-pitcher and workload research pipeline. Any disagreement on MLB game, hitter, starter or event start aborts the combined report.
- No model, sportsbook pricing, parlay probability, expected value or wager execution has been added. This component does not alter earlier frozen predictions or promote betting performance claims.

## Tests / rollout

\`\`\`bash
python -m unittest -v test_sports_mlb_reliever_candidates test_sports_mlb_auto_bullpen test_v2_19_3_37_mlb_auto_http
\`\`\`

Run the full existing GitHub Actions suite before merging; perform an independent publicly sourced pregame audit and a Render authenticated-route integration test after carefully switching \`TYLER_APP_MODULE\` to \`app_v2_19_3_37\`. Keep the previous module available for one-variable rollback. No actual sportsbook or wagers are involved.

**Next engineering stages:** pitcher handedness and pitch mix, bullpen leverage/availability from time-valid sources, expected plate appearances, independent calibrated player-prop hit/HR models, real pregame sportsbook quotes, correlated parlays and prospective grading. None of these are established by this historical research shortlist.
