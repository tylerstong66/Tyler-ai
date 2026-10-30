# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **136** · Settled: **129** · Pending: **7**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-30T07:07:06.224423+00:00 (UTC).

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
| model | 129 | 19 | 0.4835 | 0.6765 | 58.9% | 0.4688 to 0.4985 | 0.6617 to 0.6916 | 50.4% to 68.3% |
| fixed_elo | 129 | 19 | 0.4719 | 0.6645 | 57.4% | 0.4323 to 0.5141 | 0.6230 to 0.7089 | 47.5% to 67.3% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 129 | 19 | 0.4835 | 0.6765 | 58.9% | 0.4688 to 0.4985 | 0.6617 to 0.6916 | 50.4% to 68.3% |
| fixed_elo | 129 | 19 | 0.4719 | 0.6645 | 57.4% | 0.4323 to 0.5141 | 0.6230 to 0.7089 | 47.5% to 67.3% |
| market | 129 | 19 | 0.4663 | 0.6582 | 56.6% | 0.4414 to 0.4933 | 0.6322 to 0.6862 | 49.1% to 64.2% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 129 | 19 | 0.0116 | -0.0158 to 0.0366 | 0.0120 | -0.0175 to 0.0388 | 1.6 pp | -1.3 pp to 4.6 pp |
| market | 129 | 19 | 0.0172 | 0.0019 to 0.0304 | 0.0183 | 0.0023 to 0.0324 | 2.3 pp | -4.9 pp to 9.2 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 129 | 39.1% | 61.4% | 3.5% | 98.4% |
| fixed_elo | 129 | 22.7% | 79.3% | 10.0% | 56.6% |
| market | 129 | 28.6% | 76.0% | 8.1% | 66.7% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 127 | 52.0% | 59.1% | 50.4% to 67.2% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 6 | 32.1% | 16.7% | 3.0% to 56.4% |
| fixed_elo | 40%–60% | 73 | 51.1% | 57.5% | 46.1% to 68.2% |
| fixed_elo | 60%–80% | 50 | 66.8% | 66.0% | 52.2% to 77.6% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 11 | 35.5% | 36.4% | 15.2% to 64.6% |
| market (paired only) | 40%–60% | 86 | 51.7% | 55.8% | 45.3% to 65.8% |
| market (paired only) | 60%–80% | 32 | 65.2% | 75.0% | 57.9% to 86.7% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261030T192257613396Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
