# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **68** · Settled: **64** · Pending: **4**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-08T23:43:18.067703+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 68 / 100; settled among selected: 64; pending among selected: 4.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 64 | 5 | 0.4426 | 0.6969 | 68.8% | 0.3547 to 0.5126 | 0.5506 to 0.8452 | 56.5% to 83.6% |
| v1 | 64 | 5 | 0.4523 | 0.7067 | 65.6% | 0.3759 to 0.5145 | 0.5691 to 0.8562 | 52.9% to 81.5% |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 63 | 5 | 0.4259 | 0.6152 | 69.8% | 0.3469 to 0.5060 | 0.5313 to 0.6998 | 57.1% to 84.5% |
| v1 | 63 | 5 | 0.4358 | 0.6251 | 66.7% | 0.3672 to 0.5068 | 0.5527 to 0.7009 | 53.8% to 83.0% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 63 | 5 | 0.4259 | 0.6152 | 69.8% | 0.3469 to 0.5060 | 0.5313 to 0.6998 | 57.1% to 84.5% |
| v1 | 63 | 5 | 0.4358 | 0.6251 | 66.7% | 0.3672 to 0.5068 | 0.5527 to 0.7009 | 53.8% to 83.0% |
| market | 63 | 5 | 0.4122 | 0.6041 | 71.4% | 0.3266 to 0.4797 | 0.5106 to 0.6803 | 62.9% to 84.9% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 63 | 5 | -0.0099 | -0.0206 to -0.0007 | -0.0100 | -0.0219 to 0.0002 | 3.2 pp | 0.0 pp to 6.2 pp |
| market | 63 | 5 | 0.0137 | -0.0136 to 0.0438 | 0.0110 | -0.0179 to 0.0447 | -1.6 pp | -10.0 pp to 6.6 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 63 | 25.3% | 83.8% | 13.7% | 36.5% |
| v1 | 63 | 27.0% | 83.5% | 13.6% | 36.5% |
| market | 63 | 19.6% | 84.7% | 14.1% | 42.9% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 18 | 34.9% | 16.7% | 5.8% to 39.2% |
| v2 | 40%–60% | 23 | 51.3% | 47.8% | 29.2% to 67.0% |
| v2 | 60%–80% | 19 | 69.8% | 57.9% | 36.3% to 76.9% |
| v2 | 80%–100% | 3 | 82.0% | 66.7% | 20.8% to 93.9% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 15 | 33.9% | 20.0% | 7.0% to 45.2% |
| v1 | 40%–60% | 23 | 49.0% | 39.1% | 22.2% to 59.2% |
| v1 | 60%–80% | 21 | 67.6% | 57.1% | 36.5% to 75.5% |
| v1 | 80%–100% | 4 | 81.2% | 75.0% | 30.1% to 95.4% |
| market (paired only) | 0%–20% | 1 | 19.6% | 0.0% | 0.0% to 79.3% |
| market (paired only) | 20%–40% | 13 | 32.1% | 0.0% | 0.0% to 22.8% |
| market (paired only) | 40%–60% | 27 | 49.9% | 48.1% | 30.7% to 66.0% |
| market (paired only) | 60%–80% | 19 | 68.9% | 63.2% | 41.0% to 80.9% |
| market (paired only) | 80%–100% | 3 | 83.1% | 66.7% | 20.8% to 93.9% |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 18 | 34.7% | 16.7% | 5.8% to 39.2% |
| v2 full home | 40%–60% | 24 | 51.0% | 45.8% | 27.9% to 64.9% |
| v2 full home | 60%–80% | 19 | 69.6% | 57.9% | 36.3% to 76.9% |
| v2 full home | 80%–100% | 3 | 81.7% | 66.7% | 20.8% to 93.9% |
| v2 full away | 0%–20% | 3 | 17.9% | 33.3% | 6.1% to 79.2% |
| v2 full away | 20%–40% | 19 | 30.1% | 42.1% | 23.1% to 63.7% |
| v2 full away | 40%–60% | 24 | 48.7% | 50.0% | 31.4% to 68.6% |
| v2 full away | 60%–80% | 18 | 64.9% | 83.3% | 60.8% to 94.2% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 64 | 0.4% | 1.6% | 0.3% to 8.3% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 16 | 34.2% | 18.8% | 6.6% to 43.0% |
| v1 full home | 40%–60% | 24 | 49.7% | 37.5% | 21.2% to 57.3% |
| v1 full home | 60%–80% | 22 | 68.9% | 59.1% | 38.7% to 76.7% |
| v1 full home | 80%–100% | 2 | 81.9% | 100.0% | 34.2% to 100.0% |
| v1 full away | 0%–20% | 4 | 18.7% | 25.0% | 4.6% to 69.9% |
| v1 full away | 20%–40% | 21 | 32.3% | 42.9% | 24.5% to 63.5% |
| v1 full away | 40%–60% | 24 | 50.8% | 58.3% | 38.8% to 75.5% |
| v1 full away | 60%–80% | 15 | 65.9% | 80.0% | 54.8% to 93.0% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 64 | 0.4% | 1.6% | 0.3% to 8.3% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261108T234315474574Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [{"game_id": "2026_09_LV_SF", "reason": "already_started"}].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
