# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **245** · Settled: **231** · Pending: **14**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-15T02:39:57.160269+00:00 (UTC).

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
| model | 231 | 35 | 0.4805 | 0.6735 | 58.9% | 0.4699 to 0.4911 | 0.6627 to 0.6841 | 53.2% to 64.7% |
| fixed_elo | 231 | 35 | 0.4678 | 0.6596 | 58.0% | 0.4392 to 0.4962 | 0.6294 to 0.6900 | 51.9% to 64.1% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 231 | 35 | 0.4805 | 0.6735 | 58.9% | 0.4699 to 0.4911 | 0.6627 to 0.6841 | 53.2% to 64.7% |
| fixed_elo | 231 | 35 | 0.4678 | 0.6596 | 58.0% | 0.4392 to 0.4962 | 0.6294 to 0.6900 | 51.9% to 64.1% |
| market | 231 | 35 | 0.4572 | 0.6484 | 58.9% | 0.4374 to 0.4764 | 0.6276 to 0.6684 | 52.3% to 65.2% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 231 | 35 | 0.0127 | -0.0055 to 0.0309 | 0.0139 | -0.0062 to 0.0337 | 0.9 pp | -0.8 pp to 2.6 pp |
| market | 231 | 35 | 0.0233 | 0.0115 to 0.0349 | 0.0250 | 0.0127 to 0.0374 | 0.0 pp | -5.9 pp to 6.1 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 231 | 39.1% | 65.3% | 3.7% | 97.0% |
| fixed_elo | 231 | 22.7% | 86.1% | 10.4% | 57.1% |
| market | 231 | 28.6% | 78.2% | 8.1% | 67.5% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 224 | 51.8% | 52.7% | 46.2% to 59.1% |
| model | 60%–80% | 6 | 62.2% | 100.0% | 61.0% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 13 | 32.9% | 23.1% | 8.2% to 50.3% |
| fixed_elo | 40%–60% | 132 | 51.2% | 47.0% | 38.7% to 55.4% |
| fixed_elo | 60%–80% | 84 | 67.1% | 67.9% | 57.3% to 76.9% |
| fixed_elo | 80%–100% | 2 | 84.1% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 18 | 35.6% | 33.3% | 16.3% to 56.3% |
| market (paired only) | 40%–60% | 156 | 50.7% | 48.7% | 41.0% to 56.5% |
| market (paired only) | 60%–80% | 57 | 66.0% | 73.7% | 61.0% to 83.4% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261115T023955322592Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
