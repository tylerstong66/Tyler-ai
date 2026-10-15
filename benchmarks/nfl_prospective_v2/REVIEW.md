# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **14** · Settled: **13** · Pending: **1**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-13T07:43:05.745249+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 13 | 1 | 0.4832 | 0.9777 | 69.2% | Unavailable | Unavailable | Unavailable |
| v1 | 13 | 1 | 0.4938 | 0.9896 | 69.2% | Unavailable | Unavailable | Unavailable |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 12 | 1 | 0.3991 | 0.5876 | 75.0% | Unavailable | Unavailable | Unavailable |
| v1 | 12 | 1 | 0.4106 | 0.6005 | 75.0% | Unavailable | Unavailable | Unavailable |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 12 | 1 | 0.3991 | 0.5876 | 75.0% | Unavailable | Unavailable | Unavailable |
| v1 | 12 | 1 | 0.4106 | 0.6005 | 75.0% | Unavailable | Unavailable | Unavailable |
| market | 12 | 1 | 0.4132 | 0.6006 | 66.7% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 12 | 1 | -0.0115 | Unavailable | -0.0129 | Unavailable | 0.0 pp | Unavailable |
| market | 12 | 1 | -0.0141 | Unavailable | -0.0130 | Unavailable | 8.3 pp | Unavailable |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 6 | 35.8% | 16.7% | 3.0% to 56.4% |
| v2 | 40%–60% | 4 | 48.3% | 50.0% | 15.0% to 85.0% |
| v2 | 60%–80% | 2 | 68.4% | 50.0% | 9.5% to 90.5% |
| v2 | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 6 | 34.5% | 16.7% | 3.0% to 56.4% |
| v1 | 40%–60% | 3 | 44.9% | 33.3% | 6.1% to 79.2% |
| v1 | 60%–80% | 3 | 66.5% | 66.7% | 20.8% to 93.9% |
| v1 | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 4 | 30.1% | 0.0% | 0.0% to 49.0% |
| market (paired only) | 40%–60% | 5 | 53.0% | 60.0% | 23.1% to 88.2% |
| market (paired only) | 60%–80% | 3 | 61.9% | 33.3% | 6.1% to 79.2% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 6 | 35.6% | 16.7% | 3.0% to 56.4% |
| v2 full home | 40%–60% | 5 | 48.1% | 40.0% | 11.8% to 76.9% |
| v2 full home | 60%–80% | 2 | 68.1% | 50.0% | 9.5% to 90.5% |
| v2 full home | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full away | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full away | 20%–40% | 2 | 31.5% | 50.0% | 9.5% to 90.5% |
| v2 full away | 40%–60% | 5 | 51.6% | 40.0% | 11.8% to 76.9% |
| v2 full away | 60%–80% | 6 | 64.0% | 83.3% | 43.6% to 97.0% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 13 | 0.4% | 7.7% | 1.4% to 33.3% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 6 | 34.4% | 16.7% | 3.0% to 56.4% |
| v1 full home | 40%–60% | 4 | 45.8% | 25.0% | 4.6% to 69.9% |
| v1 full home | 60%–80% | 3 | 66.2% | 66.7% | 20.8% to 93.9% |
| v1 full home | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full away | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full away | 20%–40% | 3 | 33.4% | 33.3% | 6.1% to 79.2% |
| v1 full away | 40%–60% | 4 | 53.9% | 50.0% | 15.0% to 85.0% |
| v1 full away | 60%–80% | 6 | 65.3% | 83.3% | 43.6% to 97.0% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 13 | 0.4% | 7.7% | 1.4% to 33.3% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261015T095534015510Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
