# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **40** · Settled: **36** · Pending: **4**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-25T22:33:48.693749+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 40 / 100; settled among selected: 36; pending among selected: 4.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 36 | 3 | 0.5278 | 0.8341 | 55.6% | Unavailable | Unavailable | Unavailable |
| v1 | 36 | 3 | 0.5264 | 0.8322 | 52.8% | Unavailable | Unavailable | Unavailable |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 35 | 3 | 0.5004 | 0.6939 | 57.1% | Unavailable | Unavailable | Unavailable |
| v1 | 35 | 3 | 0.4991 | 0.6919 | 54.3% | Unavailable | Unavailable | Unavailable |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 35 | 3 | 0.5004 | 0.6939 | 57.1% | Unavailable | Unavailable | Unavailable |
| v1 | 35 | 3 | 0.4991 | 0.6919 | 54.3% | Unavailable | Unavailable | Unavailable |
| market | 35 | 3 | 0.4963 | 0.6965 | 60.0% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 35 | 3 | 0.0014 | Unavailable | 0.0020 | Unavailable | 2.9 pp | Unavailable |
| market | 35 | 3 | 0.0042 | Unavailable | -0.0026 | Unavailable | -2.9 pp | Unavailable |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 35 | 25.3% | 81.6% | 13.7% | 37.1% |
| v1 | 35 | 29.2% | 81.0% | 13.9% | 31.4% |
| market | 35 | 25.6% | 84.7% | 13.1% | 54.3% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 10 | 34.8% | 30.0% | 10.8% to 60.3% |
| v2 | 40%–60% | 13 | 50.2% | 38.5% | 17.7% to 64.5% |
| v2 | 60%–80% | 10 | 69.7% | 40.0% | 16.8% to 68.7% |
| v2 | 80%–100% | 2 | 81.1% | 50.0% | 9.5% to 90.5% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 10 | 34.6% | 30.0% | 10.8% to 60.3% |
| v1 | 40%–60% | 11 | 49.2% | 36.4% | 15.2% to 64.6% |
| v1 | 60%–80% | 11 | 67.0% | 36.4% | 15.2% to 64.6% |
| v1 | 80%–100% | 3 | 80.4% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 5 | 30.3% | 0.0% | 0.0% to 43.4% |
| market (paired only) | 40%–60% | 19 | 49.0% | 42.1% | 23.1% to 63.7% |
| market (paired only) | 60%–80% | 10 | 70.9% | 50.0% | 23.7% to 76.3% |
| market (paired only) | 80%–100% | 1 | 84.7% | 0.0% | 0.0% to 79.3% |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 10 | 34.6% | 30.0% | 10.8% to 60.3% |
| v2 full home | 40%–60% | 14 | 49.8% | 35.7% | 16.3% to 61.2% |
| v2 full home | 60%–80% | 10 | 69.5% | 40.0% | 16.8% to 68.7% |
| v2 full home | 80%–100% | 2 | 80.8% | 50.0% | 9.5% to 90.5% |
| v2 full away | 0%–20% | 2 | 18.8% | 50.0% | 9.5% to 90.5% |
| v2 full away | 20%–40% | 10 | 30.2% | 60.0% | 31.3% to 83.2% |
| v2 full away | 40%–60% | 14 | 49.8% | 57.1% | 32.6% to 78.6% |
| v2 full away | 60%–80% | 10 | 65.0% | 70.0% | 39.7% to 89.2% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 36 | 0.4% | 2.8% | 0.5% to 14.2% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 10 | 34.5% | 30.0% | 10.8% to 60.3% |
| v1 full home | 40%–60% | 13 | 49.8% | 30.8% | 12.7% to 57.6% |
| v1 full home | 60%–80% | 12 | 69.5% | 41.7% | 19.3% to 68.0% |
| v1 full home | 80%–100% | 1 | 80.7% | 100.0% | 20.7% to 100.0% |
| v1 full away | 0%–20% | 3 | 19.5% | 33.3% | 6.1% to 79.2% |
| v1 full away | 20%–40% | 11 | 32.9% | 63.6% | 35.4% to 84.8% |
| v1 full away | 40%–60% | 12 | 50.7% | 58.3% | 32.0% to 80.7% |
| v1 full away | 60%–80% | 10 | 65.2% | 70.0% | 39.7% to 89.2% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 36 | 0.4% | 2.8% | 0.5% to 14.2% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261025T223345876360Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
