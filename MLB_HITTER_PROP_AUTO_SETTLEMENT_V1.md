# Official-final MLB hitter shadow settlement (scheduled, NO BET)

This workflow gives a genuine pregame frozen research forecast a separately recorded final outcome **after official MLB final state**. The previously committed prediction file is immutable and never replaced.

- Python: \`sports_mlb_prop_settlement_job.py\`
- Tests: \`test_sports_mlb_prop_settlement_job.py\`
- GitHub Actions: \`.github/workflows/mlb_hit_shadow_auto_settlement.yml\`
- Source of truth: \`benchmarks/mlb_hitter_props_shadow_v1/predictions/<gamePk>_<hitterId>.json\`
- Results: \`benchmarks/mlb_hitter_props_shadow_v1/settlements/<gamePk>_<hitterId>.json\`

The scheduled GitHub workflow checks **once every three hours** (schedule can be delayed by GitHub; best-effort). It can also be manually dispatched. Every frozen forecast and existing final settlement is preflight-verified before
writing any new immutable result. The full inventory is limited to 30,000
saved predictions for bounded audit safety, but **not limited to 100 total
historical files**. The collector considers as-yet-unsettled forecasts whose
saved first pitch has passed, and checks at most **100 official player-games
per run**. If more are eligible, it divides them into stable earliest-first
windows and rotates the selected window by the three-hour UTC slot. This
ensures both old unresolved lines and later games remain retryable instead
of breaking or permanently starving the workflow after the hundredth saved
forecast. It reports the eligible-unsettled inventory, attempted checks,
explicit deferred count, and current window. Deferred records count as
pending, not as settled or official-final unresolved.

It ignores a forecast while its saved scheduled first pitch is still future,
or while the official status is not Final. A changed official start time or
game identity is never silently repaired or rewritten. If the official final boxscore lacks a hitter's `atBats`, `hits` or `homeRuns` count, or the entire batting field is absent/null, the collector explicitly reports that player-game and the missing field as unresolved, leaves the prediction unchanged and writes **no** immutable settlement for it. It retries when its bounded window next comes due; if more than 100 unsettled eligible records accumulate, some player-games may take multiple three-hour schedules to be revisited. It never assumes an absent field means zero or silently counts it as a loss. Unexpected non-integer values, inconsistent stat totals, identity conflicts and other malformed official data still fail closed. A code hotfix to the settlement modules also triggers a fresh workflow run.

For each final it validates the original SHA256 content digest, official game ID and scheduled start time, team identities and player ID, then reads official final batting counts. If the batter has 0 AB or is absent from the final boxscore, settlement is *ineligible for the conditional hit/HR event scoring*, not a loss. Otherwise it records separate 1+ hit and 1+ HR binary labels and squared Brier errors for the precise frozen probabilities.

The settlement step stages and commits **only new files beneath the settlement directory**, using GitHub's standard workflow token. A subsequent independently guarded step can refresh and commit **only** the mutable read-only `scoreboard.latest.json` if its benchmark changed, so settled outcomes become visible without relying on the next hourly schedule. No prediction files, application modules, wagers, sportsbook accounts, or production Render deployment variables are touched. The hourly publisher remains an independent fallback.

If a final's verified identity or start time differs from the freeze (e.g. reschedule), the job deliberately fails; do not guess or rewrite the original. If GitHub's organization or repository policy blocks workflow-token writes, the collector will report a permission failure, requiring an explicit repo-level decision. Pending runs should **not** be represented as successful final grading.

This is **not** a paid betting recommendation system. It does not use sportsbook odds, void/settlement policies, bookmaker line changes, or calibrated unconditional win probabilities. A handful of settled game outcomes would be insufficient to establish performance; accumulate many independent future events across diverse players and games.

Testing:

\`\`\`bash
python -m unittest -v test_sports_mlb_prop_prospective test_sports_mlb_prop_settlement_job
\`\`\`

Current inaugural pregame capture (Oct 15, 2026): \`849810_683734.json\` for Andrew Vaughn. Github server publish time for the frozen record was 2026-10-15T19:22:50Z, before its then-official 2026-10-16T00:00:00Z scheduled first pitch; original commit \`6f0ff689010578668a32d948794614314b198562\`.
