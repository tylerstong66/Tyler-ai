# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **40** · Settled: **28** · Pending: **12**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-23T04:50:13.092006+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 40 / 100; settled among selected: 28; pending among selected: 12.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 28 | 3 | 0.5243 | 0.8623 | 60.7% | Unavailable | Unavailable | Unavailable |
| v1 | 28 | 3 | 0.5266 | 0.8649 | 57.1% | Unavailable | Unavailable | Unavailable |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 27 | 3 | 0.4886 | 0.6826 | 63.0% | Unavailable | Unavailable | Unavailable |
| v1 | 27 | 3 | 0.4911 | 0.6853 | 59.3% | Unavailable | Unavailable | Unavailable |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 27 | 3 | 0.4886 | 0.6826 | 63.0% | Unavailable | Unavailable | Unavailable |
| v1 | 27 | 3 | 0.4911 | 0.6853 | 59.3% | Unavailable | Unavailable | Unavailable |
| market | 27 | 3 | 0.4623 | 0.6595 | 63.0% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 27 | 3 | -0.0024 | Unavailable | -0.0027 | Unavailable | 3.7 pp | Unavailable |
| market | 27 | 3 | 0.0264 | Unavailable | 0.0231 | Unavailable | 0.0 pp | Unavailable |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 27 | 25.3% | 81.6% | 14.3% | 37.0% |
| v1 | 27 | 29.2% | 80.2% | 14.2% | 29.6% |
| market | 27 | 25.6% | 84.7% | 13.3% | 51.9% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 8 | 34.3% | 25.0% | 7.1% to 59.1% |
| v2 | 40%–60% | 10 | 50.3% | 50.0% | 23.7% to 76.3% |
| v2 | 60%–80% | 7 | 71.0% | 42.9% | 15.8% to 75.0% |
| v2 | 80%–100% | 2 | 81.1% | 50.0% | 9.5% to 90.5% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 8 | 34.4% | 25.0% | 7.1% to 59.1% |
| v1 | 40%–60% | 8 | 48.8% | 50.0% | 21.5% to 78.5% |
| v1 | 60%–80% | 9 | 68.1% | 44.4% | 18.9% to 73.3% |
| v1 | 80%–100% | 2 | 80.2% | 50.0% | 9.5% to 90.5% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 5 | 30.3% | 0.0% | 0.0% to 43.4% |
| market (paired only) | 40%–60% | 14 | 49.7% | 50.0% | 26.8% to 73.2% |
| market (paired only) | 60%–80% | 7 | 70.1% | 57.1% | 25.0% to 84.2% |
| market (paired only) | 80%–100% | 1 | 84.7% | 0.0% | 0.0% to 79.3% |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 8 | 34.1% | 25.0% | 7.1% to 59.1% |
| v2 full home | 40%–60% | 11 | 49.9% | 45.5% | 21.3% to 72.0% |
| v2 full home | 60%–80% | 7 | 70.8% | 42.9% | 15.8% to 75.0% |
| v2 full home | 80%–100% | 2 | 80.8% | 50.0% | 9.5% to 90.5% |
| v2 full away | 0%–20% | 2 | 18.8% | 50.0% | 9.5% to 90.5% |
| v2 full away | 20%–40% | 7 | 28.9% | 57.1% | 25.0% to 84.2% |
| v2 full away | 40%–60% | 11 | 49.7% | 45.5% | 21.3% to 72.0% |
| v2 full away | 60%–80% | 8 | 65.5% | 75.0% | 40.9% to 92.9% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 28 | 0.4% | 3.6% | 0.6% to 17.7% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 8 | 34.3% | 25.0% | 7.1% to 59.1% |
| v1 full home | 40%–60% | 10 | 49.8% | 40.0% | 16.8% to 68.7% |
| v1 full home | 60%–80% | 10 | 71.1% | 50.0% | 23.7% to 76.3% |
| v1 full home | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full away | 0%–20% | 2 | 19.8% | 50.0% | 9.5% to 90.5% |
| v1 full away | 20%–40% | 9 | 31.8% | 55.6% | 26.7% to 81.1% |
| v1 full away | 40%–60% | 9 | 51.0% | 44.4% | 18.9% to 73.3% |
| v1 full away | 60%–80% | 8 | 65.4% | 75.0% | 40.9% to 92.9% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 28 | 0.4% | 3.6% | 0.6% to 17.7% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261025T162001015537Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
