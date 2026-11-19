# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **273** · Settled: **260** · Pending: **13**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-19T03:28:24.151589+00:00 (UTC).

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
| model | 260 | 39 | 0.4848 | 0.6779 | 57.3% | 0.4747 to 0.4953 | 0.6676 to 0.6885 | 51.6% to 63.1% |
| fixed_elo | 260 | 39 | 0.4792 | 0.6726 | 56.2% | 0.4506 to 0.5075 | 0.6428 to 0.7033 | 50.2% to 62.2% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 260 | 39 | 0.4848 | 0.6779 | 57.3% | 0.4747 to 0.4953 | 0.6676 to 0.6885 | 51.6% to 63.1% |
| fixed_elo | 260 | 39 | 0.4792 | 0.6726 | 56.2% | 0.4506 to 0.5075 | 0.6428 to 0.7033 | 50.2% to 62.2% |
| market | 260 | 39 | 0.4672 | 0.6593 | 57.7% | 0.4477 to 0.4871 | 0.6387 to 0.6802 | 51.8% to 63.4% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 260 | 39 | 0.0056 | -0.0129 to 0.0234 | 0.0052 | -0.0151 to 0.0248 | 1.2 pp | -0.4 pp to 2.9 pp |
| market | 260 | 39 | 0.0176 | 0.0057 to 0.0287 | 0.0186 | 0.0058 to 0.0303 | -0.4 pp | -6.3 pp to 5.7 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 260 | 39.1% | 65.3% | 3.7% | 96.5% |
| fixed_elo | 260 | 22.7% | 86.1% | 10.3% | 56.9% |
| market | 260 | 28.6% | 78.2% | 8.1% | 68.5% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 251 | 51.8% | 51.4% | 45.2% to 57.5% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 14 | 33.4% | 21.4% | 7.6% to 47.6% |
| fixed_elo | 40%–60% | 148 | 51.2% | 45.9% | 38.1% to 54.0% |
| fixed_elo | 60%–80% | 95 | 66.8% | 65.3% | 55.3% to 74.1% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 19 | 35.9% | 36.8% | 19.1% to 59.0% |
| market (paired only) | 40%–60% | 178 | 50.7% | 47.2% | 40.0% to 54.5% |
| market (paired only) | 60%–80% | 63 | 66.1% | 69.8% | 57.6% to 79.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261119T032819335740Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
