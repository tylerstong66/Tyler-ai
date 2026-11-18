# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **261** · Settled: **256** · Pending: **5**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-18T04:21:55.000889+00:00 (UTC).

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
| model | 256 | 38 | 0.4842 | 0.6773 | 57.8% | 0.4740 to 0.4949 | 0.6669 to 0.6882 | 52.1% to 63.6% |
| fixed_elo | 256 | 38 | 0.4774 | 0.6708 | 56.6% | 0.4502 to 0.5079 | 0.6417 to 0.7031 | 50.6% to 62.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 256 | 38 | 0.4842 | 0.6773 | 57.8% | 0.4740 to 0.4949 | 0.6669 to 0.6882 | 52.1% to 63.6% |
| fixed_elo | 256 | 38 | 0.4774 | 0.6708 | 56.6% | 0.4502 to 0.5079 | 0.6417 to 0.7031 | 50.6% to 62.7% |
| market | 256 | 38 | 0.4652 | 0.6572 | 58.6% | 0.4459 to 0.4853 | 0.6369 to 0.6783 | 52.8% to 64.1% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 256 | 38 | 0.0068 | -0.0126 to 0.0243 | 0.0064 | -0.0153 to 0.0258 | 1.2 pp | -0.4 pp to 2.9 pp |
| market | 256 | 38 | 0.0190 | 0.0076 to 0.0300 | 0.0201 | 0.0077 to 0.0320 | -0.8 pp | -6.4 pp to 5.3 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 256 | 39.1% | 65.3% | 3.7% | 96.5% |
| fixed_elo | 256 | 22.7% | 86.1% | 10.4% | 56.6% |
| market | 256 | 28.6% | 78.2% | 8.1% | 68.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 247 | 51.8% | 52.2% | 46.0% to 58.4% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 14 | 33.4% | 21.4% | 7.6% to 47.6% |
| fixed_elo | 40%–60% | 145 | 51.2% | 46.9% | 39.0% to 55.0% |
| fixed_elo | 60%–80% | 94 | 66.9% | 66.0% | 55.9% to 74.7% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 19 | 35.9% | 36.8% | 19.1% to 59.0% |
| market (paired only) | 40%–60% | 174 | 50.6% | 48.3% | 41.0% to 55.7% |
| market (paired only) | 60%–80% | 63 | 66.1% | 69.8% | 57.6% to 79.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261118T042153328725Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
