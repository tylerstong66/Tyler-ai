# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **180** · Settled: **176** · Pending: **4**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-06T10:53:13.815832+00:00 (UTC).

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
| model | 176 | 26 | 0.4822 | 0.6752 | 59.1% | 0.4700 to 0.4941 | 0.6629 to 0.6872 | 52.7% to 65.9% |
| fixed_elo | 176 | 26 | 0.4702 | 0.6626 | 58.0% | 0.4375 to 0.5025 | 0.6277 to 0.6970 | 50.8% to 65.1% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 176 | 26 | 0.4822 | 0.6752 | 59.1% | 0.4700 to 0.4941 | 0.6629 to 0.6872 | 52.7% to 65.9% |
| fixed_elo | 176 | 26 | 0.4702 | 0.6626 | 58.0% | 0.4375 to 0.5025 | 0.6277 to 0.6970 | 50.8% to 65.1% |
| market | 176 | 26 | 0.4615 | 0.6531 | 56.8% | 0.4389 to 0.4836 | 0.6294 to 0.6761 | 50.0% to 64.2% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 176 | 26 | 0.0120 | -0.0086 to 0.0329 | 0.0127 | -0.0099 to 0.0354 | 1.1 pp | -1.0 pp to 3.3 pp |
| market | 176 | 26 | 0.0207 | 0.0078 to 0.0338 | 0.0222 | 0.0085 to 0.0360 | 2.3 pp | -4.8 pp to 8.8 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 176 | 39.1% | 62.9% | 3.6% | 97.7% |
| fixed_elo | 176 | 22.7% | 82.1% | 10.1% | 56.8% |
| market | 176 | 28.6% | 77.2% | 8.2% | 65.9% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 172 | 51.9% | 56.4% | 48.9% to 63.6% |
| model | 60%–80% | 3 | 61.6% | 100.0% | 43.9% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 9 | 32.7% | 22.2% | 6.3% to 54.7% |
| fixed_elo | 40%–60% | 100 | 50.8% | 54.0% | 44.3% to 63.4% |
| fixed_elo | 60%–80% | 66 | 67.0% | 65.2% | 53.1% to 75.5% |
| fixed_elo | 80%–100% | 1 | 82.1% | 100.0% | 20.7% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 15 | 36.0% | 40.0% | 19.8% to 64.3% |
| market (paired only) | 40%–60% | 116 | 51.1% | 52.6% | 43.6% to 61.4% |
| market (paired only) | 60%–80% | 45 | 65.6% | 73.3% | 59.0% to 84.0% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261106T175755344477Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
