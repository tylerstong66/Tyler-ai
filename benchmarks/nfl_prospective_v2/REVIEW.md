# NFL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **67** · Settled: **56** · Pending: **11**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-06T10:53:12.498263+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: season/week. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 67 / 100; settled among selected: 56; pending among selected: 11.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All settled games — three outcomes, including NFL ties

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 56 | 5 | 0.4647 | 0.7285 | 64.3% | 0.3895 to 0.5306 | 0.5781 to 0.8858 | 54.4% to 76.7% |
| v1 | 56 | 5 | 0.4725 | 0.7364 | 60.7% | 0.4057 to 0.5311 | 0.5948 to 0.8925 | 50.0% to 72.1% |

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 55 | 5 | 0.4460 | 0.6360 | 65.5% | 0.3696 to 0.5215 | 0.5540 to 0.7171 | 54.4% to 78.6% |
| v1 | 55 | 5 | 0.4540 | 0.6441 | 61.8% | 0.3893 to 0.5194 | 0.5753 to 0.7139 | 50.0% to 74.5% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| v2 | 55 | 5 | 0.4460 | 0.6360 | 65.5% | 0.3696 to 0.5215 | 0.5540 to 0.7171 | 54.4% to 78.6% |
| v1 | 55 | 5 | 0.4540 | 0.6441 | 61.8% | 0.3893 to 0.5194 | 0.5753 to 0.7139 | 50.0% to 74.5% |
| market | 55 | 5 | 0.4360 | 0.6297 | 67.3% | 0.3653 to 0.4866 | 0.5478 to 0.6890 | 61.4% to 72.7% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| v1 | 55 | 5 | -0.0080 | -0.0197 to 0.0013 | -0.0080 | -0.0213 to 0.0027 | 3.6 pp | 0.0 pp to 7.0 pp |
| market | 55 | 5 | 0.0101 | -0.0136 to 0.0456 | 0.0063 | -0.0179 to 0.0460 | -1.8 pp | -11.4 pp to 7.5 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| v2 | 55 | 25.3% | 83.8% | 13.8% | 36.4% |
| v1 | 55 | 27.0% | 83.5% | 13.9% | 32.7% |
| market | 55 | 19.6% | 84.7% | 13.9% | 43.6% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| v2 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 | 20%–40% | 14 | 34.6% | 21.4% | 7.6% to 47.6% |
| v2 | 40%–60% | 20 | 51.7% | 50.0% | 29.9% to 70.1% |
| v2 | 60%–80% | 18 | 69.4% | 55.6% | 33.7% to 75.4% |
| v2 | 80%–100% | 3 | 82.0% | 66.7% | 20.8% to 93.9% |
| v1 | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 | 20%–40% | 13 | 34.2% | 23.1% | 8.2% to 50.3% |
| v1 | 40%–60% | 18 | 50.0% | 44.4% | 24.6% to 66.3% |
| v1 | 60%–80% | 20 | 67.1% | 55.0% | 34.2% to 74.2% |
| v1 | 80%–100% | 4 | 81.2% | 75.0% | 30.1% to 95.4% |
| market (paired only) | 0%–20% | 1 | 19.6% | 0.0% | 0.0% to 79.3% |
| market (paired only) | 20%–40% | 9 | 31.7% | 0.0% | 0.0% to 29.9% |
| market (paired only) | 40%–60% | 24 | 50.2% | 50.0% | 31.4% to 68.6% |
| market (paired only) | 60%–80% | 19 | 68.9% | 63.2% | 41.0% to 80.9% |
| market (paired only) | 80%–100% | 2 | 84.2% | 50.0% | 9.5% to 90.5% |
| v2 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full home | 20%–40% | 14 | 34.5% | 21.4% | 7.6% to 47.6% |
| v2 full home | 40%–60% | 21 | 51.4% | 47.6% | 28.3% to 67.6% |
| v2 full home | 60%–80% | 18 | 69.1% | 55.6% | 33.7% to 75.4% |
| v2 full home | 80%–100% | 3 | 81.7% | 66.7% | 20.8% to 93.9% |
| v2 full away | 0%–20% | 3 | 17.9% | 33.3% | 6.1% to 79.2% |
| v2 full away | 20%–40% | 18 | 30.5% | 44.4% | 24.6% to 66.3% |
| v2 full away | 40%–60% | 21 | 48.3% | 47.6% | 28.3% to 67.6% |
| v2 full away | 60%–80% | 14 | 65.2% | 78.6% | 52.4% to 92.4% |
| v2 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 0%–20% | 56 | 0.4% | 1.8% | 0.3% to 9.4% |
| v2 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v2 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full home | 20%–40% | 13 | 34.1% | 23.1% | 8.2% to 50.3% |
| v1 full home | 40%–60% | 20 | 50.3% | 40.0% | 21.9% to 61.3% |
| v1 full home | 60%–80% | 21 | 68.5% | 57.1% | 36.5% to 75.5% |
| v1 full home | 80%–100% | 2 | 81.9% | 100.0% | 34.2% to 100.0% |
| v1 full away | 0%–20% | 4 | 18.7% | 25.0% | 4.6% to 69.9% |
| v1 full away | 20%–40% | 20 | 32.7% | 45.0% | 25.8% to 65.8% |
| v1 full away | 40%–60% | 19 | 49.9% | 52.6% | 31.7% to 72.7% |
| v1 full away | 60%–80% | 13 | 65.6% | 76.9% | 49.7% to 91.8% |
| v1 full away | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 0%–20% | 56 | 0.4% | 1.8% | 0.3% to 9.4% |
| v1 full tie | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 40%–60% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| v1 full tie | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/nfl_prospective_v2/captures/20261108T003647748760Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [{"game_id": "2026_09_LV_SF", "reason": "Exact schedule/ESPN team and kickoff match required"}].
Optional availability errors: [].
Newer saved collection failure: null.
NFL completion must be corroborated with the successful workflow run.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
