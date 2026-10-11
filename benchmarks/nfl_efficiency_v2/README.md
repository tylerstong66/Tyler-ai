# NFL efficiency candidate v2

Experimental offline candidate, frozen on October 11, 2026. NO BET; actual wagers $0. Original paper forecasts and production are unchanged. No prospective forecasts have been recorded by this offline run.

## Data and method

8,156 team-game records cover all 4,078 regular-season and postseason games in the pinned 2010–2024 schedule. `sources.json` records the nflverse release asset URLs, published SHA256 digests, retrieval time and reduced snapshot hash. Each downloaded asset matched its published digest. Identity, season, week, opponent pairing, uniqueness and complete coverage are checked before fitting.

Efficiency is `(passing_epa + rushing_epa) / (attempts + sacks_suffered + carries)`. This is a **box-score EPA proxy**, not EPA for every play: passing EPA uses quarterback-adjusted receiver-fumble treatment; official carries include kneels and scrambles. Definitions: https://nflreadr.nflverse.com/articles/dictionary_team_stats.html.

For each prior team-game, subtract the opponent's prior defensive rating from offensive EPA; subtract the team's prior offensive rating from the opponent's defensive EPA allowed. Both ratings are read before either team is updated. Ratings use the last 16 eligible games and 200 zero-EPA pseudo plays. Lower defensive EPA allowed is better. This is an online residual adjustment, not a full-season schedule-strength fit. Ratings carry across seasons within the 16-game window; no offseason personnel inference is made.

Add the home-minus-away offensive rating and away-minus-home defensive rating to the five v1 features. Prior results become eligible after 24 hours; historical stats after 48 hours. Those delays are assumptions: retrospective revised data do not establish historical publication time. Missing or mismatched stats fail closed. No moneyline, current-game result, current-game stats or postgame quarterback identity is a predictor.

Train: 2014–2022, 2,335 regular-season games. Development validation: 2023–2024, 544 games. Fixed L2 grid: 0.001, 0.01, 0.1, selected by full three-outcome log loss; selected 0.001. Refit: 2014–2024. The already-inspected 2025 holdout was excluded from this experiment. These validation results are used for selection and **are not a fresh independent test**.

| Development validation | v1 | v2 | Market favorite |
|---|---:|---:|---:|
| Correct / 544 | 353 | 358 | 379 |
| Accuracy | 64.9% | 65.8% | 69.7% |
| Paired binary Brier | 0.445894 | 0.442004 | 0.418871 |
| Conditional log loss | 0.636617 | 0.632623 | 0.607419 |

Lower scoring loss is better. Market prices are retrospective and untimestamped. This comparison does not establish tradable value, ROI or a betting edge. Candidate remains development-only.

## Quarterback and injury evidence

The availability adapter requires an exact game and team, player ID, explicit status, HTTPS source, retained source hash, verified publication timestamp and actual retrieval before the prediction cutoff. Practice status, game designation, official inactive and confirmed starting quarterback are distinct evidence kinds. A questionable player is not automatically inactive. Missing reports are unknown, not healthy.

**Injury and quarterback effects remain disabled:** no sufficiently audited historical timestamped availability training dataset was fitted. The adapter provides evidence rules, not a claim that those effects have been modeled or live reports captured.

## Prospective test

`protocol.json` freezes the experiment before fitting. Only games kicking off after the freeze qualify. Capture current completed-game statistics and source snapshots, derive features before kickoff, record a new v2 shadow artifact with `freeze_prediction`, and preserve original forecasts. The exclusive writer rejects overwrites, post-kickoff generation, mismatched freeze times, invalid features and absent source hashes. It is an offline callable, not an enabled live collector or scheduler.

Use the first 100 eligible future NFL regular-season games, including all eligible games without outcome-based selection. Report exclusions and source coverage. Record v1 and timestamped market comparisons at the same cutoff; collect verified finals afterward. Evaluate paired Brier and log loss, calibration and uncertainty clustered by season/week. QB/injury observations are audit context only until a separately frozen model has valid training evidence. No production promotion is authorized by development results.

Reproduce without network or application credentials:

```sh
python -m unittest test_sports_efficiency_candidate test_sports_historical_benchmark
python sports_efficiency_candidate.py --output /tmp/nfl-efficiency-v2
cmp benchmarks/nfl_efficiency_v2/run_2026_10_11/model.json /tmp/nfl-efficiency-v2/model.json
cmp benchmarks/nfl_efficiency_v2/run_2026_10_11/report.json /tmp/nfl-efficiency-v2/report.json
```
