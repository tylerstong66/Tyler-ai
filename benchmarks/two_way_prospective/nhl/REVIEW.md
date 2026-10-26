# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **103** · Settled: **100** · Pending: **3**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-26T06:16:46.830983+00:00 (UTC).

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
| model | 100 | 15 | 0.4817 | 0.6747 | 61.0% | 0.4657 to 0.4971 | 0.6587 to 0.6902 | 51.8% to 71.2% |
| fixed_elo | 100 | 15 | 0.4653 | 0.6578 | 60.0% | 0.4219 to 0.5081 | 0.6118 to 0.7033 | 50.4% to 69.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 100 | 15 | 0.4817 | 0.6747 | 61.0% | 0.4657 to 0.4971 | 0.6587 to 0.6902 | 51.8% to 71.2% |
| fixed_elo | 100 | 15 | 0.4653 | 0.6578 | 60.0% | 0.4219 to 0.5081 | 0.6118 to 0.7033 | 50.4% to 69.7% |
| market | 100 | 15 | 0.4646 | 0.6566 | 57.0% | 0.4362 to 0.4921 | 0.6267 to 0.6852 | 49.4% to 65.2% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 100 | 15 | 0.0163 | -0.0113 to 0.0442 | 0.0169 | -0.0129 to 0.0468 | 1.0 pp | -2.3 pp to 4.7 pp |
| market | 100 | 15 | 0.0170 | 0.0013 to 0.0319 | 0.0181 | 0.0014 to 0.0341 | 4.0 pp | -2.4 pp to 10.9 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 100 | 39.1% | 61.4% | 3.5% | 98.0% |
| fixed_elo | 100 | 22.7% | 79.3% | 9.9% | 56.0% |
| market | 100 | 28.6% | 76.0% | 8.1% | 68.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 98 | 51.7% | 62.2% | 52.4% to 71.2% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 6 | 32.1% | 16.7% | 3.0% to 56.4% |
| fixed_elo | 40%–60% | 56 | 50.6% | 62.5% | 49.4% to 74.0% |
| fixed_elo | 60%–80% | 38 | 66.4% | 68.4% | 52.5% to 80.9% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 11 | 35.5% | 36.4% | 15.2% to 64.6% |
| market (paired only) | 40%–60% | 68 | 52.2% | 61.8% | 49.9% to 72.4% |
| market (paired only) | 60%–80% | 21 | 65.7% | 76.2% | 54.9% to 89.4% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261026T141648607579Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
