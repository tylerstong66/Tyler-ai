# Separate 2024 training / 2025 validation source seasons

**Strict research evidence acquisition only. No forecasts, wagers, performance claims, live deployment, or model promotions.**

This cohort is wholly separate from prospective original NFL/NHL/MLB
forecasts, and from the 2026 FBS/men's college hoops/NBA source snapshots
under `college_nba_source_v1`.

| League | Retrospective training request window | Unseen validation request window |
|---|---|---|
| NBA | 2024-10-22 through 2025-06-22 | 2025-10-21 through 2026-06-23 |
| NCAA FBS football | 2024-08-24 through 2025-01-21 | 2025-08-23 through 2026-01-20 |
| NCAA Division I men's basketball | 2024-11-04 through 2025-04-08 | 2025-11-03 through 2026-04-07 |

The `sports_expansion_historical_capture.py` retriever issues bounded
calendar-day ESPN requests with league-specific groups and a 500-event
cap. It captures **up to 20 new calendar days per league per scheduled
run**, at most 60 total requests; previous receipts are reverified
against original gzip SHA256 source bytes and normalized scoreboard
before any further writes. All requests in the selected batch are
parsed and validated before writing any new files. Repeated jobs skip
already sealed days; no original snapshot can be changed or silently
overwritten. Provider errors or truncated slates fail the batch. Before any network
requests, the collector also rejects unplanned files, missing halves of a
sealed source receipt, unexpected calendar dates, overlapping or unordered
training/validation partitions, modified SHA digests, and saved observation
timestamps later than the current audit clock. The increased collection
budget does not loosen those immutability or timing checks.

A three-times-daily GitHub Actions job
(`college_nba_history_source.yml`) incrementally retains these dated
source receipts. `COVERAGE.latest.json` exposes requested/retained
calendar days by league and is not a claim that every actual NCAA or
NBA event was present in the provider response. Zero-event days are
still source-observed dates, not proof of no games; postponements,
provider schedule changes and unknown dates require separate analysis.

**Future research gate:** Full closed-season source coverage, explicit
game-ID and timing integrity, independent official-result corroboration,
and deterministic per-sport chronological leakage checks must all pass
before any training/validation results become accepted. The 2025
validation season may not be used to tune a 2024-fitted candidate
after examining its results. Same-season retrospective guesses may not
be recorded as historical pregame paper forecasts. The 2026-27
prospective experiments may enroll only new future games with original
immutable pregame freeze timestamps.

This collector sets `training_allowed=false`,
`live_forecasts_allowed=false`, `historical_backfilled_forecasts=0`,
`NO_BET=true`, `actual_wagers=0` and
`promotion_allowed=false` until a separate evidence-reviewed phase.

## Historical archive resource and safety bounds

Historical receipt replay now uses the same streaming 8 MB decompression bound
as current-season source audit and rejects compressed files above 8.5 MB.
Truncated gzip and expansion bombs fail before any outbound acquisition or new
batch writes. Replay also enforces integer zero wagers, promotion disabled and
provider-only official-result status from every existing receipt. Original
archives are never repaired or overwritten by these checks.

## Separate NBA exact-tipoff identity replay (October 19)

`python sports_historical_nba_crosscheck.py --exact-tipoff-identity --split train`
(and `--split validation`) produces the separate
`tyler-historical-nba-exact-tipoff-crosscheck-v2` report. Original v1 replay and
all source receipt bytes remain unchanged. When repeated home/away fixtures
fall within 72 hours, this policy requires one exact UTC tipoff match and no
other same-home/away fixture within 30 minutes. It never uses scores, winners,
nearest-time ranking or outcome quality to select a game. Existing final,
season, postponement, one-to-one identity and postgame observation checks apply.

At the October 19 checkout, the separate policy replays 1,310 training and
1,315 validation two-source final agreements, versus 1,185 and 1,203 under v1.
The remaining unmatched observations stay excluded. These are postgame source
agreements, not historical pregame predictions, accepted training data, schedule
completeness or betting performance. CI publishes both policy outputs separately.
