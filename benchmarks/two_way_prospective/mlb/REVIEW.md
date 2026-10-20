# MLB prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **10** · Settled: **7** · Pending: **3**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-16T07:10:37.746412+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 10 / 100; settled among selected: 7; pending among selected: 3.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 7 | 5 | 0.4778 | 0.6709 | 57.1% | 0.3992 to 0.5255 | 0.5916 to 0.7190 | 33.3% to 83.3% |
| fixed_elo | 7 | 5 | 0.4705 | 0.6635 | 71.4% | 0.3662 to 0.5284 | 0.5579 to 0.7222 | 55.6% to 100.0% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 5 | 4 | 0.5222 | 0.7156 | 40.0% | Unavailable | Unavailable | Unavailable |
| fixed_elo | 5 | 4 | 0.5223 | 0.7161 | 60.0% | Unavailable | Unavailable | Unavailable |
| market | 5 | 4 | 0.6189 | 0.8143 | 40.0% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 7 | 5 | 0.0074 | -0.0122 to 0.0426 | 0.0073 | -0.0126 to 0.0432 | -14.3 pp | -50.0 pp to 0.0 pp |
| market | 5 | 4 | -0.0967 | Unavailable | -0.0987 | Unavailable | 0.0 pp | Unavailable |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 5 | 50.5% | 58.3% | 3.5% | 100.0% |
| fixed_elo | 5 | 46.8% | 60.7% | 4.8% | 80.0% |
| market | 5 | 50.6% | 62.1% | 7.3% | 60.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 7 | 54.6% | 57.1% | 25.0% to 84.2% |
| model | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 40%–60% | 5 | 51.4% | 60.0% | 23.1% to 88.2% |
| fixed_elo | 60%–80% | 2 | 60.7% | 50.0% | 9.5% to 90.5% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 40%–60% | 3 | 54.7% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 60%–80% | 2 | 61.2% | 0.0% | 0.0% to 65.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/mlb/captures/20261020T002042303505Z/manifest.json.
Manifest completion field: True. Errors: [{"game_id": "849816", "reason": "Final identity differs from saved forecast"}]. Exclusions: [{"game_id": "849814", "reason": "Exact official/ESPN matchup and kickoff match required"}].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
