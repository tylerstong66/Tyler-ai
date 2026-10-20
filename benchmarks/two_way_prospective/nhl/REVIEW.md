# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **68** · Settled: **57** · Pending: **11**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-20T06:01:39.547814+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 68 / 100; settled among selected: 57; pending among selected: 11.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 57 | 9 | 0.4736 | 0.6666 | 63.2% | 0.4567 to 0.4945 | 0.6496 to 0.6876 | 49.3% to 75.8% |
| fixed_elo | 57 | 9 | 0.4444 | 0.6355 | 59.6% | 0.3987 to 0.5021 | 0.5874 to 0.6967 | 44.2% to 72.9% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 57 | 9 | 0.4736 | 0.6666 | 63.2% | 0.4567 to 0.4945 | 0.6496 to 0.6876 | 49.3% to 75.8% |
| fixed_elo | 57 | 9 | 0.4444 | 0.6355 | 59.6% | 0.3987 to 0.5021 | 0.5874 to 0.6967 | 44.2% to 72.9% |
| market | 57 | 9 | 0.4527 | 0.6439 | 57.9% | 0.4147 to 0.4966 | 0.6040 to 0.6904 | 48.3% to 68.8% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 57 | 9 | 0.0292 | -0.0076 to 0.0587 | 0.0311 | -0.0093 to 0.0629 | 3.5 pp | 0.0 pp to 8.7 pp |
| market | 57 | 9 | 0.0208 | -0.0040 to 0.0436 | 0.0227 | -0.0037 to 0.0473 | 5.3 pp | -7.7 pp to 16.7 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 57 | 41.5% | 61.4% | 3.5% | 98.2% |
| fixed_elo | 57 | 28.1% | 79.3% | 10.0% | 54.4% |
| market | 57 | 34.3% | 76.0% | 8.5% | 68.4% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 56 | 51.7% | 60.7% | 47.6% to 72.4% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 4 | 34.3% | 25.0% | 4.6% to 69.9% |
| fixed_elo | 40%–60% | 31 | 50.7% | 54.8% | 37.8% to 70.8% |
| fixed_elo | 60%–80% | 22 | 66.7% | 77.3% | 56.6% to 89.9% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 5 | 35.5% | 40.0% | 11.8% to 76.9% |
| market (paired only) | 40%–60% | 39 | 52.8% | 56.4% | 41.0% to 70.7% |
| market (paired only) | 60%–80% | 13 | 67.3% | 84.6% | 57.8% to 95.7% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261020T113755111417Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
