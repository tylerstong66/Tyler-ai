# MLB 1+ hit and 1+ HR shadow baseline v1

**Status: experimental, not deployed, NO BET.** This phase begins calibration and benchmarking separately from the already-live v2.19.3.38 matchup research. It does **not** compute a sportsbook-ready hit or HR probability.

## What is modeled

Using the official MLB StatsAPI \`gameLog\` endpoint, the model selects prior *regular-season games* for an identified hitter, checks per-game \`gamePk\`, player identity, season, game type and date, and freezes a fixed 80-game rolling window with at least 30 games. Every observed game must include at least one official at-bat to qualify. It records two binary outcomes: 1+ hit and 1+ home run.

The experimental probability for each event uses a **fixed, preregistered 20-pseudo-game prior** (0.60 for 1+ hit; 0.08 for 1+ HR) and the last up to 80 eligible games. Both priors are exploratory references, **not** derived from a verified market or established optimal models. Neither rate accounts for expected at-bats, actual lineup or starter appearances, individual pitching matchups or reliever use.

\`\`\`text
p_event = (recent_event_games + 20 * fixed_prior) / (eligible_recent_games + 20)
\`\`\`

The prediction is ***conditional on the batter recording at least one official at-bat***. A sportsbook's settlement rules may treat zero-at-bat, no-start, substitutions, pinch-hitting, voids and delays differently. This estimate is NOT suitable for wager analysis.

## No hindsight or doubleheader leakage in computations

The forecaster uses only game logs whose **local game date is strictly earlier than the forecast game's Eastern date**; it never uses other games on the same day, even for a doubleheader. The retrospective evaluator replays each day's games as a fixed block. This ensures no label from the target or any same-day games is used as a training feature.

**However:** the current public MLB API can be queried today for historical game logs, and the service does not independently archive the data as it existed at every historical cutoff. Therefore the replay is labeled ***retrospective chronological diagnostics, not genuinely frozen prospective validation***.

Models are not adjusted after inspecting the target results. Report Brier and log loss for hit and HR against the fixed prior comparators; do not convert numerical differences into a claim of edge. At least hundreds of genuinely frozen, independently settled pregame forecasts and market quotes with appropriate uncertainty analysis will be required before any betting-value assertion.

## Run (read-only)

\`\`\`bash
python -m unittest -v test_sports_mlb_hit_prop_shadow
python sports_mlb_prop_shadow_diagnostics.py --hitter-id 683734 --season 2026 --event-start 2026-10-15T23:00:00Z
\`\`\`

The example game time is historic and only demonstrates arguments. For a current use, supply the **actual future scheduled** start time, verified separately against official MLB event ID. The diagnostic outputs source receipts and the retrospective report; it places no bet and modifies no sports prediction ledger or deployed Tyler runtime.

## Next phase

1. Validate the diagnostic on several predeclared hitters from multiple teams using source-recorded game logs, and measure sample count and Brier/log losses separately for 1+ hit and 1+ HR.
2. Improve the baseline: use as-of verified probable lineup, expected at-bat distribution, pitch mix, reliever-specific exposure and uncertainty; distinguish *conditional* from *unconditional* probability and handle sportsbook void rules.
3. Build a pregame timestamped append-only shadow ledger, save source digests and exact model version, settle against official boxscores, and grade actual prospective performance and closing-line value. Never claim a proven betting edge based on retrospective diagnostics alone.
4. Only after independent validation, add appropriately labeled read-only output to Tyler chat; the current v2.19.3.38 production logic remains untouched.
