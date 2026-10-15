# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **35** · Settled: **24** · Pending: **11**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-15T04:40:02.983366+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 24 | 4 | 0.4905 | 0.6836 | 54.2% | Unavailable | Unavailable | Unavailable |
| fixed_elo | 24 | 4 | 0.4933 | 0.6866 | 45.8% | Unavailable | Unavailable | Unavailable |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 24 | 4 | 0.4905 | 0.6836 | 54.2% | Unavailable | Unavailable | Unavailable |
| fixed_elo | 24 | 4 | 0.4933 | 0.6866 | 45.8% | Unavailable | Unavailable | Unavailable |
| market | 24 | 4 | 0.4943 | 0.6871 | 45.8% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 24 | 4 | -0.0029 | Unavailable | -0.0030 | Unavailable | 8.3 pp | Unavailable |
| market | 24 | 4 | -0.0039 | Unavailable | -0.0035 | Unavailable | 8.3 pp | Unavailable |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 24 | 52.0% | 45.8% | 27.9% to 64.9% |
| model | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 1 | 34.7% | 0.0% | 0.0% to 79.3% |
| fixed_elo | 40%–60% | 14 | 50.8% | 42.9% | 21.4% to 67.4% |
| fixed_elo | 60%–80% | 9 | 67.0% | 55.6% | 26.7% to 81.1% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 1 | 34.3% | 0.0% | 0.0% to 79.3% |
| market (paired only) | 40%–60% | 19 | 51.6% | 47.4% | 27.3% to 68.3% |
| market (paired only) | 60%–80% | 4 | 66.4% | 50.0% | 15.0% to 85.0% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261015T043958446964Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
