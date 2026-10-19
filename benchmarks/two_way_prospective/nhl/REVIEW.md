# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **57** · Settled: **53** · Pending: **4**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-19T07:47:15.834582+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 57 / 100; settled among selected: 53; pending among selected: 4.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 53 | 8 | 0.4726 | 0.6656 | 64.2% | 0.4551 to 0.4955 | 0.6480 to 0.6886 | 50.0% to 77.5% |
| fixed_elo | 53 | 8 | 0.4434 | 0.6344 | 60.4% | 0.3950 to 0.5056 | 0.5837 to 0.7004 | 43.9% to 73.9% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 53 | 8 | 0.4726 | 0.6656 | 64.2% | 0.4551 to 0.4955 | 0.6480 to 0.6886 | 50.0% to 77.5% |
| fixed_elo | 53 | 8 | 0.4434 | 0.6344 | 60.4% | 0.3950 to 0.5056 | 0.5837 to 0.7004 | 43.9% to 73.9% |
| market | 53 | 8 | 0.4504 | 0.6412 | 56.6% | 0.4107 to 0.4990 | 0.5996 to 0.6922 | 47.1% to 67.4% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 53 | 8 | 0.0291 | -0.0107 to 0.0603 | 0.0312 | -0.0132 to 0.0645 | 3.8 pp | 0.0 pp to 10.0 pp |
| market | 53 | 8 | 0.0221 | -0.0055 to 0.0461 | 0.0243 | -0.0049 to 0.0500 | 7.5 pp | -3.9 pp to 19.1 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 53 | 41.5% | 61.4% | 3.6% | 98.1% |
| fixed_elo | 53 | 28.1% | 79.3% | 10.2% | 52.8% |
| market | 53 | 34.3% | 76.0% | 8.4% | 69.8% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 52 | 51.7% | 57.7% | 44.2% to 70.1% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 4 | 34.3% | 25.0% | 4.6% to 69.9% |
| fixed_elo | 40%–60% | 28 | 50.9% | 50.0% | 32.6% to 67.4% |
| fixed_elo | 60%–80% | 21 | 66.9% | 76.2% | 54.9% to 89.4% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 4 | 35.8% | 25.0% | 4.6% to 69.9% |
| market (paired only) | 40%–60% | 37 | 52.6% | 54.1% | 38.4% to 69.0% |
| market (paired only) | 60%–80% | 12 | 67.7% | 83.3% | 55.2% to 95.3% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261019T153630557349Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
