# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **82** · Settled: **71** · Pending: **11**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-15T17:42:46.844085+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 82 / 100; settled among selected: 71; pending among selected: 11.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 71 | 6 | 0.4377 | 0.6855 | 69.0% | 0.3622 to 0.5216 | 0.5553 to 0.8325 | 54.9% to 81.7% |
| v1 | 71 | 6 | 0.4491 | 0.6970 | 64.8% | 0.3836 to 0.5227 | 0.5762 to 0.8407 | 51.4% to 76.3% |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 70 | 6 | 0.4226 | 0.6114 | 70.0% | 0.3519 to 0.5099 | 0.5368 to 0.7043 | 55.7% to 82.8% |
| v1 | 70 | 6 | 0.4342 | 0.6231 | 65.7% | 0.3736 to 0.5120 | 0.5587 to 0.7064 | 51.4% to 77.5% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 70 | 6 | 0.4226 | 0.6114 | 70.0% | 0.3519 to 0.5099 | 0.5368 to 0.7043 | 55.7% to 82.8% |
| v1 | 70 | 6 | 0.4342 | 0.6231 | 65.7% | 0.3736 to 0.5120 | 0.5587 to 0.7064 | 51.4% to 77.5% |
| market | 70 | 6 | 0.4066 | 0.5977 | 71.4% | 0.3291 to 0.4873 | 0.5120 to 0.6888 | 61.4% to 81.7% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 70 | 6 | -0.0116 | -0.0215 to 0.0003 | -0.0117 | -0.0225 to 0.0013 | 4.3 pp | 1.4 pp to 6.9 pp |
| market | 70 | 6 | 0.0159 | -0.0105 to 0.0439 | 0.0137 | -0.0142 to 0.0427 | -1.4 pp | -8.6 pp to 5.7 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 70 | 25.3% | 83.8% | 13.7% | 35.7% |
| v1 | 70 | 27.0% | 83.5% | 13.6% | 37.1% |
| market | 70 | 19.6% | 84.7% | 14.1% | 41.4% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 19 | 35.0% | 15.8% | 5.5% to 37.6% |
| v2 | 40%–60% | 25 | 51.3% | 48.0% | 30.0% to 66.5% |
| v2 | 60%–80% | 23 | 69.3% | 56.5% | 36.8% to 74.4% |
| v2 | 80%–100% | 3 | 82.0% | 66.7% | 20.8% to 93.9% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 16 | 34.2% | 18.8% | 6.6% to 43.0% |
| v1 | 40%–60% | 26 | 50.0% | 38.5% | 22.4% to 57.5% |
| v1 | 60%–80% | 24 | 67.8% | 58.3% | 38.8% to 75.5% |
| v1 | 80%–100% | 4 | 81.2% | 75.0% | 30.1% to 95.4% |
| market (paired only) | 0%–20% | 1 | 19.6% | 0.0% | 0.0% to 79.3% |
| market (paired only) | 20%–40% | 15 | 32.5% | 0.0% | 0.0% to 20.4% |
| market (paired only) | 40%–60% | 29 | 50.4% | 48.3% | 31.4% to 65.6% |
| market (paired only) | 60%–80% | 22 | 69.0% | 63.6% | 43.0% to 80.3% |
| market (paired only) | 80%–100% | 3 | 83.1% | 66.7% | 20.8% to 93.9% |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 19 | 34.9% | 15.8% | 5.5% to 37.6% |
| v2 full home | 40%–60% | 27 | 51.3% | 44.4% | 27.6% to 62.7% |
| v2 full home | 60%–80% | 22 | 69.5% | 59.1% | 38.7% to 76.7% |
| v2 full home | 80%–100% | 3 | 81.7% | 66.7% | 20.8% to 93.9% |
| v2 full away | 0%–20% | 3 | 17.9% | 33.3% | 6.1% to 79.2% |
| v2 full away | 20%–40% | 23 | 30.6% | 43.5% | 25.6% to 63.2% |
| v2 full away | 40%–60% | 26 | 48.6% | 50.0% | 32.1% to 67.9% |
| v2 full away | 60%–80% | 19 | 64.8% | 84.2% | 62.4% to 94.5% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 71 | 0.4% | 1.4% | 0.2% to 7.6% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 17 | 34.4% | 17.6% | 6.2% to 41.0% |
| v1 full home | 40%–60% | 27 | 50.5% | 37.0% | 21.5% to 55.8% |
| v1 full home | 60%–80% | 25 | 68.9% | 60.0% | 40.7% to 76.6% |
| v1 full home | 80%–100% | 2 | 81.9% | 100.0% | 34.2% to 100.0% |
| v1 full away | 0%–20% | 4 | 18.7% | 25.0% | 4.6% to 69.9% |
| v1 full away | 20%–40% | 24 | 32.1% | 41.7% | 24.5% to 61.2% |
| v1 full away | 40%–60% | 27 | 49.9% | 59.3% | 40.7% to 75.5% |
| v1 full away | 60%–80% | 16 | 65.6% | 81.2% | 57.0% to 93.4% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 71 | 0.4% | 1.4% | 0.2% to 7.6% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261115T174243109739Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
