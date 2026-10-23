# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **85** · Settled: **82** · Pending: **3**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-23T10:04:22.344788+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 85 / 100; settled among selected: 82; pending among selected: 3.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 82 | 12 | 0.4847 | 0.6777 | 58.5% | 0.4657 to 0.5027 | 0.6586 to 0.6959 | 48.1% to 70.6% |
| fixed_elo | 82 | 12 | 0.4746 | 0.6672 | 57.3% | 0.4231 to 0.5242 | 0.6131 to 0.7194 | 46.4% to 68.8% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 82 | 12 | 0.4847 | 0.6777 | 58.5% | 0.4657 to 0.5027 | 0.6586 to 0.6959 | 48.1% to 70.6% |
| fixed_elo | 82 | 12 | 0.4746 | 0.6672 | 57.3% | 0.4231 to 0.5242 | 0.6131 to 0.7194 | 46.4% to 68.8% |
| market | 82 | 12 | 0.4677 | 0.6593 | 53.7% | 0.4337 to 0.5003 | 0.6237 to 0.6934 | 45.7% to 62.7% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 82 | 12 | 0.0101 | -0.0218 to 0.0430 | 0.0105 | -0.0243 to 0.0460 | 1.2 pp | -2.8 pp to 5.7 pp |
| market | 82 | 12 | 0.0170 | -0.0024 to 0.0346 | 0.0184 | -0.0022 to 0.0374 | 4.9 pp | -3.0 pp to 13.1 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 82 | 39.1% | 61.4% | 3.6% | 97.6% |
| fixed_elo | 82 | 22.7% | 79.3% | 10.1% | 53.7% |
| market | 82 | 28.6% | 76.0% | 8.1% | 68.3% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 80 | 51.9% | 62.5% | 51.5% to 72.3% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 5 | 32.0% | 20.0% | 3.6% to 62.4% |
| fixed_elo | 40%–60% | 44 | 50.7% | 63.6% | 48.9% to 76.2% |
| fixed_elo | 60%–80% | 33 | 66.4% | 66.7% | 49.6% to 80.2% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 8 | 35.2% | 37.5% | 13.7% to 69.4% |
| market (paired only) | 40%–60% | 56 | 52.7% | 60.7% | 47.6% to 72.4% |
| market (paired only) | 60%–80% | 18 | 66.1% | 77.8% | 54.8% to 91.0% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261023T191345002051Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
