# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **94** · Settled: **92** · Pending: **2**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-23T02:45:56.988267+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 94 / 100; settled among selected: 92; pending among selected: 2.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 92 | 7 | 0.4078 | 0.6386 | 70.7% | 0.3322 to 0.4808 | 0.5187 to 0.7665 | 60.2% to 81.8% |
| v1 | 92 | 7 | 0.4142 | 0.6449 | 67.4% | 0.3434 to 0.4834 | 0.5293 to 0.7729 | 56.5% to 78.1% |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 91 | 7 | 0.3957 | 0.5803 | 71.4% | 0.3225 to 0.4702 | 0.5011 to 0.6614 | 60.4% to 82.9% |
| v1 | 91 | 7 | 0.4023 | 0.5866 | 68.1% | 0.3351 to 0.4717 | 0.5137 to 0.6617 | 57.1% to 79.0% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 91 | 7 | 0.3957 | 0.5803 | 71.4% | 0.3225 to 0.4702 | 0.5011 to 0.6614 | 60.4% to 82.9% |
| v1 | 91 | 7 | 0.4023 | 0.5866 | 68.1% | 0.3351 to 0.4717 | 0.5137 to 0.6617 | 57.1% to 79.0% |
| market | 91 | 7 | 0.3807 | 0.5654 | 72.5% | 0.2995 to 0.4498 | 0.4725 to 0.6450 | 64.3% to 82.6% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 91 | 7 | -0.0066 | -0.0185 to 0.0048 | -0.0064 | -0.0188 to 0.0056 | 3.3 pp | 1.0 pp to 6.1 pp |
| market | 91 | 7 | 0.0150 | -0.0046 to 0.0354 | 0.0149 | -0.0069 to 0.0370 | -1.1 pp | -6.6 pp to 4.3 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 91 | 16.7% | 88.1% | 15.1% | 33.0% |
| v1 | 91 | 18.0% | 87.4% | 14.9% | 34.1% |
| market | 91 | 16.0% | 90.4% | 15.8% | 35.2% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 2 | 17.9% | 0.0% | 0.0% to 65.8% |
| v2 | 20%–40% | 23 | 34.4% | 13.0% | 4.5% to 32.1% |
| v2 | 40%–60% | 30 | 51.8% | 53.3% | 36.1% to 69.8% |
| v2 | 60%–80% | 30 | 69.4% | 56.7% | 39.2% to 72.6% |
| v2 | 80%–100% | 6 | 83.4% | 83.3% | 43.6% to 97.0% |
| v1 | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 | 20%–40% | 20 | 33.5% | 15.0% | 5.2% to 36.0% |
| v1 | 40%–60% | 31 | 50.6% | 41.9% | 26.4% to 59.2% |
| v1 | 60%–80% | 31 | 68.1% | 61.3% | 43.8% to 76.3% |
| v1 | 80%–100% | 7 | 83.1% | 85.7% | 48.7% to 97.4% |
| market (paired only) | 0%–20% | 3 | 18.5% | 0.0% | 0.0% to 56.1% |
| market (paired only) | 20%–40% | 20 | 32.3% | 5.0% | 0.9% to 23.6% |
| market (paired only) | 40%–60% | 32 | 51.0% | 46.9% | 30.9% to 63.6% |
| market (paired only) | 60%–80% | 28 | 68.4% | 64.3% | 45.8% to 79.3% |
| market (paired only) | 80%–100% | 8 | 84.9% | 87.5% | 52.9% to 97.8% |
| v2 full home | 0%–20% | 2 | 17.8% | 0.0% | 0.0% to 65.8% |
| v2 full home | 20%–40% | 23 | 34.3% | 13.0% | 4.5% to 32.1% |
| v2 full home | 40%–60% | 32 | 51.7% | 50.0% | 33.6% to 66.4% |
| v2 full home | 60%–80% | 29 | 69.5% | 58.6% | 40.7% to 74.5% |
| v2 full home | 80%–100% | 6 | 83.1% | 83.3% | 43.6% to 97.0% |
| v2 full away | 0%–20% | 6 | 16.5% | 16.7% | 3.0% to 56.4% |
| v2 full away | 20%–40% | 30 | 30.5% | 43.3% | 27.4% to 60.8% |
| v2 full away | 40%–60% | 31 | 48.2% | 45.2% | 29.2% to 62.2% |
| v2 full away | 60%–80% | 23 | 65.3% | 87.0% | 67.9% to 95.5% |
| v2 full away | 80%–100% | 2 | 81.8% | 100.0% | 34.2% to 100.0% |
| v2 full tie | 0%–20% | 92 | 0.4% | 1.1% | 0.2% to 5.9% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 full home | 20%–40% | 21 | 33.7% | 14.3% | 5.0% to 34.6% |
| v1 full home | 40%–60% | 32 | 50.9% | 40.6% | 25.5% to 57.7% |
| v1 full home | 60%–80% | 32 | 68.8% | 62.5% | 45.3% to 77.1% |
| v1 full home | 80%–100% | 5 | 83.9% | 100.0% | 56.6% to 100.0% |
| v1 full away | 0%–20% | 7 | 16.9% | 14.3% | 2.6% to 51.3% |
| v1 full away | 20%–40% | 31 | 31.8% | 38.7% | 23.7% to 56.2% |
| v1 full away | 40%–60% | 32 | 49.3% | 56.2% | 39.3% to 71.8% |
| v1 full away | 60%–80% | 20 | 66.2% | 85.0% | 64.0% to 94.8% |
| v1 full away | 80%–100% | 2 | 81.3% | 100.0% | 34.2% to 100.0% |
| v1 full tie | 0%–20% | 92 | 0.4% | 1.1% | 0.2% to 5.9% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261123T024553575836Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [{"game_id": "2026_11_PIT_PHI", "reason": "already_started"}, {"game_id": "2026_11_JAX_NYG", "reason": "already_started"}].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
