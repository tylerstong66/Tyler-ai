# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **93** · Settled: **90** · Pending: **3**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-22T21:46:30.670379+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 93 / 100; settled among selected: 90; pending among selected: 3.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 90 | 7 | 0.4077 | 0.6400 | 71.1% | 0.3271 to 0.4810 | 0.5154 to 0.7693 | 60.2% to 83.3% |
| v1 | 90 | 7 | 0.4140 | 0.6461 | 67.8% | 0.3377 to 0.4834 | 0.5246 to 0.7730 | 56.7% to 79.8% |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 89 | 7 | 0.3953 | 0.5804 | 71.9% | 0.3175 to 0.4703 | 0.4969 to 0.6614 | 60.4% to 84.3% |
| v1 | 89 | 7 | 0.4017 | 0.5867 | 68.5% | 0.3306 to 0.4727 | 0.5096 to 0.6621 | 57.1% to 80.8% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 89 | 7 | 0.3953 | 0.5804 | 71.9% | 0.3175 to 0.4703 | 0.4969 to 0.6614 | 60.4% to 84.3% |
| v1 | 89 | 7 | 0.4017 | 0.5867 | 68.5% | 0.3306 to 0.4727 | 0.5096 to 0.6621 | 57.1% to 80.8% |
| market | 89 | 7 | 0.3803 | 0.5655 | 73.0% | 0.2937 to 0.4498 | 0.4673 to 0.6450 | 64.3% to 84.1% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 89 | 7 | -0.0064 | -0.0185 to 0.0053 | -0.0062 | -0.0189 to 0.0059 | 3.4 pp | 1.0 pp to 6.1 pp |
| market | 89 | 7 | 0.0150 | -0.0052 to 0.0358 | 0.0150 | -0.0072 to 0.0379 | -1.1 pp | -6.7 pp to 4.3 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 89 | 16.7% | 88.1% | 14.9% | 33.7% |
| v1 | 89 | 18.0% | 87.4% | 14.7% | 34.8% |
| market | 89 | 16.0% | 90.4% | 15.7% | 36.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 2 | 17.9% | 0.0% | 0.0% to 65.8% |
| v2 | 20%–40% | 23 | 34.4% | 13.0% | 4.5% to 32.1% |
| v2 | 40%–60% | 30 | 51.8% | 53.3% | 36.1% to 69.8% |
| v2 | 60%–80% | 29 | 69.7% | 58.6% | 40.7% to 74.5% |
| v2 | 80%–100% | 5 | 83.3% | 80.0% | 37.6% to 96.4% |
| v1 | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 | 20%–40% | 20 | 33.5% | 15.0% | 5.2% to 36.0% |
| v1 | 40%–60% | 31 | 50.6% | 41.9% | 26.4% to 59.2% |
| v1 | 60%–80% | 30 | 68.2% | 63.3% | 45.5% to 78.1% |
| v1 | 80%–100% | 6 | 82.8% | 83.3% | 43.6% to 97.0% |
| market (paired only) | 0%–20% | 3 | 18.5% | 0.0% | 0.0% to 56.1% |
| market (paired only) | 20%–40% | 20 | 32.3% | 5.0% | 0.9% to 23.6% |
| market (paired only) | 40%–60% | 32 | 51.0% | 46.9% | 30.9% to 63.6% |
| market (paired only) | 60%–80% | 27 | 68.7% | 66.7% | 47.8% to 81.4% |
| market (paired only) | 80%–100% | 7 | 85.2% | 85.7% | 48.7% to 97.4% |
| v2 full home | 0%–20% | 2 | 17.8% | 0.0% | 0.0% to 65.8% |
| v2 full home | 20%–40% | 23 | 34.3% | 13.0% | 4.5% to 32.1% |
| v2 full home | 40%–60% | 32 | 51.7% | 50.0% | 33.6% to 66.4% |
| v2 full home | 60%–80% | 28 | 69.8% | 60.7% | 42.4% to 76.4% |
| v2 full home | 80%–100% | 5 | 83.0% | 80.0% | 37.6% to 96.4% |
| v2 full away | 0%–20% | 5 | 16.6% | 20.0% | 3.6% to 62.4% |
| v2 full away | 20%–40% | 29 | 30.2% | 41.4% | 25.5% to 59.3% |
| v2 full away | 40%–60% | 31 | 48.2% | 45.2% | 29.2% to 62.2% |
| v2 full away | 60%–80% | 23 | 65.3% | 87.0% | 67.9% to 95.5% |
| v2 full away | 80%–100% | 2 | 81.8% | 100.0% | 34.2% to 100.0% |
| v2 full tie | 0%–20% | 90 | 0.4% | 1.1% | 0.2% to 6.0% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 full home | 20%–40% | 21 | 33.7% | 14.3% | 5.0% to 34.6% |
| v1 full home | 40%–60% | 32 | 50.9% | 40.6% | 25.5% to 57.7% |
| v1 full home | 60%–80% | 31 | 69.0% | 64.5% | 46.9% to 78.9% |
| v1 full home | 80%–100% | 4 | 83.8% | 100.0% | 51.0% to 100.0% |
| v1 full away | 0%–20% | 6 | 17.2% | 16.7% | 3.0% to 56.4% |
| v1 full away | 20%–40% | 30 | 31.7% | 36.7% | 21.9% to 54.5% |
| v1 full away | 40%–60% | 32 | 49.3% | 56.2% | 39.3% to 71.8% |
| v1 full away | 60%–80% | 20 | 66.2% | 85.0% | 64.0% to 94.8% |
| v1 full away | 80%–100% | 2 | 81.3% | 100.0% | 34.2% to 100.0% |
| v1 full tie | 0%–20% | 90 | 0.4% | 1.1% | 0.2% to 6.0% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261122T214627389011Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [{"game_id": "2026_11_PIT_PHI", "reason": "already_started"}, {"game_id": "2026_11_JAX_NYG", "reason": "already_started"}].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
