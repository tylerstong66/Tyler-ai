# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **193** · Settled: **181** · Pending: **12**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-07T20:53:09.976697+00:00 (UTC).

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
| model | 181 | 28 | 0.4811 | 0.6741 | 59.7% | 0.4695 to 0.4931 | 0.6624 to 0.6862 | 53.2% to 66.7% |
| fixed_elo | 181 | 28 | 0.4671 | 0.6593 | 58.6% | 0.4351 to 0.4998 | 0.6256 to 0.6942 | 51.4% to 65.6% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 181 | 28 | 0.4811 | 0.6741 | 59.7% | 0.4695 to 0.4931 | 0.6624 to 0.6862 | 53.2% to 66.7% |
| fixed_elo | 181 | 28 | 0.4671 | 0.6593 | 58.6% | 0.4351 to 0.4998 | 0.6256 to 0.6942 | 51.4% to 65.6% |
| market | 181 | 28 | 0.4597 | 0.6512 | 57.5% | 0.4380 to 0.4816 | 0.6287 to 0.6740 | 50.6% to 64.4% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 181 | 28 | 0.0140 | -0.0070 to 0.0345 | 0.0148 | -0.0080 to 0.0369 | 1.1 pp | -1.1 pp to 3.3 pp |
| market | 181 | 28 | 0.0214 | 0.0084 to 0.0349 | 0.0229 | 0.0092 to 0.0370 | 2.2 pp | -4.5 pp to 8.4 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 181 | 39.1% | 62.9% | 3.6% | 97.8% |
| fixed_elo | 181 | 22.7% | 82.1% | 10.2% | 56.4% |
| market | 181 | 28.6% | 77.2% | 8.2% | 65.7% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 177 | 51.9% | 57.1% | 49.7% to 64.1% |
| model | 60%–80% | 3 | 61.6% | 100.0% | 43.9% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 9 | 32.7% | 22.2% | 6.3% to 54.7% |
| fixed_elo | 40%–60% | 102 | 50.9% | 53.9% | 44.3% to 63.3% |
| fixed_elo | 60%–80% | 69 | 66.9% | 66.7% | 54.9% to 76.6% |
| fixed_elo | 80%–100% | 1 | 82.1% | 100.0% | 20.7% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 15 | 36.0% | 40.0% | 19.8% to 64.3% |
| market (paired only) | 40%–60% | 119 | 51.1% | 52.9% | 44.0% to 61.7% |
| market (paired only) | 60%–80% | 47 | 65.6% | 74.5% | 60.5% to 84.7% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261107T205308687859Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
