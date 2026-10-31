# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **145** · Settled: **136** · Pending: **9**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-31T21:35:37.671835+00:00 (UTC).

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
| model | 136 | 21 | 0.4834 | 0.6764 | 58.1% | 0.4696 to 0.4974 | 0.6626 to 0.6905 | 50.0% to 66.9% |
| fixed_elo | 136 | 21 | 0.4720 | 0.6644 | 56.6% | 0.4345 to 0.5103 | 0.6250 to 0.7046 | 47.6% to 65.8% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 136 | 21 | 0.4834 | 0.6764 | 58.1% | 0.4696 to 0.4974 | 0.6626 to 0.6905 | 50.0% to 66.9% |
| fixed_elo | 136 | 21 | 0.4720 | 0.6644 | 56.6% | 0.4345 to 0.5103 | 0.6250 to 0.7046 | 47.6% to 65.8% |
| market | 136 | 21 | 0.4651 | 0.6570 | 56.6% | 0.4402 to 0.4902 | 0.6313 to 0.6828 | 49.6% to 63.6% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 136 | 21 | 0.0114 | -0.0130 to 0.0356 | 0.0120 | -0.0142 to 0.0378 | 1.5 pp | -1.4 pp to 4.3 pp |
| market | 136 | 21 | 0.0183 | 0.0043 to 0.0312 | 0.0194 | 0.0046 to 0.0331 | 1.5 pp | -5.7 pp to 8.5 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 136 | 39.1% | 61.4% | 3.5% | 98.5% |
| fixed_elo | 136 | 22.7% | 79.3% | 10.0% | 56.6% |
| market | 136 | 28.6% | 76.0% | 8.0% | 66.2% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 134 | 52.1% | 59.0% | 50.5% to 66.9% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 6 | 32.1% | 16.7% | 3.0% to 56.4% |
| fixed_elo | 40%–60% | 77 | 51.0% | 57.1% | 46.0% to 67.6% |
| fixed_elo | 60%–80% | 53 | 66.8% | 66.0% | 52.6% to 77.3% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 12 | 35.9% | 41.7% | 19.3% to 68.0% |
| market (paired only) | 40%–60% | 90 | 51.5% | 54.4% | 44.2% to 64.3% |
| market (paired only) | 60%–80% | 34 | 65.2% | 76.5% | 60.0% to 87.6% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261031T213535704102Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
