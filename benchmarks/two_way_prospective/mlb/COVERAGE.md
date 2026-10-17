# MLB forecast and odds coverage

**NO BET — actual wagers $0.**

Evidence through **2026-10-17T12:07:32.060307+00:00**; cohort began 2026-10-11T15:59:30.281973+00:00.

| Coverage | Games |
|---|---:|
| Recorded / settled / pending | 10 / 7 / 3 |
| Started games in retained official schedules / enrolled | 8 / 8 |
| Observed missing started games | 0 |
| Enrollment-time priced forecasts | 7 / 10 |
| Settled with enrollment prices / decisive market-paired | 5 / 5 |
| Separate later quotes recorded prospectively | 0 |

## Missing enrollment-time prices

| Game | Matchup | Settled | Enrollment evidence | First later archived pregame pair (UTC) |
|---|---|---|---|---|
| 849808 | MIL at LAD | False | no provider odds | Unavailable |
| 849812 | LAD at MIL | True | no usable pair in reduced snapshot raw schema unavailable | 2026-10-12T07:21:49.547508+00:00 |
| 849813 | CLE at TB | True | no usable pair in reduced snapshot raw schema unavailable | 2026-10-13T07:43:09.630071+00:00 |

Later archived pairs explain timing gaps; they are not retrospectively inserted into forecasts or scored market comparisons.

## Next 24-hour pregame readiness

As of retained evidence: 2026-10-17T12:07:32.060307+00:00. Ready: 1 / 1 observed games. Status: ready_as_of_snapshot.

| Game | Matchup | Enrollment priced | Separate follow-up | Latest pair | Issues |
|---|---|---|---|---|---|
| 849816 | Tampa Bay Rays at Cleveland Guardians | True | False | True | None |

Latest audited capture only; source changes after retrieval are unknown. This does not certify future collection or wagering readiness.

## Schedule audit

| Game | Matchup | Start (UTC) | Decision | Exclusion evidence |
|---|---|---|---|---|
| 849808 | Milwaukee Brewers at Los Angeles Dodgers | 2026-10-17T01:00:00+00:00 | enrolled | — |
| 849809 | Los Angeles Dodgers at Milwaukee Brewers | 2026-10-12T00:00:00+00:00 | enrolled | — |
| 849810 | Milwaukee Brewers at Los Angeles Dodgers | 2026-10-16T00:00:00+00:00 | enrolled | — |
| 849811 | Milwaukee Brewers at Los Angeles Dodgers | 2026-10-15T00:00:00+00:00 | enrolled | — |
| 849812 | Los Angeles Dodgers at Milwaukee Brewers | 2026-10-12T21:00:00+00:00 | enrolled | — |
| 849813 | Cleveland Guardians at Tampa Bay Rays | 2026-10-14T00:00:00+00:00 | enrolled | — |
| 849816 | Tampa Bay Rays at Cleveland Guardians | 2026-10-18T00:00:00+00:00 | enrolled | — |
| 849818 | Tampa Bay Rays at Cleveland Guardians | 2026-10-15T17:00:00+00:00 | enrolled | — |
| 849820 | Cleveland Guardians at Tampa Bay Rays | 2026-10-13T00:00:00+00:00 | enrolled | — |

## Capture freshness

Audited capture manifests: 46. Latest: `20261017T120728150537Z`.

| From (UTC) | To (UTC) | Hours between audited captures |
|---|---|---:|
| 2026-10-16T23:36:15.539073+00:00 | 2026-10-17T12:07:28.150537+00:00 | 12.52 |
| 2026-10-12T07:21:47.631288+00:00 | 2026-10-12T17:55:09.207430+00:00 | 10.56 |
| 2026-10-13T07:43:07.278901+00:00 | 2026-10-13T15:59:37.046408+00:00 | 8.27 |
| 2026-10-13T00:41:35.771663+00:00 | 2026-10-13T07:43:07.278901+00:00 | 7.03 |
| 2026-10-12T00:32:40.669978+00:00 | 2026-10-12T07:21:47.631288+00:00 | 6.82 |

Historical exclusions and collector errors, including resolved ones, are retained in [COVERAGE.json](COVERAGE.json); these are not all current errors.

[Scoring review](REVIEW.md) · [Machine-readable coverage](COVERAGE.json)

Coverage is limited to retained official schedule snapshots since each cohort began; it cannot prove that a source returned every game or recover uncaptured runs. Capture gaps are observed intervals, not proof of scheduler failure. Later archived pregame prices are evidence only: they never backfill saved forecasts or enrollment-time market metrics. New follow-up quotes must be recorded before start, remain separate, and are not added to existing scored comparisons. NO BET / actual wagers $0.
