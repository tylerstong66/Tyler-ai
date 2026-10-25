# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **100** · Settled: **96** · Pending: **4**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-25T06:09:17.757516+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **awaiting_selected_results**. This is separate from the cumulative 100-settlement flag.
Selected: 100 / 100; settled among selected: 96; pending among selected: 4.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 96 | 14 | 0.4833 | 0.6763 | 60.4% | 0.4674 to 0.4987 | 0.6604 to 0.6919 | 51.2% to 71.3% |
| fixed_elo | 96 | 14 | 0.4697 | 0.6623 | 59.4% | 0.4253 to 0.5130 | 0.6159 to 0.7083 | 50.0% to 69.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 96 | 14 | 0.4833 | 0.6763 | 60.4% | 0.4674 to 0.4987 | 0.6604 to 0.6919 | 51.2% to 71.3% |
| fixed_elo | 96 | 14 | 0.4697 | 0.6623 | 59.4% | 0.4253 to 0.5130 | 0.6159 to 0.7083 | 50.0% to 69.7% |
| market | 96 | 14 | 0.4658 | 0.6576 | 56.2% | 0.4366 to 0.4937 | 0.6272 to 0.6871 | 48.6% to 64.8% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 96 | 14 | 0.0136 | -0.0147 to 0.0422 | 0.0140 | -0.0168 to 0.0443 | 1.0 pp | -2.4 pp to 4.9 pp |
| market | 96 | 14 | 0.0175 | 0.0014 to 0.0322 | 0.0187 | 0.0017 to 0.0347 | 4.2 pp | -2.7 pp to 11.5 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 96 | 39.1% | 61.4% | 3.5% | 97.9% |
| fixed_elo | 96 | 22.7% | 79.3% | 9.9% | 56.2% |
| market | 96 | 28.6% | 76.0% | 7.9% | 70.8% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 94 | 51.9% | 62.8% | 52.7% to 71.9% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 5 | 32.0% | 20.0% | 3.6% to 62.4% |
| fixed_elo | 40%–60% | 54 | 50.8% | 63.0% | 49.6% to 74.6% |
| fixed_elo | 60%–80% | 37 | 66.4% | 67.6% | 51.5% to 80.4% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 8 | 35.2% | 37.5% | 13.7% to 69.4% |
| market (paired only) | 40%–60% | 68 | 52.2% | 61.8% | 49.9% to 72.4% |
| market (paired only) | 60%–80% | 20 | 65.8% | 75.0% | 53.1% to 88.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261025T193752379816Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [{"game_id": "2026020182", "reason": "Official/ESPN venue disagreement"}].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
