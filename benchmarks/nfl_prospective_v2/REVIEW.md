# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **69** · Settled: **69** · Pending: **0**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-10T09:51:36.591331+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 69 / 100; settled among selected: 69; pending among selected: 0.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 69 | 5 | 0.4348 | 0.6840 | 69.6% | 0.3513 to 0.5076 | 0.5462 to 0.8409 | 56.5% to 82.9% |
| v1 | 69 | 5 | 0.4466 | 0.6958 | 65.2% | 0.3757 to 0.5083 | 0.5675 to 0.8478 | 52.9% to 77.1% |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 68 | 5 | 0.4192 | 0.6079 | 70.6% | 0.3451 to 0.5021 | 0.5291 to 0.6957 | 57.4% to 83.8% |
| v1 | 68 | 5 | 0.4311 | 0.6199 | 66.2% | 0.3683 to 0.5013 | 0.5529 to 0.6948 | 54.3% to 78.8% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 68 | 5 | 0.4192 | 0.6079 | 70.6% | 0.3451 to 0.5021 | 0.5291 to 0.6957 | 57.4% to 83.8% |
| v1 | 68 | 5 | 0.4311 | 0.6199 | 66.2% | 0.3683 to 0.5013 | 0.5529 to 0.6948 | 54.3% to 78.8% |
| market | 68 | 5 | 0.4043 | 0.5953 | 72.1% | 0.3219 to 0.4797 | 0.5047 to 0.6803 | 62.9% to 83.8% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 68 | 5 | -0.0119 | -0.0231 to -0.0007 | -0.0120 | -0.0241 to -0.0004 | 4.4 pp | 1.5 pp to 7.1 pp |
| market | 68 | 5 | 0.0149 | -0.0136 to 0.0424 | 0.0126 | -0.0179 to 0.0421 | -1.5 pp | -8.8 pp to 6.1 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 68 | 25.3% | 83.8% | 13.8% | 35.3% |
| v1 | 68 | 27.0% | 83.5% | 13.7% | 36.8% |
| market | 68 | 19.6% | 84.7% | 14.4% | 39.7% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 19 | 35.0% | 15.8% | 5.5% to 37.6% |
| v2 | 40%–60% | 24 | 51.0% | 45.8% | 27.9% to 64.9% |
| v2 | 60%–80% | 22 | 69.7% | 59.1% | 38.7% to 76.7% |
| v2 | 80%–100% | 3 | 82.0% | 66.7% | 20.8% to 93.9% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 16 | 34.2% | 18.8% | 6.6% to 43.0% |
| v1 | 40%–60% | 25 | 49.6% | 36.0% | 20.2% to 55.5% |
| v1 | 60%–80% | 23 | 68.1% | 60.9% | 40.8% to 77.8% |
| v1 | 80%–100% | 4 | 81.2% | 75.0% | 30.1% to 95.4% |
| market (paired only) | 0%–20% | 1 | 19.6% | 0.0% | 0.0% to 79.3% |
| market (paired only) | 20%–40% | 15 | 32.5% | 0.0% | 0.0% to 20.4% |
| market (paired only) | 40%–60% | 27 | 49.9% | 48.1% | 30.7% to 66.0% |
| market (paired only) | 60%–80% | 22 | 69.0% | 63.6% | 43.0% to 80.3% |
| market (paired only) | 80%–100% | 3 | 83.1% | 66.7% | 20.8% to 93.9% |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 19 | 34.9% | 15.8% | 5.5% to 37.6% |
| v2 full home | 40%–60% | 26 | 51.1% | 42.3% | 25.5% to 61.1% |
| v2 full home | 60%–80% | 21 | 69.9% | 61.9% | 40.9% to 79.2% |
| v2 full home | 80%–100% | 3 | 81.7% | 66.7% | 20.8% to 93.9% |
| v2 full away | 0%–20% | 3 | 17.9% | 33.3% | 6.1% to 79.2% |
| v2 full away | 20%–40% | 22 | 30.2% | 40.9% | 23.3% to 61.3% |
| v2 full away | 40%–60% | 25 | 48.9% | 52.0% | 33.5% to 70.0% |
| v2 full away | 60%–80% | 19 | 64.8% | 84.2% | 62.4% to 94.5% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 69 | 0.4% | 1.4% | 0.3% to 7.8% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 17 | 34.4% | 17.6% | 6.2% to 41.0% |
| v1 full home | 40%–60% | 26 | 50.2% | 34.6% | 19.4% to 53.8% |
| v1 full home | 60%–80% | 24 | 69.2% | 62.5% | 42.7% to 78.8% |
| v1 full home | 80%–100% | 2 | 81.9% | 100.0% | 34.2% to 100.0% |
| v1 full away | 0%–20% | 4 | 18.7% | 25.0% | 4.6% to 69.9% |
| v1 full away | 20%–40% | 23 | 31.8% | 39.1% | 22.2% to 59.2% |
| v1 full away | 40%–60% | 26 | 50.2% | 61.5% | 42.5% to 77.6% |
| v1 full away | 60%–80% | 16 | 65.6% | 81.2% | 57.0% to 93.4% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 69 | 0.4% | 1.4% | 0.3% to 7.8% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261110T095134854692Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
