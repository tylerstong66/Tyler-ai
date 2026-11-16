# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **247** · Settled: **245** · Pending: **2**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-16T11:18:15.681126+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **preserved**. This is separate from the cumulative 100-settlement flag.
Selected: 100 / 100; settled among selected: 100; pending among selected: 0.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.
[Preserved checkpoint review](checkpoints/first_100_enrolled/REVIEW.md). Later games do not change this window.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 245 | 36 | 0.4829 | 0.6759 | 58.0% | 0.4723 to 0.4935 | 0.6652 to 0.6867 | 52.0% to 64.1% |
| fixed_elo | 245 | 36 | 0.4741 | 0.6670 | 57.1% | 0.4449 to 0.5027 | 0.6358 to 0.6978 | 50.9% to 63.4% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 245 | 36 | 0.4829 | 0.6759 | 58.0% | 0.4723 to 0.4935 | 0.6652 to 0.6867 | 52.0% to 64.1% |
| fixed_elo | 245 | 36 | 0.4741 | 0.6670 | 57.1% | 0.4449 to 0.5027 | 0.6358 to 0.6978 | 50.9% to 63.4% |
| market | 245 | 36 | 0.4625 | 0.6543 | 58.8% | 0.4421 to 0.4825 | 0.6327 to 0.6751 | 52.7% to 64.6% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 245 | 36 | 0.0087 | -0.0097 to 0.0274 | 0.0089 | -0.0116 to 0.0296 | 0.8 pp | -0.7 pp to 2.6 pp |
| market | 245 | 36 | 0.0203 | 0.0088 to 0.0319 | 0.0216 | 0.0089 to 0.0340 | -0.8 pp | -6.7 pp to 5.7 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 245 | 39.1% | 65.3% | 3.7% | 96.7% |
| fixed_elo | 245 | 22.7% | 86.1% | 10.4% | 56.7% |
| market | 245 | 28.6% | 78.2% | 8.1% | 67.8% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 237 | 51.8% | 51.5% | 45.1% to 57.8% |
| model | 60%–80% | 7 | 62.4% | 85.7% | 48.7% to 97.4% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 14 | 33.4% | 21.4% | 7.6% to 47.6% |
| fixed_elo | 40%–60% | 139 | 51.1% | 46.0% | 38.0% to 54.3% |
| fixed_elo | 60%–80% | 89 | 66.8% | 66.3% | 56.0% to 75.3% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 19 | 35.9% | 36.8% | 19.1% to 59.0% |
| market (paired only) | 40%–60% | 166 | 50.6% | 47.6% | 40.1% to 55.2% |
| market (paired only) | 60%–80% | 60 | 66.1% | 70.0% | 57.5% to 80.1% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261116T220208784528Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
