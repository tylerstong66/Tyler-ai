# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **214** · Settled: **207** · Pending: **7**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-11T06:21:51.216999+00:00 (UTC).

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
| model | 207 | 31 | 0.4786 | 0.6716 | 60.4% | 0.4674 to 0.4904 | 0.6603 to 0.6835 | 54.3% to 66.7% |
| fixed_elo | 207 | 31 | 0.4615 | 0.6529 | 59.4% | 0.4320 to 0.4930 | 0.6216 to 0.6862 | 52.7% to 65.9% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 207 | 31 | 0.4786 | 0.6716 | 60.4% | 0.4674 to 0.4904 | 0.6603 to 0.6835 | 54.3% to 66.7% |
| fixed_elo | 207 | 31 | 0.4615 | 0.6529 | 59.4% | 0.4320 to 0.4930 | 0.6216 to 0.6862 | 52.7% to 65.9% |
| market | 207 | 31 | 0.4557 | 0.6469 | 58.9% | 0.4346 to 0.4771 | 0.6249 to 0.6690 | 52.3% to 65.5% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 207 | 31 | 0.0171 | -0.0027 to 0.0355 | 0.0186 | -0.0031 to 0.0389 | 1.0 pp | -0.9 pp to 2.9 pp |
| market | 207 | 31 | 0.0229 | 0.0104 to 0.0354 | 0.0247 | 0.0112 to 0.0380 | 1.4 pp | -4.5 pp to 7.6 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 207 | 39.1% | 65.3% | 3.7% | 97.1% |
| fixed_elo | 207 | 22.7% | 86.1% | 10.3% | 58.0% |
| market | 207 | 28.6% | 78.2% | 8.1% | 68.1% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 201 | 51.9% | 55.7% | 48.8% to 62.4% |
| model | 60%–80% | 5 | 62.3% | 100.0% | 56.6% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 9 | 32.7% | 22.2% | 6.3% to 54.7% |
| fixed_elo | 40%–60% | 120 | 50.9% | 50.0% | 41.2% to 58.8% |
| fixed_elo | 60%–80% | 76 | 67.0% | 69.7% | 58.7% to 78.9% |
| fixed_elo | 80%–100% | 2 | 84.1% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 15 | 36.0% | 40.0% | 19.8% to 64.3% |
| market (paired only) | 40%–60% | 141 | 50.7% | 51.1% | 42.9% to 59.2% |
| market (paired only) | 60%–80% | 51 | 66.2% | 76.5% | 63.2% to 86.0% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261111T215943933796Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
