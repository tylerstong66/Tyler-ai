# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **261** · Settled: **258** · Pending: **3**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-18T13:58:50.312359+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **preserved**. This is separate from the cumulative 100-settlement flag.
Selected: 100 / 100; settled among selected: 100; pending among selected: 0.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.
[Preserved checkpoint review](checkpoints/first_100_enrolled/REVIEW.md). Later games do not change this window.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 258 | 38 | 0.4846 | 0.6777 | 57.4% | 0.4744 to 0.4955 | 0.6673 to 0.6887 | 51.7% to 63.0% |
| fixed_elo | 258 | 38 | 0.4787 | 0.6721 | 56.2% | 0.4514 to 0.5090 | 0.6425 to 0.7044 | 50.2% to 62.2% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 258 | 38 | 0.4846 | 0.6777 | 57.4% | 0.4744 to 0.4955 | 0.6673 to 0.6887 | 51.7% to 63.0% |
| fixed_elo | 258 | 38 | 0.4787 | 0.6721 | 56.2% | 0.4514 to 0.5090 | 0.6425 to 0.7044 | 50.2% to 62.2% |
| market | 258 | 38 | 0.4661 | 0.6581 | 58.1% | 0.4469 to 0.4867 | 0.6379 to 0.6796 | 52.2% to 63.8% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 258 | 38 | 0.0060 | -0.0134 to 0.0233 | 0.0056 | -0.0161 to 0.0249 | 1.2 pp | -0.4 pp to 2.9 pp |
| market | 258 | 38 | 0.0185 | 0.0070 to 0.0298 | 0.0196 | 0.0071 to 0.0317 | -0.8 pp | -6.4 pp to 5.3 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 258 | 39.1% | 65.3% | 3.7% | 96.5% |
| fixed_elo | 258 | 22.7% | 86.1% | 10.4% | 57.0% |
| market | 258 | 28.6% | 78.2% | 8.1% | 68.2% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 249 | 51.8% | 51.8% | 45.6% to 57.9% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 14 | 33.4% | 21.4% | 7.6% to 47.6% |
| fixed_elo | 40%–60% | 147 | 51.2% | 46.3% | 38.4% to 54.3% |
| fixed_elo | 60%–80% | 94 | 66.9% | 66.0% | 55.9% to 74.7% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 19 | 35.9% | 36.8% | 19.1% to 59.0% |
| market (paired only) | 40%–60% | 176 | 50.7% | 47.7% | 40.5% to 55.1% |
| market (paired only) | 60%–80% | 63 | 66.1% | 69.8% | 57.6% to 79.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261118T215721639070Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
