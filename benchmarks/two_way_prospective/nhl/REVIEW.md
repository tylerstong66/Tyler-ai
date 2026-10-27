# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **114** · Settled: **103** · Pending: **11**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-27T06:17:19.332455+00:00 (UTC).

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
| model | 103 | 16 | 0.4841 | 0.6772 | 60.2% | 0.4691 to 0.5000 | 0.6621 to 0.6932 | 51.0% to 69.8% |
| fixed_elo | 103 | 16 | 0.4726 | 0.6654 | 59.2% | 0.4315 to 0.5168 | 0.6223 to 0.7121 | 50.0% to 68.3% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 103 | 16 | 0.4841 | 0.6772 | 60.2% | 0.4691 to 0.5000 | 0.6621 to 0.6932 | 51.0% to 69.8% |
| fixed_elo | 103 | 16 | 0.4726 | 0.6654 | 59.2% | 0.4315 to 0.5168 | 0.6223 to 0.7121 | 50.0% to 68.3% |
| market | 103 | 16 | 0.4712 | 0.6633 | 55.3% | 0.4433 to 0.5032 | 0.6344 to 0.6964 | 46.2% to 63.8% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 103 | 16 | 0.0116 | -0.0168 to 0.0378 | 0.0118 | -0.0190 to 0.0403 | 1.0 pp | -2.4 pp to 4.4 pp |
| market | 103 | 16 | 0.0129 | -0.0065 to 0.0277 | 0.0139 | -0.0066 to 0.0297 | 4.9 pp | -1.3 pp to 11.9 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 103 | 39.1% | 61.4% | 3.6% | 98.1% |
| fixed_elo | 103 | 22.7% | 79.3% | 10.0% | 55.3% |
| market | 103 | 28.6% | 76.0% | 8.2% | 68.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 101 | 51.8% | 61.4% | 51.6% to 70.3% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 6 | 32.1% | 16.7% | 3.0% to 56.4% |
| fixed_elo | 40%–60% | 57 | 50.7% | 63.2% | 50.2% to 74.5% |
| fixed_elo | 60%–80% | 40 | 66.4% | 65.0% | 49.5% to 77.9% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 11 | 35.5% | 36.4% | 15.2% to 64.6% |
| market (paired only) | 40%–60% | 70 | 52.0% | 61.4% | 49.7% to 72.0% |
| market (paired only) | 60%–80% | 22 | 65.5% | 72.7% | 51.8% to 86.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261027T184312125929Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
