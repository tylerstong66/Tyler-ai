# MLB prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **8** · Settled: **6** · Pending: **2**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-15T22:19:23.232438+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 8 / 100; settled among selected: 6; pending among selected: 2.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 6 | 5 | 0.4694 | 0.6624 | 66.7% | 0.3917 to 0.5251 | 0.5840 to 0.7186 | 33.3% to 100.0% |
| fixed_elo | 6 | 5 | 0.4709 | 0.6640 | 66.7% | 0.3662 to 0.5457 | 0.5579 to 0.7397 | 33.3% to 100.0% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 4 | 4 | 0.5206 | 0.7141 | 50.0% | Unavailable | Unavailable | Unavailable |
| fixed_elo | 4 | 4 | 0.5359 | 0.7299 | 50.0% | Unavailable | Unavailable | Unavailable |
| market | 4 | 4 | 0.5998 | 0.7951 | 50.0% | Unavailable | Unavailable | Unavailable |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 6 | 5 | -0.0015 | -0.0358 to 0.0426 | -0.0016 | -0.0361 to 0.0432 | 0.0 pp | -50.0 pp to 50.0 pp |
| market | 4 | 4 | -0.0791 | Unavailable | -0.0811 | Unavailable | 0.0 pp | Unavailable |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 6 | 55.1% | 66.7% | 30.0% to 90.3% |
| model | 60%–80% | 0 | Unavailable | Unavailable | Unavailable |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 40%–60% | 4 | 52.2% | 75.0% | 30.1% to 95.4% |
| fixed_elo | 60%–80% | 2 | 60.7% | 50.0% | 9.5% to 90.5% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 40%–60% | 2 | 52.6% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 60%–80% | 2 | 61.2% | 0.0% | 0.0% to 65.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/mlb/captures/20261015T221920847439Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
