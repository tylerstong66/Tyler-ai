# Tyler-ai
Tyler AI autonomous assistant

## Independent prospective sports tests

**NO BET / actual wagers $0.** These experimental forecasts do not place wagers or change the production Tyler AI model.

- [NFL results](benchmarks/nfl_prospective_v2/RESULTS.md): the previously frozen efficiency candidate versus team Elo and market odds.
- [NHL results](benchmarks/two_way_prospective/nhl/RESULTS.md) and [MLB results](benchmarks/two_way_prospective/mlb/RESULTS.md): separate frozen team-Elo logistic baselines versus fixed Elo and timestamped market odds. All verified regular-season and playoff games within 24 hours are eligible, including unpriced games. There is no NHL/MLB enrollment cap; the first review milestone is 100 settled games per league.
- [NHL/MLB retrospective diagnostics](benchmarks/two_way_retrospective_v1/README.md): reproducible chronological scoring of the frozen models on retained 2026-season games before the prospective trials. This post-hoc reconstruction is separate from the live test and is not a blind holdout.

The shared hourly GitHub workflow captures public sources, saves predictions before kickoff, and settles only when official league and ESPN identities, start times and final scores agree. Forecast files and frozen assets are hashed. Existing predictions are never replaced. Sleeping services, upstream failures, rescheduling and workflow delays can leave gaps; exact enrollment and settlement timing are not guaranteed.

NHL/MLB weights were fit once using 2025 regular-season results, with 2024 history for warmup. NHL fitting covers 1,312 games; MLB covers 2,421 games after excluding four ambiguous suspended/resumed 2025 games. Seven ambiguous resumption records across the two MLB seasons update ratings only at the later observed start plus the 12-hour delay. This historical fit has no independent validation; the saved upcoming forecasts are the independent test. Neither model uses NFL coefficients. Goalie confirmations, probable pitchers and lineups are evidence only, with unknown information retained as unknown and no effects applied to predictions. No predictive edge has been established.
