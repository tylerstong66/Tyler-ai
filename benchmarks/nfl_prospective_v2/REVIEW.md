# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **56** · Settled: **55** · Pending: **1**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-03T06:48:01.509970+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 56 / 100; settled among selected: 55; pending among selected: 1.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 55 | 4 | 0.4679 | 0.7330 | 63.6% | Unavailable | Unavailable | Unavailable |
| v1 | 55 | 4 | 0.4756 | 0.7408 | 60.0% | Unavailable | Unavailable | Unavailable |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 54 | 4 | 0.4489 | 0.6389 | 64.8% | Unavailable | Unavailable | Unavailable |
| v1 | 54 | 4 | 0.4568 | 0.6469 | 61.1% | Unavailable | Unavailable | Unavailable |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 54 | 4 | 0.4489 | 0.6389 | 64.8% | Unavailable | Unavailable | Unavailable |
| v1 | 54 | 4 | 0.4568 | 0.6469 | 61.1% | Unavailable | Unavailable | Unavailable |
| market | 54 | 4 | 0.4426 | 0.6373 | 66.7% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 54 | 4 | -0.0079 | Unavailable | -0.0079 | Unavailable | 3.7 pp | Unavailable |
| market | 54 | 4 | 0.0063 | Unavailable | 0.0016 | Unavailable | -1.9 pp | Unavailable |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 54 | 25.3% | 83.8% | 13.9% | 37.0% |
| v1 | 54 | 27.0% | 83.5% | 14.0% | 33.3% |
| market | 54 | 25.6% | 84.7% | 13.6% | 44.4% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 13 | 34.3% | 23.1% | 8.2% to 50.3% |
| v2 | 40%–60% | 20 | 51.7% | 50.0% | 29.9% to 70.1% |
| v2 | 60%–80% | 18 | 69.4% | 55.6% | 33.7% to 75.4% |
| v2 | 80%–100% | 3 | 82.0% | 66.7% | 20.8% to 93.9% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 12 | 33.8% | 25.0% | 8.9% to 53.2% |
| v1 | 40%–60% | 18 | 50.0% | 44.4% | 24.6% to 66.3% |
| v1 | 60%–80% | 20 | 67.1% | 55.0% | 34.2% to 74.2% |
| v1 | 80%–100% | 4 | 81.2% | 75.0% | 30.1% to 95.4% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 9 | 31.7% | 0.0% | 0.0% to 29.9% |
| market (paired only) | 40%–60% | 24 | 50.2% | 50.0% | 31.4% to 68.6% |
| market (paired only) | 60%–80% | 19 | 68.9% | 63.2% | 41.0% to 80.9% |
| market (paired only) | 80%–100% | 2 | 84.2% | 50.0% | 9.5% to 90.5% |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 13 | 34.2% | 23.1% | 8.2% to 50.3% |
| v2 full home | 40%–60% | 21 | 51.4% | 47.6% | 28.3% to 67.6% |
| v2 full home | 60%–80% | 18 | 69.1% | 55.6% | 33.7% to 75.4% |
| v2 full home | 80%–100% | 3 | 81.7% | 66.7% | 20.8% to 93.9% |
| v2 full away | 0%–20% | 3 | 17.9% | 33.3% | 6.1% to 79.2% |
| v2 full away | 20%–40% | 18 | 30.5% | 44.4% | 24.6% to 66.3% |
| v2 full away | 40%–60% | 21 | 48.3% | 47.6% | 28.3% to 67.6% |
| v2 full away | 60%–80% | 13 | 65.4% | 76.9% | 49.7% to 91.8% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 55 | 0.4% | 1.8% | 0.3% to 9.6% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 12 | 33.7% | 25.0% | 8.9% to 53.2% |
| v1 full home | 40%–60% | 20 | 50.3% | 40.0% | 21.9% to 61.3% |
| v1 full home | 60%–80% | 21 | 68.5% | 57.1% | 36.5% to 75.5% |
| v1 full home | 80%–100% | 2 | 81.9% | 100.0% | 34.2% to 100.0% |
| v1 full away | 0%–20% | 4 | 18.7% | 25.0% | 4.6% to 69.9% |
| v1 full away | 20%–40% | 20 | 32.7% | 45.0% | 25.8% to 65.8% |
| v1 full away | 40%–60% | 19 | 49.9% | 52.6% | 31.7% to 72.7% |
| v1 full away | 60%–80% | 12 | 66.0% | 75.0% | 46.8% to 91.1% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 55 | 0.4% | 1.8% | 0.3% to 9.6% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261105T152738979169Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
