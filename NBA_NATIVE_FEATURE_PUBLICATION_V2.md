# Native daily feature publication evidence

The first two real native-daily feature files were frozen at
2026-10-21T12:07:16.005953+00:00 by committed recipe
`333f744544eb2a4e4bf05a94b76eae9815323d3b`. Their original source receipt is
`20261021T100534161148Z`. Game `0022600006` has both saved starts at October 22
23:00 UTC; `0022600007` has both at October 23 01:30 UTC. Original source and
historical-reference replay accepted both; no target was withheld.

The first collection attempt correctly wrote no files because a new reference-ID
check wrongly excluded playoff references permitted by the unchanged sealed
reference policy. The committed correction and regression preserve previous-season
regular/playoff references and regular-only targets. The successful observation
freeze above is the actual later collection clock, never the failed attempt's
clock. No forecast or source timestamp was rewritten.

These two game IDs already occur in the sixteen-record v1 feature cohort.
They are separate versioned observations and cannot be pooled as two additional
independent games. Both remain features, not forecasts, with zero outcomes,
accuracy computation, training, historical evaluation, promotion or wagers.

`sports_nba_native_feature_publication.py` separately replays the new protocol,
original native/ESPN bytes, historical seals and frozen feature files before
querying GitHub. The specified integrated-regression run must belong to this
repository, be a pull-request or push event, and have a server creation time
at/after every original freeze and before both saved starts. Exact committed
file metadata, Git/SHA-256 hashes and decoded bytes must agree with each source-
replayed original file at that immutable head.

Use `--run-id ID` to inspect a real integrated-regression run or `--replay PATH`
to freshly verify a retained recipe. Explicit original cohort IDs prevent later
records from being attributed to an earlier run. A saved recipe always requires
fresh GitHub API replay; offline fixture tests are not live server evidence.
No public-repository visibility, source-origin or actual-tipoff certification
is asserted. Existing v1 publication evidence and default reader behavior remain
unchanged. NO_BET=true, actual wagers zero, promotion disabled.
