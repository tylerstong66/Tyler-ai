# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **99** · Settled: **97** · Pending: **2**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-27T02:10:22.436964+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 99 / 100; settled among selected: 97; pending among selected: 2.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 97 | 8 | 0.4179 | 0.6473 | 69.1% | 0.3471 to 0.4886 | 0.5353 to 0.7759 | 58.9% to 79.8% |
| v1 | 97 | 8 | 0.4238 | 0.6529 | 66.0% | 0.3603 to 0.4893 | 0.5460 to 0.7771 | 55.4% to 75.9% |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 96 | 8 | 0.4066 | 0.5919 | 69.8% | 0.3393 to 0.4774 | 0.5193 to 0.6686 | 59.4% to 80.4% |
| v1 | 96 | 8 | 0.4126 | 0.5976 | 66.7% | 0.3523 to 0.4780 | 0.5329 to 0.6684 | 55.7% to 76.6% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 96 | 8 | 0.4066 | 0.5919 | 69.8% | 0.3393 to 0.4774 | 0.5193 to 0.6686 | 59.4% to 80.4% |
| v1 | 96 | 8 | 0.4126 | 0.5976 | 66.7% | 0.3523 to 0.4780 | 0.5329 to 0.6684 | 55.7% to 76.6% |
| market | 96 | 8 | 0.3970 | 0.5839 | 71.9% | 0.3277 to 0.4656 | 0.5045 to 0.6631 | 64.6% to 80.8% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 96 | 8 | -0.0059 | -0.0172 to 0.0058 | -0.0056 | -0.0176 to 0.0067 | 3.1 pp | 1.0 pp to 5.7 pp |
| market | 96 | 8 | 0.0097 | -0.0114 to 0.0316 | 0.0080 | -0.0157 to 0.0304 | -2.1 pp | -8.3 pp to 2.9 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 96 | 16.7% | 88.1% | 15.1% | 31.2% |
| v1 | 96 | 18.0% | 87.4% | 14.8% | 33.3% |
| market | 96 | 16.0% | 90.4% | 15.7% | 35.4% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 2 | 17.9% | 0.0% | 0.0% to 65.8% |
| v2 | 20%–40% | 24 | 34.5% | 16.7% | 6.7% to 35.9% |
| v2 | 40%–60% | 30 | 51.8% | 53.3% | 36.1% to 69.8% |
| v2 | 60%–80% | 34 | 69.0% | 55.9% | 39.5% to 71.1% |
| v2 | 80%–100% | 6 | 83.4% | 83.3% | 43.6% to 97.0% |
| v1 | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 | 20%–40% | 21 | 33.6% | 19.0% | 7.7% to 40.0% |
| v1 | 40%–60% | 32 | 50.8% | 43.8% | 28.2% to 60.7% |
| v1 | 60%–80% | 34 | 67.7% | 58.8% | 42.2% to 73.6% |
| v1 | 80%–100% | 7 | 83.1% | 85.7% | 48.7% to 97.4% |
| market (paired only) | 0%–20% | 3 | 18.5% | 0.0% | 0.0% to 56.1% |
| market (paired only) | 20%–40% | 21 | 32.1% | 9.5% | 2.7% to 28.9% |
| market (paired only) | 40%–60% | 34 | 51.0% | 47.1% | 31.5% to 63.3% |
| market (paired only) | 60%–80% | 30 | 68.5% | 63.3% | 45.5% to 78.1% |
| market (paired only) | 80%–100% | 8 | 84.9% | 87.5% | 52.9% to 97.8% |
| v2 full home | 0%–20% | 2 | 17.8% | 0.0% | 0.0% to 65.8% |
| v2 full home | 20%–40% | 24 | 34.3% | 16.7% | 6.7% to 35.9% |
| v2 full home | 40%–60% | 32 | 51.7% | 50.0% | 33.6% to 66.4% |
| v2 full home | 60%–80% | 33 | 69.0% | 57.6% | 40.8% to 72.8% |
| v2 full home | 80%–100% | 6 | 83.1% | 83.3% | 43.6% to 97.0% |
| v2 full away | 0%–20% | 6 | 16.5% | 16.7% | 3.0% to 56.4% |
| v2 full away | 20%–40% | 34 | 30.9% | 44.1% | 28.9% to 60.5% |
| v2 full away | 40%–60% | 31 | 48.2% | 45.2% | 29.2% to 62.2% |
| v2 full away | 60%–80% | 24 | 65.3% | 83.3% | 64.1% to 93.3% |
| v2 full away | 80%–100% | 2 | 81.8% | 100.0% | 34.2% to 100.0% |
| v2 full tie | 0%–20% | 97 | 0.4% | 1.0% | 0.2% to 5.6% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 2 | 18.4% | 0.0% | 0.0% to 65.8% |
| v1 full home | 20%–40% | 22 | 33.8% | 18.2% | 7.3% to 38.5% |
| v1 full home | 40%–60% | 33 | 51.2% | 42.4% | 27.2% to 59.2% |
| v1 full home | 60%–80% | 35 | 68.3% | 60.0% | 43.6% to 74.4% |
| v1 full home | 80%–100% | 5 | 83.9% | 100.0% | 56.6% to 100.0% |
| v1 full away | 0%–20% | 7 | 16.9% | 14.3% | 2.6% to 51.3% |
| v1 full away | 20%–40% | 34 | 32.2% | 41.2% | 26.4% to 57.8% |
| v1 full away | 40%–60% | 33 | 49.0% | 54.5% | 38.0% to 70.2% |
| v1 full away | 60%–80% | 21 | 66.1% | 81.0% | 60.0% to 92.3% |
| v1 full away | 80%–100% | 2 | 81.3% | 100.0% | 34.2% to 100.0% |
| v1 full tie | 0%–20% | 97 | 0.4% | 1.0% | 0.2% to 5.6% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261127T021018913736Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
