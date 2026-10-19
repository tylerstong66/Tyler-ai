# Source-backed FBS pregame reference observations

The separate digest-pinned FBS protocol freezes four corroborated previous-season
results per team as reference features for future 2026 regular-season targets.
It does not borrow NBA/NFL coefficients, fit a model or create predictions.
The target league is the retained FBS source cohort; institutional membership
is explicitly not certified, including possible visiting lower-division schools.

The first five records froze at 2026-10-19T18:31:11.792063Z before saved starts
from October 20 at 23:00 UTC through October 22 at 23:30 UTC. The targets are
Memphis–East Carolina, App State–James Madison, Florida International–Middle
Tennessee, Delaware–Missouri State and Marshall–South Alabama. Both source
archives, the original crosswalk and original prior-season final evidence are
replayed. A second collection verified five existing records, wrote zero new
records and preserved their exact bytes.

`benchmarks/fbs_pregame_reference_features_v1/protocol.json` is pinned in code:
`230e8833affe1346fe2e349e92f2c3bc64ac1db85fe5b16bb236ab8d9cde721e`.
Changing the window, reference scope or protocol requires a separately versioned
experiment. The 2025 validation-source cohort is isolated from 2026 targets.
References use actual retained receipt availability; hypothetical kickoff-plus-
24-hour availability is never substituted in these prospective observations.

The collector requires one-to-one original NCAA/ESPN identity, positive game and
team IDs, both sources in pregame states, ESPN's explicit `STATUS_SCHEDULED`,
regular-season scope, fixed 2026 NCAA request URLs and a freeze before both
saved starts. Both source captures and the original crosswalk must precede the
freeze, and neither source may be older than 12 hours. Delayed, postponed,
missing, conflicting or unknown ESPN status cannot count as scheduled.

Historical references require the same ESPN team ID and exact normalized
provider display name; unknown name changes stay unenrolled. Selected last-four
references must be unique, source-corroborated, within the fixed season/sport
and available by the freeze. The report retains each full original source row
and digest, original target IDs/starts, crosswalk/source capture hashes and
protocol/reference report digests. Current target outcomes never enter features.

The features are prior-game count, mean points for/against/margin and days since
the latest reference start. These are previous-season reference summaries:
current-season form and prior-season roster/coach changes are not modeled.
They are not an assessment of current team strength or calibrated probabilities.

Default execution is read-only. Collection uses exclusive file creation and
verifies every existing record before preparing any new writes. Rehashed edits
cannot bypass a fresh replay, including integer/boolean guard substitutions.
Source files must be bounded regular files; source corruption fails the whole
preflight. Later snapshots and postgame audits never rewrite original records.

```sh
python sports_fbs_pregame_features.py            # read-only audit
python sports_fbs_pregame_features.py --collect  # append eligible original observations
```

The scheduled source workflow collects only after a valid NCAA/ESPN crosswalk,
stages records only after successful preflight and reports `FBS_FEATURE_OBSERVATIONS`
in its source-status receipt. Archived CI replays the cohort without creating
records. Original files decline independent publication-time attestation; that
requires a separate server chronology audit. No fitting, evaluation, forecasting,
model activation, promotion, odds, accuracy grading or wagers are enabled.
NO_BET remains true, actual wagers zero.
