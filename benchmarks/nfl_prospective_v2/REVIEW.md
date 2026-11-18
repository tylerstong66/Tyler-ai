# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **83** · Settled: **83** · Pending: **0**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-17T04:29:12.493346+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 83 / 100; settled among selected: 83; pending among selected: 0.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 83 | 6 | 0.4301 | 0.6687 | 68.7% | 0.3656 to 0.5049 | 0.5574 to 0.8017 | 57.1% to 79.8% |
| v1 | 83 | 6 | 0.4368 | 0.6752 | 65.1% | 0.3806 to 0.5060 | 0.5685 to 0.8112 | 53.6% to 75.3% |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 82 | 6 | 0.4171 | 0.6047 | 69.5% | 0.3566 to 0.4894 | 0.5408 to 0.6815 | 57.3% to 81.0% |
| v1 | 82 | 6 | 0.4239 | 0.6114 | 65.9% | 0.3717 to 0.4881 | 0.5560 to 0.6806 | 53.7% to 76.2% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 82 | 6 | 0.4171 | 0.6047 | 69.5% | 0.3566 to 0.4894 | 0.5408 to 0.6815 | 57.3% to 81.0% |
| v1 | 82 | 6 | 0.4239 | 0.6114 | 65.9% | 0.3717 to 0.4881 | 0.5560 to 0.6806 | 53.7% to 76.2% |
| market | 82 | 6 | 0.4023 | 0.5916 | 70.7% | 0.3382 to 0.4697 | 0.5188 to 0.6683 | 62.5% to 80.5% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 82 | 6 | -0.0068 | -0.0195 to 0.0061 | -0.0066 | -0.0200 to 0.0071 | 3.7 pp | 1.2 pp to 6.1 pp |
| market | 82 | 6 | 0.0147 | -0.0079 to 0.0387 | 0.0131 | -0.0110 to 0.0379 | -1.2 pp | -7.3 pp to 4.9 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 82 | 16.7% | 83.8% | 14.0% | 35.4% |
| v1 | 82 | 18.0% | 83.5% | 13.8% | 37.8% |
| market | 82 | 16.0% | 84.7% | 14.7% | 37.8% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 2 | 17.9% | 0.0% | 0.0% to 65.8% |
| v2 | 20%–40% | 23 | 34.4% | 13.0% | 4.5% to 32.1% |
| v2 | 40%–60% | 29 | 51.5% | 51.7% | 34.4% to 68.6% |
| v2 | 60%–80% | 25 | 69.0% | 52.0% | 33.5% to 70.0% |
| v2 | 80%–100% | 3 | 82.0% | 66.7% | 20.8% to 93.9% |
| v1 | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 | 20%–40% | 20 | 33.5% | 15.0% | 5.2% to 36.0% |
| v1 | 40%–60% | 31 | 50.6% | 41.9% | 26.4% to 59.2% |
| v1 | 60%–80% | 25 | 67.8% | 56.0% | 37.1% to 73.3% |
| v1 | 80%–100% | 4 | 81.2% | 75.0% | 30.1% to 95.4% |
| market (paired only) | 0%–20% | 3 | 18.5% | 0.0% | 0.0% to 56.1% |
| market (paired only) | 20%–40% | 20 | 32.3% | 5.0% | 0.9% to 23.6% |
| market (paired only) | 40%–60% | 31 | 50.7% | 45.2% | 29.2% to 62.2% |
| market (paired only) | 60%–80% | 25 | 68.5% | 64.0% | 44.5% to 79.8% |
| market (paired only) | 80%–100% | 3 | 83.1% | 66.7% | 20.8% to 93.9% |
| v2 full home | 0%–20% | 2 | 17.8% | 0.0% | 0.0% to 65.8% |
| v2 full home | 20%–40% | 23 | 34.3% | 13.0% | 4.5% to 32.1% |
| v2 full home | 40%–60% | 31 | 51.5% | 48.4% | 32.0% to 65.2% |
| v2 full home | 60%–80% | 24 | 69.2% | 54.2% | 35.1% to 72.1% |
| v2 full home | 80%–100% | 3 | 81.7% | 66.7% | 20.8% to 93.9% |
| v2 full away | 0%–20% | 3 | 17.9% | 33.3% | 6.1% to 79.2% |
| v2 full away | 20%–40% | 25 | 30.8% | 48.0% | 30.0% to 66.5% |
| v2 full away | 40%–60% | 30 | 48.4% | 46.7% | 30.2% to 63.9% |
| v2 full away | 60%–80% | 23 | 65.3% | 87.0% | 67.9% to 95.5% |
| v2 full away | 80%–100% | 2 | 81.8% | 100.0% | 34.2% to 100.0% |
| v2 full tie | 0%–20% | 83 | 0.4% | 1.2% | 0.2% to 6.5% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 full home | 20%–40% | 21 | 33.7% | 14.3% | 5.0% to 34.6% |
| v1 full home | 40%–60% | 32 | 50.9% | 40.6% | 25.5% to 57.7% |
| v1 full home | 60%–80% | 26 | 68.8% | 57.7% | 38.9% to 74.5% |
| v1 full home | 80%–100% | 2 | 81.9% | 100.0% | 34.2% to 100.0% |
| v1 full away | 0%–20% | 4 | 18.7% | 25.0% | 4.6% to 69.9% |
| v1 full away | 20%–40% | 25 | 32.1% | 44.0% | 26.7% to 62.9% |
| v1 full away | 40%–60% | 32 | 49.3% | 56.2% | 39.3% to 71.8% |
| v1 full away | 60%–80% | 20 | 66.2% | 85.0% | 64.0% to 94.8% |
| v1 full away | 80%–100% | 2 | 81.3% | 100.0% | 34.2% to 100.0% |
| v1 full tie | 0%–20% | 83 | 0.4% | 1.2% | 0.2% to 6.5% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261118T135845620962Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
