# Frozen NBA feature cohort lifecycle

`sports_nba_feature_cohort.py` replays all original feature records and their
source seals before inspecting the latest retained NBA and ESPN observations.
The latest ESPN capture is read independently of the older ESPN capture linked
inside the most recent NBA receipt. Original feature files are never changed.

For each frozen identity the report retains original starts, later source starts,
signed drift in minutes, the original record digest and current source-row hashes.
Aggregate provenance includes capture IDs, original manifest/response digests,
observation times and source age. An observation older than 12 hours is marked
explicitly; stale pregame status cannot establish that a game is still pregame.
The clock-based `original_saved_start_reached` flag does not establish actual tipoff.
A missing game does not imply cancellation or justify substituting another ID.

An attached result requires the frozen NBA and ESPN IDs, both teams and their
orientation, ESPN team IDs, regular-season scope, the unique current crosswalk,
and agreeing final scores. Both final observations must follow original and
latest saved starts and the feature freeze. Changed identities, ambiguous repeat
fixtures, postponement, one-sided finals and conflicting scores remain pending.
Source corruption or future timestamps fail the audit rather than becoming
missing data. A legitimate later schedule shift is shown separately; it never
rewrites the original feature freeze or original starts.

These are source result observations associated with feature records, not graded
predictions. The module computes no prediction accuracy, model fit or betting
performance. It does not reattest publication chronology or actual tipoff.
The separately replayable publication report retains its own narrower proof.
NO_BET remains true, wagers zero, and training, evaluation, forecasting and
promotion remain disabled.

The scheduled source workflow runs this read-only audit after provider replay,
even if new NBA acquisition failed. It uploads a lifecycle artifact and includes
`NBA_FEATURE_COHORT_AUDIT` in its source-status receipt. A successful cohort replay
does not imply fresh NBA acquisition; source ages and step outcomes remain visible.
The archived-receipt workflow also runs the audit and its regression tests.

```sh
python sports_nba_feature_cohort.py
```
