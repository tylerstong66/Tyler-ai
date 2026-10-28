# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **118** · Settled: **104** · Pending: **14**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-28T02:15:59.154316+00:00 (UTC).

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
| model | 104 | 17 | 0.4846 | 0.6777 | 59.6% | 0.4694 to 0.5005 | 0.6624 to 0.6937 | 50.7% to 69.1% |
| fixed_elo | 104 | 17 | 0.4739 | 0.6667 | 58.7% | 0.4326 to 0.5185 | 0.6238 to 0.7136 | 50.0% to 67.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 104 | 17 | 0.4846 | 0.6777 | 59.6% | 0.4694 to 0.5005 | 0.6624 to 0.6937 | 50.7% to 69.1% |
| fixed_elo | 104 | 17 | 0.4739 | 0.6667 | 58.7% | 0.4326 to 0.5185 | 0.6238 to 0.7136 | 50.0% to 67.7% |
| market | 104 | 17 | 0.4711 | 0.6631 | 55.8% | 0.4436 to 0.5018 | 0.6347 to 0.6950 | 47.3% to 64.1% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 104 | 17 | 0.0107 | -0.0181 to 0.0371 | 0.0109 | -0.0201 to 0.0393 | 1.0 pp | -2.2 pp to 4.5 pp |
| market | 104 | 17 | 0.0135 | -0.0057 to 0.0283 | 0.0145 | -0.0058 to 0.0302 | 3.8 pp | -3.4 pp to 10.8 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 104 | 39.1% | 61.4% | 3.5% | 98.1% |
| fixed_elo | 104 | 22.7% | 79.3% | 10.0% | 55.8% |
| market | 104 | 28.6% | 76.0% | 8.1% | 68.3% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 102 | 51.8% | 60.8% | 51.1% to 69.7% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 6 | 32.1% | 16.7% | 3.0% to 56.4% |
| fixed_elo | 40%–60% | 58 | 50.7% | 62.1% | 49.2% to 73.4% |
| fixed_elo | 60%–80% | 40 | 66.4% | 65.0% | 49.5% to 77.9% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 11 | 35.5% | 36.4% | 15.2% to 64.6% |
| market (paired only) | 40%–60% | 71 | 52.0% | 60.6% | 48.9% to 71.1% |
| market (paired only) | 60%–80% | 22 | 65.5% | 72.7% | 51.8% to 86.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261028T021557056278Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
