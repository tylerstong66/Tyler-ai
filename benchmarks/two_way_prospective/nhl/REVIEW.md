# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **166** · Settled: **162** · Pending: **4**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-04T09:13:18.173741+00:00 (UTC).

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
| model | 162 | 24 | 0.4835 | 0.6766 | 58.0% | 0.4705 to 0.4966 | 0.6635 to 0.6897 | 51.2% to 65.6% |
| fixed_elo | 162 | 24 | 0.4733 | 0.6659 | 56.8% | 0.4379 to 0.5093 | 0.6283 to 0.7039 | 49.1% to 64.6% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 162 | 24 | 0.4835 | 0.6766 | 58.0% | 0.4705 to 0.4966 | 0.6635 to 0.6897 | 51.2% to 65.6% |
| fixed_elo | 162 | 24 | 0.4733 | 0.6659 | 56.8% | 0.4379 to 0.5093 | 0.6283 to 0.7039 | 49.1% to 64.6% |
| market | 162 | 24 | 0.4629 | 0.6546 | 56.8% | 0.4387 to 0.4872 | 0.6295 to 0.6796 | 48.8% to 64.6% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 162 | 24 | 0.0102 | -0.0132 to 0.0326 | 0.0107 | -0.0147 to 0.0352 | 1.2 pp | -1.2 pp to 3.6 pp |
| market | 162 | 24 | 0.0206 | 0.0065 to 0.0342 | 0.0220 | 0.0072 to 0.0364 | 1.2 pp | -5.7 pp to 8.5 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 162 | 39.1% | 62.9% | 3.6% | 98.1% |
| fixed_elo | 162 | 22.7% | 82.1% | 10.0% | 58.0% |
| market | 162 | 28.6% | 77.2% | 8.1% | 66.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 159 | 51.9% | 56.6% | 48.8% to 64.1% |
| model | 60%–80% | 2 | 62.1% | 100.0% | 34.2% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 8 | 32.3% | 25.0% | 7.1% to 59.1% |
| fixed_elo | 40%–60% | 94 | 50.8% | 53.2% | 43.2% to 63.0% |
| fixed_elo | 60%–80% | 59 | 67.0% | 66.1% | 53.4% to 76.9% |
| fixed_elo | 80%–100% | 1 | 82.1% | 100.0% | 20.7% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 15 | 36.0% | 40.0% | 19.8% to 64.3% |
| market (paired only) | 40%–60% | 107 | 51.1% | 52.3% | 43.0% to 61.6% |
| market (paired only) | 60%–80% | 40 | 65.5% | 75.0% | 59.8% to 85.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261104T171930219385Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
