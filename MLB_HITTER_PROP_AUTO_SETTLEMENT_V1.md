# Official-final MLB hitter shadow settlement (scheduled, NO BET)

This workflow gives a genuine pregame frozen research forecast a separately recorded final outcome **after official MLB final state**. The previously committed prediction file is immutable and never replaced.

- Python: \`sports_mlb_prop_settlement_job.py\`
- Tests: \`test_sports_mlb_prop_settlement_job.py\`
- GitHub Actions: \`.github/workflows/mlb_hit_shadow_auto_settlement.yml\`
- Source of truth: \`benchmarks/mlb_hitter_props_shadow_v1/predictions/<gamePk>_<hitterId>.json\`
- Results: \`benchmarks/mlb_hitter_props_shadow_v1/settlements/<gamePk>_<hitterId>.json\`

The scheduled GitHub workflow checks **once every three hours** (schedule can be delayed by GitHub; best-effort). It can also be manually dispatched. Only existing, verified pregame forecasts are considered, up to 100 per run. It ignores a forecast while its event is not final and reports pending status.

For each final it validates the original SHA256 content digest, official game ID and scheduled start time, team identities and player ID, then reads official final batting counts. If the batter has 0 AB or is absent from the final boxscore, settlement is *ineligible for the conditional hit/HR event scoring*, not a loss. Otherwise it records separate 1+ hit and 1+ HR binary labels and squared Brier errors for the precise frozen probabilities.

The workflow stages and commits **only new files beneath the settlement directory**, using GitHub's standard workflow token. No prediction files, application modules, wagers, sportsbook accounts, or production Render deployment variables are touched.

If a final's verified identity or start time differs from the freeze (e.g. reschedule), the job deliberately fails; do not guess or rewrite the original. If GitHub's organization or repository policy blocks workflow-token writes, the collector will report a permission failure, requiring an explicit repo-level decision. Pending runs should **not** be represented as successful final grading.

This is **not** a paid betting recommendation system. It does not use sportsbook odds, void/settlement policies, bookmaker line changes, or calibrated unconditional win probabilities. A handful of settled game outcomes would be insufficient to establish performance; accumulate many independent future events across diverse players and games.

Testing:

\`\`\`bash
python -m unittest -v test_sports_mlb_prop_prospective test_sports_mlb_prop_settlement_job
\`\`\`

Current inaugural pregame capture (Oct 15, 2026): \`849810_683734.json\` for Andrew Vaughn. Github server publish time for the frozen record was 2026-10-15T19:22:50Z, before its then-official 2026-10-16T00:00:00Z scheduled first pitch; original commit \`6f0ff689010578668a32d948794614314b198562\`.
