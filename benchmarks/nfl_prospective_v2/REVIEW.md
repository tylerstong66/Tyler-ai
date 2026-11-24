# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **94** · Settled: **94** · Pending: **0**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-24T10:55:32.898344+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 94 / 100; settled among selected: 94; pending among selected: 0.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 94 | 7 | 0.4103 | 0.6405 | 70.2% | 0.3418 to 0.4808 | 0.5277 to 0.7664 | 60.2% to 80.9% |
| v1 | 94 | 7 | 0.4175 | 0.6476 | 67.0% | 0.3558 to 0.4835 | 0.5400 to 0.7729 | 56.4% to 76.6% |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 93 | 7 | 0.3985 | 0.5833 | 71.0% | 0.3327 to 0.4703 | 0.5105 to 0.6614 | 60.4% to 81.7% |
| v1 | 93 | 7 | 0.4058 | 0.5905 | 67.7% | 0.3468 to 0.4730 | 0.5253 to 0.6627 | 57.1% to 77.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 93 | 7 | 0.3985 | 0.5833 | 71.0% | 0.3327 to 0.4703 | 0.5105 to 0.6614 | 60.4% to 81.7% |
| v1 | 93 | 7 | 0.4058 | 0.5905 | 67.7% | 0.3468 to 0.4730 | 0.5253 to 0.6627 | 57.1% to 77.7% |
| market | 93 | 7 | 0.3870 | 0.5723 | 72.0% | 0.3204 to 0.4516 | 0.4956 to 0.6459 | 64.3% to 81.4% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 93 | 7 | -0.0073 | -0.0186 to 0.0040 | -0.0072 | -0.0191 to 0.0047 | 3.2 pp | 1.0 pp to 6.1 pp |
| market | 93 | 7 | 0.0116 | -0.0102 to 0.0329 | 0.0110 | -0.0108 to 0.0326 | -1.1 pp | -6.5 pp to 4.2 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 93 | 16.7% | 88.1% | 15.1% | 32.3% |
| v1 | 93 | 18.0% | 87.4% | 14.8% | 34.4% |
| market | 93 | 16.0% | 90.4% | 15.9% | 34.4% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 2 | 17.9% | 0.0% | 0.0% to 65.8% |
| v2 | 20%–40% | 24 | 34.5% | 16.7% | 6.7% to 35.9% |
| v2 | 40%–60% | 30 | 51.8% | 53.3% | 36.1% to 69.8% |
| v2 | 60%–80% | 31 | 69.3% | 58.1% | 40.8% to 73.6% |
| v2 | 80%–100% | 6 | 83.4% | 83.3% | 43.6% to 97.0% |
| v1 | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 | 20%–40% | 21 | 33.6% | 19.0% | 7.7% to 40.0% |
| v1 | 40%–60% | 32 | 50.8% | 43.8% | 28.2% to 60.7% |
| v1 | 60%–80% | 31 | 68.1% | 61.3% | 43.8% to 76.3% |
| v1 | 80%–100% | 7 | 83.1% | 85.7% | 48.7% to 97.4% |
| market (paired only) | 0%–20% | 3 | 18.5% | 0.0% | 0.0% to 56.1% |
| market (paired only) | 20%–40% | 21 | 32.1% | 9.5% | 2.7% to 28.9% |
| market (paired only) | 40%–60% | 32 | 51.0% | 46.9% | 30.9% to 63.6% |
| market (paired only) | 60%–80% | 29 | 68.1% | 65.5% | 47.3% to 80.1% |
| market (paired only) | 80%–100% | 8 | 84.9% | 87.5% | 52.9% to 97.8% |
| v2 full home | 0%–20% | 2 | 17.8% | 0.0% | 0.0% to 65.8% |
| v2 full home | 20%–40% | 24 | 34.3% | 16.7% | 6.7% to 35.9% |
| v2 full home | 40%–60% | 32 | 51.7% | 50.0% | 33.6% to 66.4% |
| v2 full home | 60%–80% | 30 | 69.4% | 60.0% | 42.3% to 75.4% |
| v2 full home | 80%–100% | 6 | 83.1% | 83.3% | 43.6% to 97.0% |
| v2 full away | 0%–20% | 6 | 16.5% | 16.7% | 3.0% to 56.4% |
| v2 full away | 20%–40% | 31 | 30.6% | 41.9% | 26.4% to 59.2% |
| v2 full away | 40%–60% | 31 | 48.2% | 45.2% | 29.2% to 62.2% |
| v2 full away | 60%–80% | 24 | 65.3% | 83.3% | 64.1% to 93.3% |
| v2 full away | 80%–100% | 2 | 81.8% | 100.0% | 34.2% to 100.0% |
| v2 full tie | 0%–20% | 94 | 0.4% | 1.1% | 0.2% to 5.8% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 full home | 20%–40% | 22 | 33.8% | 18.2% | 7.3% to 38.5% |
| v1 full home | 40%–60% | 33 | 51.2% | 42.4% | 27.2% to 59.2% |
| v1 full home | 60%–80% | 32 | 68.8% | 62.5% | 45.3% to 77.1% |
| v1 full home | 80%–100% | 5 | 83.9% | 100.0% | 56.6% to 100.0% |
| v1 full away | 0%–20% | 7 | 16.9% | 14.3% | 2.6% to 51.3% |
| v1 full away | 20%–40% | 31 | 31.8% | 38.7% | 23.7% to 56.2% |
| v1 full away | 40%–60% | 33 | 49.0% | 54.5% | 38.0% to 70.2% |
| v1 full away | 60%–80% | 21 | 66.1% | 81.0% | 60.0% to 92.3% |
| v1 full away | 80%–100% | 2 | 81.3% | 100.0% | 34.2% to 100.0% |
| v1 full tie | 0%–20% | 94 | 0.4% | 1.1% | 0.2% to 5.8% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261124T105529946535Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
