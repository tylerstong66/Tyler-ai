# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **37** · Settled: **35** · Pending: **2**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-16T07:10:34.917388+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 37 / 100; settled among selected: 35; pending among selected: 2.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 35 | 5 | 0.4774 | 0.6704 | 60.0% | 0.4536 to 0.4963 | 0.6465 to 0.6894 | 46.2% to 81.8% |
| fixed_elo | 35 | 5 | 0.4570 | 0.6483 | 54.3% | 0.3905 to 0.5099 | 0.5791 to 0.7033 | 40.7% to 71.1% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 35 | 5 | 0.4774 | 0.6704 | 60.0% | 0.4536 to 0.4963 | 0.6465 to 0.6894 | 46.2% to 81.8% |
| fixed_elo | 35 | 5 | 0.4570 | 0.6483 | 54.3% | 0.3905 to 0.5099 | 0.5791 to 0.7033 | 40.7% to 71.1% |
| market | 35 | 5 | 0.4629 | 0.6542 | 51.4% | 0.4095 to 0.5075 | 0.5981 to 0.7007 | 42.3% to 63.3% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 35 | 5 | 0.0204 | -0.0136 to 0.0631 | 0.0221 | -0.0139 to 0.0674 | 5.7 pp | 0.0 pp to 15.4 pp |
| market | 35 | 5 | 0.0144 | -0.0191 to 0.0485 | 0.0162 | -0.0184 to 0.0528 | 8.6 pp | 0.0 pp to 30.8 pp |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 35 | 52.3% | 54.3% | 38.2% to 69.5% |
| model | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 1 | 34.7% | 0.0% | 0.0% to 79.3% |
| fixed_elo | 40%–60% | 20 | 51.2% | 45.0% | 25.8% to 65.8% |
| fixed_elo | 60%–80% | 14 | 67.2% | 71.4% | 45.4% to 88.3% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 1 | 34.3% | 0.0% | 0.0% to 79.3% |
| market (paired only) | 40%–60% | 27 | 52.5% | 51.9% | 34.0% to 69.3% |
| market (paired only) | 60%–80% | 7 | 68.2% | 71.4% | 35.9% to 91.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261016T071033764285Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
