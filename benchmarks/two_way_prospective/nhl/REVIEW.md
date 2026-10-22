# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **82** · Settled: **70** · Pending: **12**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-22T04:47:02.375724+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 82 / 100; settled among selected: 70; pending among selected: 12.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 70 | 11 | 0.4812 | 0.6742 | 61.4% | 0.4618 to 0.5016 | 0.6547 to 0.6948 | 50.0% to 73.1% |
| fixed_elo | 70 | 11 | 0.4666 | 0.6591 | 58.6% | 0.4119 to 0.5236 | 0.6018 to 0.7197 | 45.9% to 70.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 70 | 11 | 0.4812 | 0.6742 | 61.4% | 0.4618 to 0.5016 | 0.6547 to 0.6948 | 50.0% to 73.1% |
| fixed_elo | 70 | 11 | 0.4666 | 0.6591 | 58.6% | 0.4119 to 0.5236 | 0.6018 to 0.7197 | 45.9% to 70.7% |
| market | 70 | 11 | 0.4640 | 0.6554 | 55.7% | 0.4276 to 0.5036 | 0.6172 to 0.6968 | 47.1% to 64.7% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 70 | 11 | 0.0146 | -0.0225 to 0.0492 | 0.0152 | -0.0249 to 0.0527 | 2.9 pp | 0.0 pp to 6.9 pp |
| market | 70 | 11 | 0.0172 | -0.0059 to 0.0368 | 0.0188 | -0.0059 to 0.0399 | 5.7 pp | -4.2 pp to 15.9 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 70 | 39.1% | 61.4% | 3.7% | 97.1% |
| fixed_elo | 70 | 22.7% | 79.3% | 10.3% | 52.9% |
| market | 70 | 28.6% | 76.0% | 8.3% | 68.6% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 68 | 52.0% | 60.3% | 48.4% to 71.1% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 5 | 32.0% | 20.0% | 3.6% to 62.4% |
| fixed_elo | 40%–60% | 37 | 51.4% | 59.5% | 43.5% to 73.7% |
| fixed_elo | 60%–80% | 28 | 66.5% | 67.9% | 49.3% to 82.1% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 6 | 34.3% | 33.3% | 9.7% to 70.0% |
| market (paired only) | 40%–60% | 48 | 53.1% | 58.3% | 44.3% to 71.2% |
| market (paired only) | 60%–80% | 16 | 66.3% | 75.0% | 50.5% to 89.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261022T151855730873Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
