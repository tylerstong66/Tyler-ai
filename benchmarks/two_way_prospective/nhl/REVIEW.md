# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **179** · Settled: **166** · Pending: **13**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-05T06:47:33.326570+00:00 (UTC).

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
| model | 166 | 25 | 0.4831 | 0.6762 | 58.4% | 0.4704 to 0.4959 | 0.6633 to 0.6890 | 51.8% to 65.5% |
| fixed_elo | 166 | 25 | 0.4722 | 0.6647 | 57.2% | 0.4374 to 0.5076 | 0.6277 to 0.7024 | 50.0% to 64.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 166 | 25 | 0.4831 | 0.6762 | 58.4% | 0.4704 to 0.4959 | 0.6633 to 0.6890 | 51.8% to 65.5% |
| fixed_elo | 166 | 25 | 0.4722 | 0.6647 | 57.2% | 0.4374 to 0.5076 | 0.6277 to 0.7024 | 50.0% to 64.7% |
| market | 166 | 25 | 0.4610 | 0.6526 | 57.2% | 0.4375 to 0.4838 | 0.6283 to 0.6762 | 49.7% to 64.9% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 166 | 25 | 0.0109 | -0.0119 to 0.0332 | 0.0115 | -0.0135 to 0.0357 | 1.2 pp | -1.0 pp to 3.4 pp |
| market | 166 | 25 | 0.0221 | 0.0084 to 0.0356 | 0.0235 | 0.0093 to 0.0379 | 1.2 pp | -5.7 pp to 7.6 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 166 | 39.1% | 62.9% | 3.6% | 98.2% |
| fixed_elo | 166 | 22.7% | 82.1% | 10.0% | 57.8% |
| market | 166 | 28.6% | 77.2% | 8.1% | 66.3% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 163 | 51.9% | 57.1% | 49.4% to 64.4% |
| model | 60%–80% | 2 | 62.1% | 100.0% | 34.2% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 8 | 32.3% | 25.0% | 7.1% to 59.1% |
| fixed_elo | 40%–60% | 96 | 50.9% | 54.2% | 44.2% to 63.8% |
| fixed_elo | 60%–80% | 61 | 67.0% | 65.6% | 53.0% to 76.3% |
| fixed_elo | 80%–100% | 1 | 82.1% | 100.0% | 20.7% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 15 | 36.0% | 40.0% | 19.8% to 64.3% |
| market (paired only) | 40%–60% | 110 | 51.3% | 52.7% | 43.5% to 61.8% |
| market (paired only) | 60%–80% | 41 | 65.6% | 75.6% | 60.7% to 86.2% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261106T022703948886Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
