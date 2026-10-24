# MLB prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **12** · Settled: **8** · Pending: **4**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-24T07:18:06.121973+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 12 / 100; settled among selected: 8; pending among selected: 4.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 8 | 6 | 0.4633 | 0.6562 | 62.5% | 0.3889 to 0.5110 | 0.5811 to 0.7044 | 40.0% to 85.7% |
| fixed_elo | 8 | 6 | 0.4530 | 0.6459 | 75.0% | 0.3567 to 0.5162 | 0.5482 to 0.7101 | 60.0% to 100.0% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 6 | 5 | 0.4954 | 0.6886 | 50.0% | 0.4044 to 0.5854 | 0.5970 to 0.7794 | 16.7% to 83.3% |
| fixed_elo | 6 | 5 | 0.4904 | 0.6838 | 66.7% | 0.3751 to 0.6029 | 0.5672 to 0.7979 | 33.3% to 100.0% |
| market | 6 | 5 | 0.5601 | 0.7542 | 50.0% | 0.4112 to 0.6967 | 0.6022 to 0.8935 | 16.7% to 83.3% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 8 | 6 | 0.0102 | -0.0079 to 0.0405 | 0.0103 | -0.0084 to 0.0412 | -12.5 pp | -42.9 pp to 0.0 pp |
| market | 6 | 5 | -0.0647 | -0.1577 to 0.0164 | -0.0657 | -0.1603 to 0.0189 | 0.0 pp | 0.0 pp to 0.0 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 6 | 50.5% | 58.3% | 4.2% | 100.0% |
| fixed_elo | 6 | 46.8% | 60.7% | 5.6% | 83.3% |
| market | 6 | 50.6% | 63.5% | 8.3% | 50.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 8 | 54.9% | 62.5% | 30.6% to 86.3% |
| model | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 40%–60% | 6 | 52.7% | 66.7% | 30.0% to 90.3% |
| fixed_elo | 60%–80% | 2 | 60.7% | 50.0% | 9.5% to 90.5% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 40%–60% | 3 | 54.7% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 60%–80% | 3 | 62.0% | 33.3% | 6.1% to 79.2% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/mlb/captures/20261024T124042211919Z/manifest.json.
Manifest completion field: True. Errors: [{"game_id": "849816", "reason": "Final identity differs from saved forecast"}]. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
