# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **289** · Settled: **274** · Pending: **15**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-21T23:16:37.556142+00:00 (UTC).

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
| model | 274 | 41 | 0.4853 | 0.6784 | 57.3% | 0.4757 to 0.4956 | 0.6687 to 0.6888 | 51.9% to 62.8% |
| fixed_elo | 274 | 41 | 0.4807 | 0.6742 | 56.2% | 0.4542 to 0.5093 | 0.6461 to 0.7047 | 50.3% to 62.1% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 274 | 41 | 0.4853 | 0.6784 | 57.3% | 0.4757 to 0.4956 | 0.6687 to 0.6888 | 51.9% to 62.8% |
| fixed_elo | 274 | 41 | 0.4807 | 0.6742 | 56.2% | 0.4542 to 0.5093 | 0.6461 to 0.7047 | 50.3% to 62.1% |
| market | 274 | 41 | 0.4682 | 0.6603 | 57.3% | 0.4485 to 0.4872 | 0.6398 to 0.6803 | 51.6% to 62.7% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 274 | 41 | 0.0046 | -0.0135 to 0.0215 | 0.0041 | -0.0160 to 0.0228 | 1.1 pp | -0.4 pp to 2.7 pp |
| market | 274 | 41 | 0.0172 | 0.0064 to 0.0284 | 0.0181 | 0.0065 to 0.0302 | 0.0 pp | -5.6 pp to 5.8 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 274 | 39.1% | 65.3% | 3.7% | 96.7% |
| fixed_elo | 274 | 22.7% | 86.1% | 10.4% | 56.6% |
| market | 274 | 28.6% | 78.2% | 8.0% | 68.2% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 265 | 51.8% | 50.9% | 45.0% to 56.9% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 15 | 33.7% | 20.0% | 7.0% to 45.2% |
| fixed_elo | 40%–60% | 155 | 51.2% | 45.8% | 38.2% to 53.7% |
| fixed_elo | 60%–80% | 101 | 66.9% | 64.4% | 54.6% to 73.0% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 20 | 35.8% | 35.0% | 18.1% to 56.7% |
| market (paired only) | 40%–60% | 187 | 50.7% | 47.1% | 40.0% to 54.2% |
| market (paired only) | 60%–80% | 67 | 66.0% | 68.7% | 56.8% to 78.5% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261121T231636425209Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
