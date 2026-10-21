# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **70** · Settled: **68** · Pending: **2**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-21T10:09:03.373760+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 70 / 100; settled among selected: 68; pending among selected: 2.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 68 | 10 | 0.4798 | 0.6728 | 61.8% | 0.4601 to 0.5013 | 0.6530 to 0.6945 | 50.6% to 73.7% |
| fixed_elo | 68 | 10 | 0.4625 | 0.6547 | 58.8% | 0.4077 to 0.5221 | 0.5971 to 0.7188 | 46.0% to 71.2% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 68 | 10 | 0.4798 | 0.6728 | 61.8% | 0.4601 to 0.5013 | 0.6530 to 0.6945 | 50.6% to 73.7% |
| fixed_elo | 68 | 10 | 0.4625 | 0.6547 | 58.8% | 0.4077 to 0.5221 | 0.5971 to 0.7188 | 46.0% to 71.2% |
| market | 68 | 10 | 0.4587 | 0.6500 | 57.4% | 0.4227 to 0.4957 | 0.6122 to 0.6890 | 49.4% to 66.2% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 68 | 10 | 0.0172 | -0.0213 to 0.0523 | 0.0181 | -0.0243 to 0.0558 | 2.9 pp | 0.0 pp to 7.7 pp |
| market | 68 | 10 | 0.0210 | 0.0002 to 0.0403 | 0.0227 | 0.0003 to 0.0435 | 4.4 pp | -5.9 pp to 13.6 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 68 | 39.1% | 61.4% | 3.6% | 97.1% |
| fixed_elo | 68 | 22.7% | 79.3% | 10.2% | 54.4% |
| market | 68 | 28.6% | 76.0% | 8.4% | 69.1% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 66 | 51.9% | 60.6% | 48.5% to 71.5% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 5 | 32.0% | 20.0% | 3.6% to 62.4% |
| fixed_elo | 40%–60% | 37 | 51.4% | 59.5% | 43.5% to 73.7% |
| fixed_elo | 60%–80% | 26 | 66.7% | 69.2% | 50.0% to 83.5% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 6 | 34.3% | 33.3% | 9.7% to 70.0% |
| market (paired only) | 40%–60% | 47 | 53.1% | 57.4% | 43.3% to 70.5% |
| market (paired only) | 60%–80% | 15 | 66.6% | 80.0% | 54.8% to 93.0% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261021T151510311440Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
