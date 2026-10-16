# Tyler MLB benchmark scoreboard — GitHub feed and authenticated chat v2.19.3.39

The existing frozen MLB 1+ hit/HR model predictions and official settlements live in GitHub. Render auto-deployment is disabled, and GitHub's automated captures/settlements update the repository separately from Render. Reading only Render's local checkout would silently show an outdated scorecard. This upgrade solves that problem **without Slack, a new provider account, or sportsbook credentials**.

## Published read-only feed

The GitHub Actions workflow \`.github/workflows/mlb_shadow_scoreboard_publisher.yml\` runs once per hour (best effort; GitHub Actions cron can be delayed), reads the original sealed prediction and settlement files through \`official_shadow_scoreboard\`, and publishes a compact \`scoreboard.latest.json\` under the benchmark directory **when saved benchmark evidence changes, or after at least two hours of unchanged evidence to refresh the read-only feed heartbeat**. It never modifies the frozen predictions, original published commitments or official settlement files.

The file has a canonical report SHA-256, a GitHub input source commit hash, publication time, counts for pending/scored/ineligible records, distinct games, metrics against the fixed reference, and explicit limitations.

**Freshness is not new evidence.** `published_at_utc` is when the research
feed was last written or heartbeat-refreshed. The new
`benchmark_last_changed_at_utc` preserves the time that the actual saved
benchmark contents most recently changed. The separate `source_refresh_kind`
explicitly distinguishes `benchmark_changed` from
`unchanged_saved_evidence_heartbeat`; the reader exposes separate
`snapshot_age_hours` and `benchmark_age_hours` and accepts older feeds
that do not have those optional metadata fields.

A no-change heartbeat is **not** a new official MLB final, a live API fetch,
a verified market quote or independent proof of pregame publication. It means
the saved repository's official settlement and prediction ledger was
recomputed and was still unchanged. Pending hitters remain pending, and
GitHub cron delay may still make the feed appear stale.

The public snapshot URL used by Tyler is fixed:

\`\`\`text
https://raw.githubusercontent.com/tylerstong66/Tyler-ai/main/benchmarks/mlb_hitter_props_shadow_v1/scoreboard.latest.json
\`\`\`

The authenticated Tyler application v2.19.3.39 reads and checks the public JSON at request time instead of trusting the deployment snapshot. It validates the source URL, content digest, counts, no-wager status and publication age. If the file is missing, inconsistent or inaccessible, it returns an explicit unavailable error rather than a fabricated score.

## Tyler chat command

Once the application version is deliberately activated in Render by setting \`TYLER_APP_MODULE=app_v2_19_3_39\`, use:

\`\`\`text
sports mlb shadow scoreboard
\`\`\`

The command returns read-only current published GitHub counts, Brier/log-loss for settled conditional-at-bat predictions (when available), as-of age and a stale-feed warning. It still does not compute true unconditional sportsbook player props or make betting recommendations.

This is a **scheduled snapshot**, not the live state of the MLB API. It may lag official finals and GitHub Actions writes by hours. Exact git commit history and source timing remain independently reviewable; the feed SHA-256 is an integrity check, not independent proof of when GitHub received a prediction.

## Checks and rollout

\`\`\`bash
python -m unittest -v test_sports_mlb_prop_scoreboard_feed test_v2_19_3_39_mlb_scoreboard_http
\`\`\`

After all GitHub PR checks pass, merge and verify the publisher creates an initial snapshot in the actual repository. Only then activate the Render version, and verify the public \`/status\`, \`/health\`, anonymous HTTP 401 and modeled authenticated route tests. No live authenticated request with the user's personal key is necessary to activate this report.

If the public snapshot becomes older than four hours, Tyler shows \`snapshot_may_be_stale=true\`. No wagering or model promotion is performed, and the live athlete research commands remain in place.
