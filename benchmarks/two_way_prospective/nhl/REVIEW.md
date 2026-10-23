# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **84** · Settled: **81** · Pending: **3**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-23T04:50:14.488414+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 84 / 100; settled among selected: 81; pending among selected: 3.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 81 | 12 | 0.4843 | 0.6774 | 59.3% | 0.4655 to 0.5024 | 0.6584 to 0.6956 | 49.0% to 70.8% |
| fixed_elo | 81 | 12 | 0.4741 | 0.6667 | 58.0% | 0.4227 to 0.5243 | 0.6129 to 0.7196 | 46.9% to 69.1% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 81 | 12 | 0.4843 | 0.6774 | 59.3% | 0.4655 to 0.5024 | 0.6584 to 0.6956 | 49.0% to 70.8% |
| fixed_elo | 81 | 12 | 0.4741 | 0.6667 | 58.0% | 0.4227 to 0.5243 | 0.6129 to 0.7196 | 46.9% to 69.1% |
| market | 81 | 12 | 0.4647 | 0.6563 | 54.3% | 0.4325 to 0.4976 | 0.6224 to 0.6907 | 46.7% to 63.0% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 81 | 12 | 0.0103 | -0.0218 to 0.0431 | 0.0107 | -0.0245 to 0.0460 | 1.2 pp | -2.9 pp to 5.7 pp |
| market | 81 | 12 | 0.0196 | -0.0006 to 0.0364 | 0.0210 | -0.0005 to 0.0392 | 4.9 pp | -3.1 pp to 13.3 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 81 | 39.1% | 61.4% | 3.6% | 97.5% |
| fixed_elo | 81 | 22.7% | 79.3% | 10.2% | 53.1% |
| market | 81 | 28.6% | 76.0% | 8.1% | 67.9% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 79 | 51.9% | 62.0% | 51.0% to 71.9% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 5 | 32.0% | 20.0% | 3.6% to 62.4% |
| fixed_elo | 40%–60% | 43 | 50.8% | 62.8% | 47.9% to 75.6% |
| fixed_elo | 60%–80% | 33 | 66.4% | 66.7% | 49.6% to 80.2% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 8 | 35.2% | 37.5% | 13.7% to 69.4% |
| market (paired only) | 40%–60% | 55 | 52.9% | 60.0% | 46.8% to 71.9% |
| market (paired only) | 60%–80% | 18 | 66.1% | 77.8% | 54.8% to 91.0% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261023T045013245961Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
