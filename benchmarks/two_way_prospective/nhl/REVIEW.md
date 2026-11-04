# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **164** · Settled: **151** · Pending: **13**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-03T06:48:04.463485+00:00 (UTC).

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
| model | 151 | 23 | 0.4814 | 0.6744 | 58.3% | 0.4686 to 0.4952 | 0.6615 to 0.6883 | 50.8% to 66.2% |
| fixed_elo | 151 | 23 | 0.4675 | 0.6595 | 57.0% | 0.4321 to 0.5053 | 0.6218 to 0.6993 | 49.1% to 65.1% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 151 | 23 | 0.4814 | 0.6744 | 58.3% | 0.4686 to 0.4952 | 0.6615 to 0.6883 | 50.8% to 66.2% |
| fixed_elo | 151 | 23 | 0.4675 | 0.6595 | 57.0% | 0.4321 to 0.5053 | 0.6218 to 0.6993 | 49.1% to 65.1% |
| market | 151 | 23 | 0.4619 | 0.6534 | 56.3% | 0.4373 to 0.4872 | 0.6278 to 0.6796 | 48.1% to 64.2% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 151 | 23 | 0.0138 | -0.0103 to 0.0367 | 0.0149 | -0.0111 to 0.0396 | 1.3 pp | -1.2 pp to 3.7 pp |
| market | 151 | 23 | 0.0195 | 0.0050 to 0.0335 | 0.0209 | 0.0057 to 0.0358 | 2.0 pp | -5.3 pp to 9.2 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 151 | 39.1% | 62.9% | 3.6% | 98.0% |
| fixed_elo | 151 | 22.7% | 82.1% | 10.0% | 57.0% |
| market | 151 | 28.6% | 77.2% | 8.1% | 66.2% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 148 | 52.0% | 57.4% | 49.4% to 65.1% |
| model | 60%–80% | 2 | 62.1% | 100.0% | 34.2% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 7 | 32.6% | 14.3% | 2.6% to 51.3% |
| fixed_elo | 40%–60% | 86 | 51.0% | 54.7% | 44.2% to 64.7% |
| fixed_elo | 60%–80% | 57 | 66.8% | 66.7% | 53.7% to 77.5% |
| fixed_elo | 80%–100% | 1 | 82.1% | 100.0% | 20.7% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 13 | 35.7% | 38.5% | 17.7% to 64.5% |
| market (paired only) | 40%–60% | 100 | 51.3% | 53.0% | 43.3% to 62.5% |
| market (paired only) | 60%–80% | 38 | 65.5% | 76.3% | 60.8% to 87.0% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261104T012222180391Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
