# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **54** · Settled: **50** · Pending: **4**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-01T23:36:13.585058+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 54 / 100; settled among selected: 50; pending among selected: 4.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 50 | 4 | 0.4782 | 0.7510 | 62.0% | Unavailable | Unavailable | Unavailable |
| v1 | 50 | 4 | 0.4832 | 0.7557 | 58.0% | Unavailable | Unavailable | Unavailable |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 49 | 4 | 0.4576 | 0.6481 | 63.3% | Unavailable | Unavailable | Unavailable |
| v1 | 49 | 4 | 0.4627 | 0.6529 | 59.2% | Unavailable | Unavailable | Unavailable |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 49 | 4 | 0.4576 | 0.6481 | 63.3% | Unavailable | Unavailable | Unavailable |
| v1 | 49 | 4 | 0.4627 | 0.6529 | 59.2% | Unavailable | Unavailable | Unavailable |
| market | 49 | 4 | 0.4513 | 0.6471 | 67.3% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 49 | 4 | -0.0051 | Unavailable | -0.0048 | Unavailable | 4.1 pp | Unavailable |
| market | 49 | 4 | 0.0063 | Unavailable | 0.0010 | Unavailable | -4.1 pp | Unavailable |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 49 | 25.3% | 83.8% | 13.9% | 36.7% |
| v1 | 49 | 27.0% | 83.5% | 14.1% | 32.7% |
| market | 49 | 25.6% | 84.7% | 13.5% | 46.9% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 12 | 34.5% | 25.0% | 8.9% to 53.2% |
| v2 | 40%–60% | 18 | 51.2% | 44.4% | 24.6% to 66.3% |
| v2 | 60%–80% | 16 | 69.6% | 56.2% | 33.2% to 76.9% |
| v2 | 80%–100% | 3 | 82.0% | 66.7% | 20.8% to 93.9% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 11 | 33.9% | 27.3% | 9.7% to 56.6% |
| v1 | 40%–60% | 16 | 49.4% | 37.5% | 18.5% to 61.4% |
| v1 | 60%–80% | 18 | 67.1% | 55.6% | 33.7% to 75.4% |
| v1 | 80%–100% | 4 | 81.2% | 75.0% | 30.1% to 95.4% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 8 | 32.2% | 0.0% | 0.0% to 32.4% |
| market (paired only) | 40%–60% | 23 | 50.3% | 47.8% | 29.2% to 67.0% |
| market (paired only) | 60%–80% | 16 | 69.4% | 62.5% | 38.6% to 81.5% |
| market (paired only) | 80%–100% | 2 | 84.2% | 50.0% | 9.5% to 90.5% |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 12 | 34.4% | 25.0% | 8.9% to 53.2% |
| v2 full home | 40%–60% | 19 | 50.9% | 42.1% | 23.1% to 63.7% |
| v2 full home | 60%–80% | 16 | 69.3% | 56.2% | 33.2% to 76.9% |
| v2 full home | 80%–100% | 3 | 81.7% | 66.7% | 20.8% to 93.9% |
| v2 full away | 0%–20% | 3 | 17.9% | 33.3% | 6.1% to 79.2% |
| v2 full away | 20%–40% | 16 | 30.3% | 43.8% | 23.1% to 66.8% |
| v2 full away | 40%–60% | 19 | 48.8% | 52.6% | 31.7% to 72.7% |
| v2 full away | 60%–80% | 12 | 65.3% | 75.0% | 46.8% to 91.1% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 50 | 0.4% | 2.0% | 0.4% to 10.5% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 11 | 33.8% | 27.3% | 9.7% to 56.6% |
| v1 full home | 40%–60% | 18 | 49.8% | 33.3% | 16.3% to 56.3% |
| v1 full home | 60%–80% | 19 | 68.6% | 57.9% | 36.3% to 76.9% |
| v1 full home | 80%–100% | 2 | 81.9% | 100.0% | 34.2% to 100.0% |
| v1 full away | 0%–20% | 4 | 18.7% | 25.0% | 4.6% to 69.9% |
| v1 full away | 20%–40% | 18 | 32.8% | 44.4% | 24.6% to 66.3% |
| v1 full away | 40%–60% | 17 | 50.4% | 58.8% | 36.0% to 78.4% |
| v1 full away | 60%–80% | 11 | 65.9% | 72.7% | 43.4% to 90.3% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 50 | 0.4% | 2.0% | 0.4% to 10.5% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261101T233610272301Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
