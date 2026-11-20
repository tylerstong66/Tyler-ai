# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **273** · Settled: **268** · Pending: **5**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-20T03:15:57.427042+00:00 (UTC).

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
| model | 268 | 40 | 0.4867 | 0.6798 | 56.7% | 0.4763 to 0.4973 | 0.6692 to 0.6905 | 51.2% to 62.4% |
| fixed_elo | 268 | 40 | 0.4844 | 0.6781 | 55.6% | 0.4557 to 0.5126 | 0.6475 to 0.7084 | 49.8% to 61.5% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 268 | 40 | 0.4867 | 0.6798 | 56.7% | 0.4763 to 0.4973 | 0.6692 to 0.6905 | 51.2% to 62.4% |
| fixed_elo | 268 | 40 | 0.4844 | 0.6781 | 55.6% | 0.4557 to 0.5126 | 0.6475 to 0.7084 | 49.8% to 61.5% |
| market | 268 | 40 | 0.4709 | 0.6631 | 56.7% | 0.4502 to 0.4919 | 0.6414 to 0.6854 | 50.6% to 62.6% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 268 | 40 | 0.0023 | -0.0159 to 0.0208 | 0.0017 | -0.0183 to 0.0218 | 1.1 pp | -0.4 pp to 2.8 pp |
| market | 268 | 40 | 0.0158 | 0.0033 to 0.0280 | 0.0167 | 0.0032 to 0.0297 | 0.0 pp | -5.7 pp to 6.0 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 268 | 39.1% | 65.3% | 3.7% | 96.6% |
| fixed_elo | 268 | 22.7% | 86.1% | 10.3% | 57.1% |
| market | 268 | 28.6% | 78.2% | 8.0% | 68.7% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 259 | 51.8% | 51.0% | 44.9% to 57.0% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 14 | 33.4% | 21.4% | 7.6% to 47.6% |
| fixed_elo | 40%–60% | 153 | 51.2% | 46.4% | 38.7% to 54.3% |
| fixed_elo | 60%–80% | 98 | 66.8% | 63.3% | 53.4% to 72.1% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 19 | 35.9% | 36.8% | 19.1% to 59.0% |
| market (paired only) | 40%–60% | 184 | 50.8% | 47.3% | 40.2% to 54.5% |
| market (paired only) | 60%–80% | 65 | 66.1% | 67.7% | 55.6% to 77.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261120T031556761277Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
