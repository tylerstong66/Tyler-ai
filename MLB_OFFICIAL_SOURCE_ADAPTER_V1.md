# Official MLB matchup source adapter v1

This adapter is **research only / NO BET**. It collects MLB StatsAPI pregame game identity, active-roster identities, the listed **probable** opposing starter, optional manually nominated potential relievers, and available historical \`vsPlayerTotal\` batting counts. It passes validated inputs into \`sports_mlb_matchups.analyze\`. It never offers a player-prop probability, calculates betting expected value, executes wagers, or modifies the frozen team-level benchmark.

## Run

\`\`\`bash
python -m unittest -v test_sports_mlb_sources test_sports_mlb_matchups
python sports_mlb_sources.py 849831 10001 --hitter-side away --reliever-id 30001
\`\`\`

IDs in the illustrative command are test placeholders; no valid real matchup is implied. The CLI requires access to the public MLB StatsAPI and will fail closed for unknown, in-progress, started, or settled games.

Data comes only from fixed-origin, bounded HTTPS requests to \`https://statsapi.mlb.com/api/v1/\` for rosters, schedule and hitter stats, and \`https://statsapi.mlb.com/api/v1.1/\` for game feeds, with redirects disallowed. Each response gets a content digest, retrieval timestamp and exact request URL. The reader confirms the official game ID, schedule start and pregame state, the hitter's active-roster membership and the pitchers' active-roster positions. It does **not** treat the active roster as a published batting order or a probable starting pitcher as a confirmed starter.

Historical counts use explicit \`vsPlayer\` per-season splits for the current and preceding regular seasons, rechecking each split's season and game type. The October 15 live audit found that MLB may ignore these URL query filters and return other seasons/types; unscoped \`vsPlayerTotal\` is never used. Missing and duplicate rows fail closed. A missing pitcher matchup remains missing, not zero. The output preserves collection receipts for all seasons.

Important caveats:
- MLB StatsAPI's current aggregates do not provide their exact original publication time. Those captures are valid only for the moment retrieved; never backdate their availability for historical simulations.
- Every pregame request must finish before first pitch. A postponed or rescheduled event needs fresh analysis with current official identity.
- Historical starter matches alone have small sample sizes and are **not** predictive player-prop probability estimates.
- Relievers are explicitly nominated candidates, *not* inferred or projected to enter a game. Rest days, bullpen usage, availability, handedness, pitch mix and game script remain unknown.
- Regular season and postseason pregame contests are accepted, but the historical stat window currently includes only regular-season data.
- Actual run against the live third-party API and chronological prospective player-prop validation are pending separate checks.

Next: validate actual StatsAPI payload compatibility against real captures; add independently sourced candidate/usage evidence with known-as-of timestamps; then integrate a human-readable authenticated Tyler chat workflow in research-only mode.

## Live-source schema audit

A GitHub-hosted audit on October 15, 2026 confirmed both problems: the MLB source returned multiple season/game-type splits despite query filters; a sampled 2024 historic `v1` game feed was HTTP 404 while `v1.1` returned an official final and bullpen boxscore. See [audit run](https://github.com/tylerstong66/Tyler-ai/actions/runs/38771616758). These findings prompted the per-split filtering and game-feed version correction; they are not an end-to-end proof of live pregame functionality.
