# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **26** · Settled: **21** · Pending: **5**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-18T20:44:05.227940+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 26 / 100; settled among selected: 21; pending among selected: 5.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 21 | 2 | 0.5603 | 0.9435 | 52.4% | Unavailable | Unavailable | Unavailable |
| v1 | 21 | 2 | 0.5613 | 0.9444 | 52.4% | Unavailable | Unavailable | Unavailable |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 20 | 2 | 0.5140 | 0.7063 | 55.0% | Unavailable | Unavailable | Unavailable |
| v1 | 20 | 2 | 0.5151 | 0.7073 | 55.0% | Unavailable | Unavailable | Unavailable |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 20 | 2 | 0.5140 | 0.7063 | 55.0% | Unavailable | Unavailable | Unavailable |
| v1 | 20 | 2 | 0.5151 | 0.7073 | 55.0% | Unavailable | Unavailable | Unavailable |
| market | 20 | 2 | 0.4737 | 0.6651 | 55.0% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 20 | 2 | -0.0011 | Unavailable | -0.0010 | Unavailable | 0.0 pp | Unavailable |
| market | 20 | 2 | 0.0403 | Unavailable | 0.0412 | Unavailable | 0.0 pp | Unavailable |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 20 | 31.8% | 81.6% | 13.3% | 35.0% |
| v1 | 20 | 32.0% | 80.2% | 13.4% | 25.0% |
| market | 20 | 25.6% | 74.4% | 11.6% | 55.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 7 | 35.5% | 28.6% | 8.2% to 64.1% |
| v2 | 40%–60% | 7 | 49.1% | 42.9% | 15.8% to 75.0% |
| v2 | 60%–80% | 5 | 68.5% | 20.0% | 3.6% to 62.4% |
| v2 | 80%–100% | 1 | 81.6% | 100.0% | 20.7% to 100.0% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 7 | 35.1% | 28.6% | 8.2% to 64.1% |
| v1 | 40%–60% | 5 | 45.5% | 40.0% | 11.8% to 76.9% |
| v1 | 60%–80% | 7 | 65.8% | 28.6% | 8.2% to 64.1% |
| v1 | 80%–100% | 1 | 80.2% | 100.0% | 20.7% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 4 | 30.1% | 0.0% | 0.0% to 49.0% |
| market (paired only) | 40%–60% | 11 | 49.4% | 45.5% | 21.3% to 72.0% |
| market (paired only) | 60%–80% | 5 | 66.8% | 40.0% | 11.8% to 76.9% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 7 | 35.4% | 28.6% | 8.2% to 64.1% |
| v2 full home | 40%–60% | 8 | 48.8% | 37.5% | 13.7% to 69.4% |
| v2 full home | 60%–80% | 5 | 68.2% | 20.0% | 3.6% to 62.4% |
| v2 full home | 80%–100% | 1 | 81.3% | 100.0% | 20.7% to 100.0% |
| v2 full away | 0%–20% | 1 | 18.4% | 0.0% | 0.0% to 79.3% |
| v2 full away | 20%–40% | 5 | 31.4% | 80.0% | 37.6% to 96.4% |
| v2 full away | 40%–60% | 8 | 50.9% | 50.0% | 21.5% to 78.5% |
| v2 full away | 60%–80% | 7 | 64.2% | 71.4% | 35.9% to 91.8% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 21 | 0.4% | 4.8% | 0.8% to 22.7% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 7 | 35.0% | 28.6% | 8.2% to 64.1% |
| v1 full home | 40%–60% | 7 | 47.9% | 28.6% | 8.2% to 64.1% |
| v1 full home | 60%–80% | 7 | 68.4% | 42.9% | 15.8% to 75.0% |
| v1 full home | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full away | 0%–20% | 1 | 19.8% | 0.0% | 0.0% to 79.3% |
| v1 full away | 20%–40% | 7 | 34.1% | 71.4% | 35.9% to 91.8% |
| v1 full away | 40%–60% | 6 | 53.7% | 50.0% | 18.8% to 81.2% |
| v1 full away | 60%–80% | 7 | 64.6% | 71.4% | 35.9% to 91.8% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 21 | 0.4% | 4.8% | 0.8% to 22.7% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261018T204402139309Z/manifest.json.
Manifest completion field: True. Errors: [{"game_id": "2026_06_PIT_TB", "reason": "final schedule missing"}]. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
