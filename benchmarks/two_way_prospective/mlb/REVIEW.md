# MLB prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **14** · Settled: **10** · Pending: **4**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-27T06:17:23.341492+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 14 / 100; settled among selected: 10; pending among selected: 4.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 10 | 8 | 0.4568 | 0.6497 | 60.0% | 0.3930 to 0.5026 | 0.5853 to 0.6960 | 36.4% to 87.5% |
| fixed_elo | 10 | 8 | 0.4377 | 0.6304 | 80.0% | 0.3552 to 0.4968 | 0.5470 to 0.6903 | 61.5% to 100.0% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 7 | 6 | 0.4962 | 0.6894 | 42.9% | 0.4211 to 0.5732 | 0.6136 to 0.7672 | 14.3% to 75.0% |
| fixed_elo | 7 | 6 | 0.4806 | 0.6739 | 71.4% | 0.3898 to 0.5836 | 0.5820 to 0.7783 | 42.9% to 100.0% |
| market | 7 | 6 | 0.5575 | 0.7515 | 42.9% | 0.4330 to 0.6759 | 0.6244 to 0.8728 | 14.3% to 75.0% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 10 | 8 | 0.0191 | -0.0014 to 0.0479 | 0.0193 | -0.0016 to 0.0483 | -20.0 pp | -50.0 pp to 0.0 pp |
| market | 7 | 6 | -0.0613 | -0.1427 to 0.0068 | -0.0621 | -0.1459 to 0.0077 | 0.0 pp | 0.0 pp to 0.0 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 7 | 50.0% | 58.3% | 3.6% | 100.0% |
| fixed_elo | 7 | 45.9% | 60.7% | 5.3% | 85.7% |
| market | 7 | 50.6% | 63.5% | 7.4% | 57.1% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 10 | 54.7% | 60.0% | 31.3% to 83.2% |
| model | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 40%–60% | 8 | 52.7% | 62.5% | 30.6% to 86.3% |
| fixed_elo | 60%–80% | 2 | 60.7% | 50.0% | 9.5% to 90.5% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 40%–60% | 4 | 54.0% | 50.0% | 15.0% to 85.0% |
| market (paired only) | 60%–80% | 3 | 62.0% | 33.3% | 6.1% to 79.2% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/mlb/captures/20261027T131251904161Z/manifest.json.
Manifest completion field: True. Errors: [{"game_id": "849816", "reason": "Final identity differs from saved forecast"}]. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
