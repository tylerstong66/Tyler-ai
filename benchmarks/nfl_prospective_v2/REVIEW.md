# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **99** · Settled: **99** · Pending: **0**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-28T02:41:32.377726+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 99 / 100; settled among selected: 99; pending among selected: 0.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 99 | 8 | 0.4178 | 0.6464 | 68.7% | 0.3486 to 0.4854 | 0.5358 to 0.7701 | 58.5% to 79.4% |
| v1 | 99 | 8 | 0.4241 | 0.6525 | 65.7% | 0.3617 to 0.4888 | 0.5482 to 0.7739 | 55.3% to 75.5% |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 98 | 8 | 0.4067 | 0.5920 | 69.4% | 0.3404 to 0.4751 | 0.5204 to 0.6668 | 58.8% to 79.8% |
| v1 | 98 | 8 | 0.4131 | 0.5982 | 66.3% | 0.3530 to 0.4764 | 0.5332 to 0.6667 | 55.4% to 76.0% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 98 | 8 | 0.4067 | 0.5920 | 69.4% | 0.3404 to 0.4751 | 0.5204 to 0.6668 | 58.8% to 79.8% |
| v1 | 98 | 8 | 0.4131 | 0.5982 | 66.3% | 0.3530 to 0.4764 | 0.5332 to 0.6667 | 55.4% to 76.0% |
| market | 98 | 8 | 0.4022 | 0.5895 | 71.4% | 0.3310 to 0.4727 | 0.5102 to 0.6702 | 64.1% to 80.2% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 98 | 8 | -0.0064 | -0.0173 to 0.0043 | -0.0062 | -0.0176 to 0.0054 | 3.1 pp | 1.0 pp to 5.6 pp |
| market | 98 | 8 | 0.0045 | -0.0219 to 0.0290 | 0.0025 | -0.0273 to 0.0289 | -2.0 pp | -8.0 pp to 2.9 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 98 | 16.7% | 88.1% | 15.0% | 31.6% |
| v1 | 98 | 18.0% | 87.4% | 14.7% | 33.7% |
| market | 98 | 16.0% | 90.4% | 15.7% | 35.7% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 2 | 17.9% | 0.0% | 0.0% to 65.8% |
| v2 | 20%–40% | 24 | 34.5% | 16.7% | 6.7% to 35.9% |
| v2 | 40%–60% | 31 | 51.6% | 54.8% | 37.8% to 70.8% |
| v2 | 60%–80% | 35 | 68.9% | 57.1% | 40.9% to 72.0% |
| v2 | 80%–100% | 6 | 83.4% | 83.3% | 43.6% to 97.0% |
| v1 | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 | 20%–40% | 21 | 33.6% | 19.0% | 7.7% to 40.0% |
| v1 | 40%–60% | 33 | 50.6% | 45.5% | 29.8% to 62.0% |
| v1 | 60%–80% | 35 | 67.6% | 60.0% | 43.6% to 74.4% |
| v1 | 80%–100% | 7 | 83.1% | 85.7% | 48.7% to 97.4% |
| market (paired only) | 0%–20% | 3 | 18.5% | 0.0% | 0.0% to 56.1% |
| market (paired only) | 20%–40% | 22 | 32.0% | 13.6% | 4.7% to 33.3% |
| market (paired only) | 40%–60% | 35 | 51.2% | 48.6% | 33.0% to 64.4% |
| market (paired only) | 60%–80% | 30 | 68.5% | 63.3% | 45.5% to 78.1% |
| market (paired only) | 80%–100% | 8 | 84.9% | 87.5% | 52.9% to 97.8% |
| v2 full home | 0%–20% | 2 | 17.8% | 0.0% | 0.0% to 65.8% |
| v2 full home | 20%–40% | 24 | 34.3% | 16.7% | 6.7% to 35.9% |
| v2 full home | 40%–60% | 33 | 51.5% | 51.5% | 35.2% to 67.5% |
| v2 full home | 60%–80% | 34 | 68.9% | 58.8% | 42.2% to 73.6% |
| v2 full home | 80%–100% | 6 | 83.1% | 83.3% | 43.6% to 97.0% |
| v2 full away | 0%–20% | 6 | 16.5% | 16.7% | 3.0% to 56.4% |
| v2 full away | 20%–40% | 35 | 31.0% | 42.9% | 28.0% to 59.1% |
| v2 full away | 40%–60% | 32 | 48.4% | 43.8% | 28.2% to 60.7% |
| v2 full away | 60%–80% | 24 | 65.3% | 83.3% | 64.1% to 93.3% |
| v2 full away | 80%–100% | 2 | 81.8% | 100.0% | 34.2% to 100.0% |
| v2 full tie | 0%–20% | 99 | 0.4% | 1.0% | 0.2% to 5.5% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 full home | 20%–40% | 22 | 33.8% | 18.2% | 7.3% to 38.5% |
| v1 full home | 40%–60% | 34 | 51.0% | 44.1% | 28.9% to 60.5% |
| v1 full home | 60%–80% | 36 | 68.2% | 61.1% | 44.9% to 75.2% |
| v1 full home | 80%–100% | 5 | 83.9% | 100.0% | 56.6% to 100.0% |
| v1 full away | 0%–20% | 7 | 16.9% | 14.3% | 2.6% to 51.3% |
| v1 full away | 20%–40% | 35 | 32.3% | 40.0% | 25.6% to 56.4% |
| v1 full away | 40%–60% | 34 | 49.2% | 52.9% | 36.7% to 68.5% |
| v1 full away | 60%–80% | 21 | 66.1% | 81.0% | 60.0% to 92.3% |
| v1 full away | 80%–100% | 2 | 81.3% | 100.0% | 34.2% to 100.0% |
| v1 full tie | 0%–20% | 99 | 0.4% | 1.0% | 0.2% to 5.5% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261128T114524980349Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
