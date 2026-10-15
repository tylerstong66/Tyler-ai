# Daily MLB hitter shadow capture — automated and no wagering

This provides a larger *prospective* sample than a single Andrew Vaughn prediction. The scheduled GitHub Action runs once each day (14:23 UTC; GitHub can delay it) and considers only officially scheduled **upcoming games on the current US Eastern calendar date**. It requires at least 45 minutes to scheduled first pitch when selecting a game, and the publication guard requires at least 3 minutes to first pitch when committing. It does **not** read live market odds or place wagers.

For each eligible official MLB game, select up to three nonpitchers per club by **ascending numeric MLB player ID from the official active roster**, before reading any hitter outcomes. This is an arbitrary but reproducible population, not a confirmed batting lineup. It favors veteran IDs and does not represent a statistically random baseball sample.

For each player, independently verify game, roster and team IDs, obtain regular-season game logs from current/prior seasons, and freeze the experimental 1+ hit and 1+ HR conditional game estimates when at least 30 eligible prior games exist. Every resulting per-player file is SHA256-sealed and created only if the file did not already exist. Existing predictions are checked for tampering and are **never overwritten**.

The runner adds **only** new predictions under \`benchmarks/mlb_hitter_props_shadow_v1/predictions/\`. A separate, previously installed scheduled collector reads official finals and writes settled outcomes under \`.../settlements/\` without mutating original forecasts. Thus capture and settlement operate independently.

The GitHub Actions workflow uses a standard scoped repository token for write-back. If repo permissions prohibit GitHub Actions pushes, the attempt will fail visibly; there is no hidden fallback or claim of a successful save. Before publishing, the exact staged file list is verified, every digest is checked and current UTC time must still be at least three minutes before all staged first pitches. Runner scheduling is best-effort, not guaranteed.

## Initial manual test

The workflow also runs once when the workflow file is updated on the main branch, allowing a pregame write-back test. It may legitimately create no predictions if no games qualify or the cutoff window has passed.

## Limits

- No confirmed batting order, guaranteed player appearance, or modeled chance of recording at least one at-bat.
- No calibrated unconditional 1+ hit or home-run prop probabilities, bookmaker odds or correlated parlay values.
- No actual wagers or settlement of real-money sportsbook tickets.
- No data from later game outcomes is used when freezing a new pregame record.
- Each later outcome is stored in a separate result file; only *eligible games with at least one at-bat* count for this deliberately conditional forecast experiment.

Unit tests:

\`\`\`bash
python -m unittest -v test_sports_mlb_prop_batch_capture test_sports_mlb_prop_prospective
\`\`\`

Tracking model performance will require many independently frozen official pregame player-game records, and proper grade summaries across teams, months and seasons. Actual model superiority remains unproven.
