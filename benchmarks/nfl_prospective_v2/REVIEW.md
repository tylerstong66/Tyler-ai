# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **55** · Settled: **54** · Pending: **1**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-02T06:04:03.611690+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 55 / 100; settled among selected: 54; pending among selected: 1.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 54 | 4 | 0.4631 | 0.7294 | 64.8% | Unavailable | Unavailable | Unavailable |
| v1 | 54 | 4 | 0.4695 | 0.7358 | 61.1% | Unavailable | Unavailable | Unavailable |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 53 | 4 | 0.4437 | 0.6336 | 66.0% | Unavailable | Unavailable | Unavailable |
| v1 | 53 | 4 | 0.4503 | 0.6401 | 62.3% | Unavailable | Unavailable | Unavailable |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 53 | 4 | 0.4437 | 0.6336 | 66.0% | Unavailable | Unavailable | Unavailable |
| v1 | 53 | 4 | 0.4503 | 0.6401 | 62.3% | Unavailable | Unavailable | Unavailable |
| market | 53 | 4 | 0.4372 | 0.6319 | 67.9% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 53 | 4 | -0.0066 | Unavailable | -0.0066 | Unavailable | 3.8 pp | Unavailable |
| market | 53 | 4 | 0.0064 | Unavailable | 0.0017 | Unavailable | -1.9 pp | Unavailable |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 53 | 25.3% | 83.8% | 13.9% | 37.7% |
| v1 | 53 | 27.0% | 83.5% | 14.0% | 34.0% |
| market | 53 | 25.6% | 84.7% | 13.6% | 45.3% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 13 | 34.3% | 23.1% | 8.2% to 50.3% |
| v2 | 40%–60% | 20 | 51.7% | 50.0% | 29.9% to 70.1% |
| v2 | 60%–80% | 17 | 69.9% | 58.8% | 36.0% to 78.4% |
| v2 | 80%–100% | 3 | 82.0% | 66.7% | 20.8% to 93.9% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 12 | 33.8% | 25.0% | 8.9% to 53.2% |
| v1 | 40%–60% | 18 | 50.0% | 44.4% | 24.6% to 66.3% |
| v1 | 60%–80% | 19 | 67.3% | 57.9% | 36.3% to 76.9% |
| v1 | 80%–100% | 4 | 81.2% | 75.0% | 30.1% to 95.4% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 9 | 31.7% | 0.0% | 0.0% to 29.9% |
| market (paired only) | 40%–60% | 24 | 50.2% | 50.0% | 31.4% to 68.6% |
| market (paired only) | 60%–80% | 18 | 69.4% | 66.7% | 43.7% to 83.7% |
| market (paired only) | 80%–100% | 2 | 84.2% | 50.0% | 9.5% to 90.5% |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 13 | 34.2% | 23.1% | 8.2% to 50.3% |
| v2 full home | 40%–60% | 21 | 51.4% | 47.6% | 28.3% to 67.6% |
| v2 full home | 60%–80% | 17 | 69.7% | 58.8% | 36.0% to 78.4% |
| v2 full home | 80%–100% | 3 | 81.7% | 66.7% | 20.8% to 93.9% |
| v2 full away | 0%–20% | 3 | 17.9% | 33.3% | 6.1% to 79.2% |
| v2 full away | 20%–40% | 17 | 30.0% | 41.2% | 21.6% to 64.0% |
| v2 full away | 40%–60% | 21 | 48.3% | 47.6% | 28.3% to 67.6% |
| v2 full away | 60%–80% | 13 | 65.4% | 76.9% | 49.7% to 91.8% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 54 | 0.4% | 1.9% | 0.3% to 9.8% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 12 | 33.7% | 25.0% | 8.9% to 53.2% |
| v1 full home | 40%–60% | 20 | 50.3% | 40.0% | 21.9% to 61.3% |
| v1 full home | 60%–80% | 20 | 68.7% | 60.0% | 38.7% to 78.1% |
| v1 full home | 80%–100% | 2 | 81.9% | 100.0% | 34.2% to 100.0% |
| v1 full away | 0%–20% | 4 | 18.7% | 25.0% | 4.6% to 69.9% |
| v1 full away | 20%–40% | 19 | 32.5% | 42.1% | 23.1% to 63.7% |
| v1 full away | 40%–60% | 19 | 49.9% | 52.6% | 31.7% to 72.7% |
| v1 full away | 60%–80% | 12 | 66.0% | 75.0% | 46.8% to 91.1% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 54 | 0.4% | 1.9% | 0.3% to 9.8% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261102T060359458924Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
