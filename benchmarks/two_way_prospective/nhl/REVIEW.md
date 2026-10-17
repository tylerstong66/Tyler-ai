# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **51** · Settled: **36** · Pending: **15**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-17T04:27:21.906529+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 51 / 100; settled among selected: 36; pending among selected: 15.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 36 | 6 | 0.4751 | 0.6681 | 61.1% | 0.4497 to 0.4946 | 0.6425 to 0.6877 | 47.4% to 83.3% |
| fixed_elo | 36 | 6 | 0.4508 | 0.6418 | 55.6% | 0.3791 to 0.5053 | 0.5671 to 0.6983 | 41.1% to 73.3% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 36 | 6 | 0.4751 | 0.6681 | 61.1% | 0.4497 to 0.4946 | 0.6425 to 0.6877 | 47.4% to 83.3% |
| fixed_elo | 36 | 6 | 0.4508 | 0.6418 | 55.6% | 0.3791 to 0.5053 | 0.5671 to 0.6983 | 41.1% to 73.3% |
| market | 36 | 6 | 0.4566 | 0.6476 | 52.8% | 0.3955 to 0.5009 | 0.5837 to 0.6941 | 43.3% to 66.7% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 36 | 6 | 0.0243 | -0.0107 to 0.0704 | 0.0263 | -0.0109 to 0.0749 | 5.6 pp | 0.0 pp to 14.3 pp |
| market | 36 | 6 | 0.0185 | -0.0157 to 0.0561 | 0.0205 | -0.0155 to 0.0608 | 8.3 pp | 0.0 pp to 30.4 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 36 | 44.1% | 58.9% | 3.6% | 100.0% |
| fixed_elo | 36 | 34.7% | 74.1% | 10.1% | 55.6% |
| market | 36 | 34.3% | 72.2% | 8.0% | 75.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 36 | 52.4% | 55.6% | 39.6% to 70.5% |
| model | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 1 | 34.7% | 0.0% | 0.0% to 79.3% |
| fixed_elo | 40%–60% | 20 | 51.2% | 45.0% | 25.8% to 65.8% |
| fixed_elo | 60%–80% | 15 | 67.1% | 73.3% | 48.0% to 89.1% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 1 | 34.3% | 0.0% | 0.0% to 79.3% |
| market (paired only) | 40%–60% | 27 | 52.5% | 51.9% | 34.0% to 69.3% |
| market (paired only) | 60%–80% | 8 | 67.9% | 75.0% | 40.9% to 92.9% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261017T042718800295Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
