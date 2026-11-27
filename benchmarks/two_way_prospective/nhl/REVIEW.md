# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **329** · Settled: **314** · Pending: **15**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-26T08:18:13.187573+00:00 (UTC).

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
| model | 314 | 45 | 0.4876 | 0.6807 | 57.6% | 0.4781 to 0.4966 | 0.6710 to 0.6898 | 52.7% to 62.4% |
| fixed_elo | 314 | 45 | 0.4872 | 0.6815 | 56.7% | 0.4616 to 0.5116 | 0.6536 to 0.7083 | 51.4% to 61.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 314 | 45 | 0.4876 | 0.6807 | 57.6% | 0.4781 to 0.4966 | 0.6710 to 0.6898 | 52.7% to 62.4% |
| fixed_elo | 314 | 45 | 0.4872 | 0.6815 | 56.7% | 0.4616 to 0.5116 | 0.6536 to 0.7083 | 51.4% to 61.7% |
| market | 314 | 45 | 0.4715 | 0.6638 | 57.6% | 0.4535 to 0.4886 | 0.6448 to 0.6818 | 52.7% to 62.5% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 314 | 45 | 0.0005 | -0.0155 to 0.0166 | -0.0007 | -0.0183 to 0.0172 | 1.0 pp | -0.4 pp to 2.4 pp |
| market | 314 | 45 | 0.0162 | 0.0062 to 0.0264 | 0.0169 | 0.0061 to 0.0279 | 0.0 pp | -5.0 pp to 5.2 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 314 | 39.1% | 65.3% | 3.7% | 96.8% |
| fixed_elo | 314 | 22.7% | 86.1% | 10.5% | 55.7% |
| market | 314 | 28.2% | 78.2% | 8.0% | 69.4% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 2 | 39.1% | 50.0% | 9.5% to 90.5% |
| model | 40%–60% | 304 | 52.0% | 51.0% | 45.4% to 56.6% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 18 | 33.6% | 22.2% | 9.0% to 45.2% |
| fixed_elo | 40%–60% | 175 | 51.4% | 47.4% | 40.2% to 54.8% |
| fixed_elo | 60%–80% | 118 | 67.1% | 61.9% | 52.9% to 70.1% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 22 | 35.4% | 36.4% | 19.7% to 57.0% |
| market (paired only) | 40%–60% | 218 | 51.1% | 47.2% | 40.7% to 53.9% |
| market (paired only) | 60%–80% | 74 | 65.8% | 68.9% | 57.7% to 78.3% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261127T021022575988Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
