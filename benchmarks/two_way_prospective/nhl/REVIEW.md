# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **142** · Settled: **132** · Pending: **10**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-31T05:42:05.470560+00:00 (UTC).

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
| model | 132 | 20 | 0.4834 | 0.6765 | 59.1% | 0.4695 to 0.4982 | 0.6625 to 0.6913 | 50.7% to 67.9% |
| fixed_elo | 132 | 20 | 0.4717 | 0.6643 | 57.6% | 0.4341 to 0.5134 | 0.6242 to 0.7081 | 48.4% to 66.9% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 132 | 20 | 0.4834 | 0.6765 | 59.1% | 0.4695 to 0.4982 | 0.6625 to 0.6913 | 50.7% to 67.9% |
| fixed_elo | 132 | 20 | 0.4717 | 0.6643 | 57.6% | 0.4341 to 0.5134 | 0.6242 to 0.7081 | 48.4% to 66.9% |
| market | 132 | 20 | 0.4654 | 0.6573 | 56.1% | 0.4402 to 0.4913 | 0.6312 to 0.6839 | 48.7% to 63.0% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 132 | 20 | 0.0117 | -0.0148 to 0.0357 | 0.0122 | -0.0165 to 0.0381 | 1.5 pp | -1.4 pp to 4.5 pp |
| market | 132 | 20 | 0.0181 | 0.0039 to 0.0314 | 0.0192 | 0.0039 to 0.0334 | 3.0 pp | -3.8 pp to 9.9 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 132 | 39.1% | 61.4% | 3.5% | 98.5% |
| fixed_elo | 132 | 22.7% | 79.3% | 10.0% | 56.1% |
| market | 132 | 28.6% | 76.0% | 8.0% | 66.7% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 130 | 52.1% | 59.2% | 50.6% to 67.3% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 6 | 32.1% | 16.7% | 3.0% to 56.4% |
| fixed_elo | 40%–60% | 74 | 51.1% | 58.1% | 46.7% to 68.7% |
| fixed_elo | 60%–80% | 52 | 66.7% | 65.4% | 51.8% to 76.8% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 11 | 35.5% | 36.4% | 15.2% to 64.6% |
| market (paired only) | 40%–60% | 88 | 51.7% | 55.7% | 45.3% to 65.6% |
| market (paired only) | 60%–80% | 33 | 65.2% | 75.8% | 59.0% to 87.2% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261031T174409525947Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
