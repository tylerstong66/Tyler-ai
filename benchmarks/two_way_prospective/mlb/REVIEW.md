# MLB prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **7** · Settled: **5** · Pending: **2**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-15T04:40:06.768457+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 5 | 4 | 0.4654 | 0.6584 | 60.0% | Unavailable | Unavailable | Unavailable |
| fixed_elo | 5 | 4 | 0.4518 | 0.6449 | 80.0% | Unavailable | Unavailable | Unavailable |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 3 | 3 | 0.5310 | 0.7246 | 33.3% | Unavailable | Unavailable | Unavailable |
| fixed_elo | 3 | 3 | 0.5258 | 0.7200 | 66.7% | Unavailable | Unavailable | Unavailable |
| market | 3 | 3 | 0.6618 | 0.8580 | 33.3% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 5 | 4 | 0.0135 | Unavailable | 0.0135 | Unavailable | -20.0 pp | Unavailable |
| market | 3 | 3 | -0.1307 | Unavailable | -0.1334 | Unavailable | 0.0 pp | Unavailable |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 5 | 56.0% | 60.0% | 23.1% to 88.2% |
| model | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 40%–60% | 3 | 54.0% | 66.7% | 20.8% to 93.9% |
| fixed_elo | 60%–80% | 2 | 60.7% | 50.0% | 9.5% to 90.5% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 40%–60% | 1 | 50.6% | 100.0% | 20.7% to 100.0% |
| market (paired only) | 60%–80% | 2 | 61.2% | 0.0% | 0.0% to 65.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/mlb/captures/20261015T044003019188Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
