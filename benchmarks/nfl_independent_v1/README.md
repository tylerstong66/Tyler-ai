# Independent NFL baseline v1

This is an **offline, retrospective benchmark**, separate from Tyler's live
paper cohorts and behavioral Sports Betting Analyst benchmark. It neither
imports the application nor writes its ledger. The candidate stays **NO BET**
and is **not promoted to production**: its held-out probability scores trail
the historical market comparison.

## Frozen source and evaluation

`games_2010_2025.csv` contains 4,363 schedule/result rows (regular season and
postseason), reduced to the 13 necessary columns from Lee Sharpe's nflverse
schedule data. `protocol.json` pins the upstream commit, source URL, download
time, raw SHA-256 and subset SHA-256. The source is
[nflverse/nfldata](https://github.com/nflverse/nfldata); field definitions are
in the [schedule dictionary](https://nflreadr.nflverse.com/articles/dictionary_schedules.html).
The original download is 2,184,004 bytes; the reduced snapshot is 311,936 bytes.
No network, app credentials, LLM or extra Python package is needed to reproduce.

| Role | Seasons | Regular-season games |
| --- | --- | ---: |
| Rating/history warm-up | 2010–2013 | 1,024 |
| Coefficient training | 2014–2022 | 2,335 |
| Regularization selection | 2023–2024 | 544 |
| Refit with selected regularization | 2014–2024 | 2,879 |
| Held-out sequential evaluation | 2025 | 272 (271 decisive, 1 tie) |

The protocol was saved at 2026-10-11T13:25:34.480990+00:00 before the first
test score. Three positive L2 penalties (0.001, 0.01, 0.1) were compared by
conditional log loss on validation seasons only. The selected penalty is
0.001. Coefficients are refit using training plus validation and written to
`model.json` before test metrics are computed. This is a held-out historical
season, **not a blinded or prospective experiment**; the source snapshot is
retrospective and contains test results.

## Independent features and cutoff rules

The fitted logistic regression receives an intercept and four features:

- Prior-game Elo rating difference, scaled by 200. Both teams start at 1500;
  K is fixed at 20. Expected rating updates use a fixed 55-point home venue
  adjustment, removed for neutral games. Ratings regress one third toward
  1500 at season boundaries. Franchise relocations OAK/LV, SD/LAC and STL/LA
  retain their identity.
- Home venue indicator, zero at a publisher-designated neutral venue.
- Difference in rest derived from prior games, scaled by 7 days. Individual
  rest is capped to 3–14 days; offseason gaps over 30 days use a neutral 7-day
  input rather than treating offseason length as a rest advantage.
- Difference in each team's mean scoring margin over its last eight eligible
  games, scaled by 14 points. The history carries across season boundaries.

Features are generated in kickoff order, with a cutoff one second before
kickoff. Every prior final is held in a pending queue until kickoff plus 24
hours. Simultaneous games cannot consume one another's results. Postseason
results update history but are not fitted or scored as regular-season targets.
Earlier test-season results may update Elo/history after their assumed
availability; model coefficients and tie probability remain fixed throughout
the test. This is sequential forecasting rather than a single preseason forecast.

Historical exact final publication timestamps are unavailable in the snapshot.
The 24-hour availability delay is a conservative **assumption**, not proof of
the information present at the historical cutoff. Schedule, venue and final
score corrections may also be retrospective. The row audit records cutoff,
latest assumed available result and number of prior results used.

Market moneylines, current-game scores, retrospective quarterback identities,
weather observations and precomputed rest fields are excluded from feature
inputs. Moneylines appear only in the evaluation layer. Injury effects are
disabled. The `verified_observations` adapter rejects observations without a
verified publication timestamp and retrieval timestamp preceding the cutoff;
it is a gate for future sourced injury work, not a fitted v1 feature. Missing
injury data cannot be interpreted as a healthy roster.

Tie probability is the smoothed historical tie rate from the development
seasons: (ties + 0.5) / (games + 1), equal to 0.0036458333333333334. This is
a fixed baseline tie prior, not an injury-dependent or game-specific tie model.

## First held-out result

| Measure | Independent baseline | Historical market comparison | Constant home-rate baseline |
| --- | ---: | ---: | ---: |
| Correct decisive picks | 175/271 (64.6%) | 177/271 (65.3%) | Not reported |
| Paired two-outcome Brier (lower is better) | 0.442313 | 0.424278 | 0.497192 |
| Paired conditional log loss (lower is better) | 0.631442 | 0.609383 | 0.690338 |

All 271 decisive test games have valid paired prices. The tied game is excluded
from two-way market comparisons and pick accuracy, and retained in the full
three-outcome score. Full candidate Brier across all 272 games is 0.446264;
full three-outcome log loss is 0.653400. Two-way historical moneyline implied
probabilities are normalized proportionally to remove margin. Bookmaker,
quote time, executable-price status and closing-line status are unverified.
No hypothetical ROI or closing-line value is calculated from these prices.

Mean candidate-minus-market Brier is +0.018035 (positive means worse).
A deterministic 2,000-draw week-block bootstrap across 18 weeks gives an
approximate 95% interval of +0.002852 to +0.033832. This is a descriptive
single-season interval with limited dependence modeling, not proof of future
performance. Confidence bins are in `report.json`; small-bin deviations must
not become after-the-fact tuning rules.

## Run and verify

From the repository root:

```bash
python -m unittest -v test_sports_historical_benchmark.py
python sports_historical_benchmark.py \
  --snapshot benchmarks/nfl_independent_v1/games_2010_2025.csv \
  --protocol benchmarks/nfl_independent_v1/protocol.json \
  --output /tmp/tyler-nfl-new-run
```

Output directories must be new; existing runs cannot be overwritten. The
snapshot hash must match the protocol. The saved outputs are:

- `run_2026_10_11/model.json`: frozen coefficients and model metadata.
- `run_2026_10_11/report.json`: exact metrics, validation selection and limits.
- `run_2026_10_11/test_predictions.jsonl`: all 272 forecasts, cutoffs, independent
  features, separately labeled evaluation targets and evaluation-only markets.

The dedicated GitHub workflow runs 19 meaningful checks and reproduces all
three outputs byte for byte. These checks cover future/current-result and
market isolation, same-time games, delayed final availability, neutral venue,
rest, relocation, season decay, ties, missing prices, injury timestamp gates,
optimizer convergence, holdout-label independence, snapshot integrity and
run preservation. Local output audits verify unique IDs, all 272 cutoffs,
normalization and identical frozen model hashes.

## Decision and next data work

Keep v1 as an independent engineering baseline. Do not change today's live
forecasts, active model/profile or previously accepted behavioral benchmark.
Do not fit another candidate based on which games this 2025 test missed; the
season is now an inspected evaluation set. A later method must be specified
with new validation and fresh prospective evaluation before promotion.

The next substantive data work is audited prior-game offense/defense efficiency
and timestamped quarterback/availability snapshots, with source publication
cutoffs and coverage reported before fitting. Rest and simple win/margin history
alone have not beaten the market here. NHL needs its own historical data and
market comparator; this NFL benchmark does not validate a hockey model.

Today's 43 saved live forecasts remain separate. The October 11 morning review
collected 29 results with zero errors and verified all 43 forecast hashes
unchanged; the remaining 14 forecasts cover today's NFL games. The replacement
Tyler Health & Results task was enabled at 13:08:39 UTC, hourly from 10 a.m.
Eastern. No wagers, live-model promotion, deployment or database change was
performed for this benchmark.
