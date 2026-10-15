# MLB hitter shadow cohort retrospective v1

**No wagering. Not deployed to Tyler AI.** This module evaluates the already-existing 1+ hit / 1+ home run conditional on 1+ official at-bat baseline across a deliberately selected group of hitters, rather than relying only on Andrew Vaughn.

## Reproducible convenience cohort

Example diagnostic:

\`\`\`bash
python sports_mlb_prop_cohort_diagnostics.py --game-id 849810 --season 2026 --per-side 5
\`\`\`

That game ID is an October 15, 2026 fixture and may stop working once the game begins. The CLI selects the **lowest numeric official MLB player IDs among non-pitchers** on the two teams' public active rosters, up to a specified number on each side. It does this *before* retrieving any hitter game logs. This ranking is arbitrary but reproducible and avoids manually selecting only hitters with favorable backtests. It may favor established veteran players and is **not representative of MLB hitters**.

For each selected player, retrieve official 2025 and 2026 regular-season per-game logs and replay the 2026 games using strictly earlier local-date game outcomes. Evaluate 1+ hit and 1+ HR game binary events on games with 1+ official AB, excluding same-day doubleheader results from predictor history.

## Comparison and limits

The baseline probabilities are the original untuned fixed references (0.60 for conditional 1+ hit and 0.08 for conditional 1+ HR), versus the predeclared smoothed 80-game rolling frequency predictor. Brier and log loss are reported per hitter and pooled, weighted by the number of eligible recorded player-games.

**A lower Brier score is not enough to establish value, and even a winning cohort is not an independently frozen prospective test.** These official historical gameLogs are downloaded after the fact. No prop settlement rules, lineup nonappearance, same-game correlations, pricing, bookmaker vig, weather or pitcher-specific exposures are modeled. More importantly, the cohort is selected using today's active rosters, so a survivor/sample selection effect remains. No confidence interval or proven superiority claim is supplied.

Safeguards:

\`\`\`bash
python -m unittest -v test_sports_mlb_prop_cohort test_sports_mlb_prop_cohort_diagnostics
\`\`\`

The deployment stays at the most recent independently verified research-only version. The next requirement for credible performance claims is a prospectively frozen append-only player-event ledger, with pregame timestamps, official game and hitter IDs, source content digests, label definitions, model version, and later official final-state settlement.
