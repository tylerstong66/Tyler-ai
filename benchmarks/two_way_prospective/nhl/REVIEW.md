# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **207** · Settled: **200** · Pending: **7**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-10T09:51:37.648072+00:00 (UTC).

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
| model | 200 | 30 | 0.4776 | 0.6706 | 61.0% | 0.4652 to 0.4899 | 0.6581 to 0.6830 | 54.5% to 67.3% |
| fixed_elo | 200 | 30 | 0.4588 | 0.6502 | 60.0% | 0.4268 to 0.4917 | 0.6160 to 0.6854 | 52.9% to 66.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 200 | 30 | 0.4776 | 0.6706 | 61.0% | 0.4652 to 0.4899 | 0.6581 to 0.6830 | 54.5% to 67.3% |
| fixed_elo | 200 | 30 | 0.4588 | 0.6502 | 60.0% | 0.4268 to 0.4917 | 0.6160 to 0.6854 | 52.9% to 66.7% |
| market | 200 | 30 | 0.4542 | 0.6454 | 59.0% | 0.4312 to 0.4761 | 0.6212 to 0.6681 | 52.4% to 66.1% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 200 | 30 | 0.0188 | -0.0018 to 0.0388 | 0.0203 | -0.0021 to 0.0422 | 1.0 pp | -0.9 pp to 2.9 pp |
| market | 200 | 30 | 0.0234 | 0.0105 to 0.0363 | 0.0252 | 0.0115 to 0.0389 | 2.0 pp | -3.8 pp to 8.0 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 200 | 39.1% | 65.3% | 3.7% | 97.0% |
| fixed_elo | 200 | 22.7% | 86.1% | 10.4% | 57.0% |
| market | 200 | 28.6% | 78.2% | 8.2% | 67.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 194 | 51.9% | 56.7% | 49.7% to 63.5% |
| model | 60%–80% | 5 | 62.3% | 100.0% | 56.6% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 9 | 32.7% | 22.2% | 6.3% to 54.7% |
| fixed_elo | 40%–60% | 114 | 50.9% | 51.8% | 42.7% to 60.7% |
| fixed_elo | 60%–80% | 75 | 67.0% | 69.3% | 58.2% to 78.6% |
| fixed_elo | 80%–100% | 2 | 84.1% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 15 | 36.0% | 40.0% | 19.8% to 64.3% |
| market (paired only) | 40%–60% | 134 | 50.8% | 52.2% | 43.8% to 60.5% |
| market (paired only) | 60%–80% | 51 | 66.2% | 76.5% | 63.2% to 86.0% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261110T232242106711Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
