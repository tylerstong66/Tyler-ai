# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **51** · Settled: **37** · Pending: **14**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-17T09:22:15.570212+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 51 / 100; settled among selected: 37; pending among selected: 14.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 37 | 6 | 0.4761 | 0.6691 | 59.5% | 0.4536 to 0.4947 | 0.6465 to 0.6878 | 46.3% to 79.2% |
| fixed_elo | 37 | 6 | 0.4535 | 0.6446 | 54.1% | 0.3899 to 0.5053 | 0.5781 to 0.6983 | 40.0% to 70.0% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 37 | 6 | 0.4761 | 0.6691 | 59.5% | 0.4536 to 0.4947 | 0.6465 to 0.6878 | 46.3% to 79.2% |
| fixed_elo | 37 | 6 | 0.4535 | 0.6446 | 54.1% | 0.3899 to 0.5053 | 0.5781 to 0.6983 | 40.0% to 70.0% |
| market | 37 | 6 | 0.4572 | 0.6483 | 54.1% | 0.4013 to 0.5009 | 0.5896 to 0.6939 | 43.9% to 69.6% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 37 | 6 | 0.0226 | -0.0109 to 0.0641 | 0.0245 | -0.0110 to 0.0690 | 5.4 pp | 0.0 pp to 13.8 pp |
| market | 37 | 6 | 0.0189 | -0.0140 to 0.0542 | 0.0208 | -0.0138 to 0.0582 | 5.4 pp | -9.1 pp to 24.3 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 37 | 44.1% | 58.9% | 3.5% | 100.0% |
| fixed_elo | 37 | 34.7% | 74.1% | 9.9% | 56.8% |
| market | 37 | 34.3% | 72.2% | 7.8% | 75.7% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 37 | 52.4% | 54.1% | 38.4% to 69.0% |
| model | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 1 | 34.7% | 0.0% | 0.0% to 79.3% |
| fixed_elo | 40%–60% | 21 | 51.3% | 42.9% | 24.5% to 63.5% |
| fixed_elo | 60%–80% | 15 | 67.1% | 73.3% | 48.0% to 89.1% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 1 | 34.3% | 0.0% | 0.0% to 79.3% |
| market (paired only) | 40%–60% | 28 | 52.4% | 50.0% | 32.6% to 67.4% |
| market (paired only) | 60%–80% | 8 | 67.9% | 75.0% | 40.9% to 92.9% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261017T192537251604Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
