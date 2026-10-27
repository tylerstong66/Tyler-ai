# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **41** · Settled: **40** · Pending: **1**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-26T06:16:44.041739+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 41 / 100; settled among selected: 40; pending among selected: 1.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 40 | 3 | 0.5015 | 0.7960 | 60.0% | Unavailable | Unavailable | Unavailable |
| v1 | 40 | 3 | 0.5009 | 0.7949 | 57.5% | Unavailable | Unavailable | Unavailable |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 39 | 3 | 0.4762 | 0.6688 | 61.5% | Unavailable | Unavailable | Unavailable |
| v1 | 39 | 3 | 0.4756 | 0.6676 | 59.0% | Unavailable | Unavailable | Unavailable |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 39 | 3 | 0.4762 | 0.6688 | 61.5% | Unavailable | Unavailable | Unavailable |
| v1 | 39 | 3 | 0.4756 | 0.6676 | 59.0% | Unavailable | Unavailable | Unavailable |
| market | 39 | 3 | 0.4759 | 0.6750 | 64.1% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 39 | 3 | 0.0006 | Unavailable | 0.0012 | Unavailable | 2.6 pp | Unavailable |
| market | 39 | 3 | 0.0002 | Unavailable | -0.0061 | Unavailable | -2.6 pp | Unavailable |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 39 | 25.3% | 81.6% | 13.7% | 35.9% |
| v1 | 39 | 27.0% | 81.0% | 13.8% | 30.8% |
| market | 39 | 25.6% | 84.7% | 12.9% | 51.3% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 12 | 34.5% | 25.0% | 8.9% to 53.2% |
| v2 | 40%–60% | 14 | 50.8% | 42.9% | 21.4% to 67.4% |
| v2 | 60%–80% | 11 | 69.1% | 45.5% | 21.3% to 72.0% |
| v2 | 80%–100% | 2 | 81.1% | 50.0% | 9.5% to 90.5% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 11 | 33.9% | 27.3% | 9.7% to 56.6% |
| v1 | 40%–60% | 12 | 48.5% | 33.3% | 13.8% to 60.9% |
| v1 | 60%–80% | 13 | 66.1% | 46.2% | 23.2% to 70.9% |
| v1 | 80%–100% | 3 | 80.4% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 7 | 32.0% | 0.0% | 0.0% to 35.4% |
| market (paired only) | 40%–60% | 20 | 49.4% | 45.0% | 25.8% to 65.8% |
| market (paired only) | 60%–80% | 11 | 70.0% | 54.5% | 28.0% to 78.7% |
| market (paired only) | 80%–100% | 1 | 84.7% | 0.0% | 0.0% to 79.3% |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 12 | 34.4% | 25.0% | 8.9% to 53.2% |
| v2 full home | 40%–60% | 15 | 50.4% | 40.0% | 19.8% to 64.3% |
| v2 full home | 60%–80% | 11 | 68.8% | 45.5% | 21.3% to 72.0% |
| v2 full home | 80%–100% | 2 | 80.8% | 50.0% | 9.5% to 90.5% |
| v2 full away | 0%–20% | 2 | 18.8% | 50.0% | 9.5% to 90.5% |
| v2 full away | 20%–40% | 11 | 30.8% | 54.5% | 28.0% to 78.7% |
| v2 full away | 40%–60% | 15 | 49.2% | 53.3% | 30.1% to 75.2% |
| v2 full away | 60%–80% | 12 | 65.3% | 75.0% | 46.8% to 91.1% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 40 | 0.4% | 2.5% | 0.4% to 12.9% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 11 | 33.8% | 27.3% | 9.7% to 56.6% |
| v1 full home | 40%–60% | 14 | 49.2% | 28.6% | 11.7% to 54.6% |
| v1 full home | 60%–80% | 14 | 68.3% | 50.0% | 26.8% to 73.2% |
| v1 full home | 80%–100% | 1 | 80.7% | 100.0% | 20.7% to 100.0% |
| v1 full away | 0%–20% | 3 | 19.5% | 33.3% | 6.1% to 79.2% |
| v1 full away | 20%–40% | 13 | 33.8% | 53.8% | 29.1% to 76.8% |
| v1 full away | 40%–60% | 13 | 51.3% | 61.5% | 35.5% to 82.3% |
| v1 full away | 60%–80% | 11 | 65.9% | 72.7% | 43.4% to 90.3% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 40 | 0.4% | 2.5% | 0.4% to 12.9% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261027T002556715880Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
