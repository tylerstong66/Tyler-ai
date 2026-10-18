# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **53** · Settled: **41** · Pending: **12**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-18T01:03:02.947547+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 53 / 100; settled among selected: 41; pending among selected: 12.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 41 | 7 | 0.4672 | 0.6601 | 63.4% | 0.4297 to 0.4921 | 0.6223 to 0.6852 | 48.9% to 85.0% |
| fixed_elo | 41 | 7 | 0.4316 | 0.6214 | 58.5% | 0.3364 to 0.4970 | 0.5213 to 0.6900 | 43.2% to 80.0% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 41 | 7 | 0.4672 | 0.6601 | 63.4% | 0.4297 to 0.4921 | 0.6223 to 0.6852 | 48.9% to 85.0% |
| fixed_elo | 41 | 7 | 0.4316 | 0.6214 | 58.5% | 0.3364 to 0.4970 | 0.5213 to 0.6900 | 43.2% to 80.0% |
| market | 41 | 7 | 0.4402 | 0.6305 | 58.5% | 0.3685 to 0.4915 | 0.5553 to 0.6843 | 46.7% to 79.2% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 41 | 7 | 0.0356 | -0.0049 to 0.0947 | 0.0387 | -0.0050 to 0.1026 | 4.9 pp | 0.0 pp to 11.8 pp |
| market | 41 | 7 | 0.0270 | -0.0028 to 0.0670 | 0.0297 | -0.0024 to 0.0725 | 4.9 pp | -6.9 pp to 20.9 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 41 | 44.1% | 61.4% | 3.8% | 97.6% |
| fixed_elo | 41 | 34.7% | 79.3% | 10.6% | 51.2% |
| market | 41 | 34.3% | 76.0% | 8.3% | 70.7% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 40 | 52.2% | 55.0% | 39.8% to 69.3% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 2 | 34.8% | 0.0% | 0.0% to 65.8% |
| fixed_elo | 40%–60% | 21 | 51.3% | 42.9% | 24.5% to 63.5% |
| fixed_elo | 60%–80% | 18 | 67.2% | 77.8% | 54.8% to 91.0% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 2 | 36.3% | 0.0% | 0.0% to 65.8% |
| market (paired only) | 40%–60% | 29 | 52.4% | 51.7% | 34.4% to 68.6% |
| market (paired only) | 60%–80% | 10 | 68.2% | 80.0% | 49.0% to 94.3% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261018T010301204444Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
