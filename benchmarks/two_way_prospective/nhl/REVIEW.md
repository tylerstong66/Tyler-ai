# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **258** · Settled: **247** · Pending: **11**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-17T14:24:51.009082+00:00 (UTC).

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
| model | 247 | 37 | 0.4840 | 0.6771 | 57.5% | 0.4736 to 0.4948 | 0.6665 to 0.6880 | 51.6% to 63.5% |
| fixed_elo | 247 | 37 | 0.4774 | 0.6706 | 56.7% | 0.4496 to 0.5074 | 0.6405 to 0.7026 | 50.2% to 62.9% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 247 | 37 | 0.4840 | 0.6771 | 57.5% | 0.4736 to 0.4948 | 0.6665 to 0.6880 | 51.6% to 63.5% |
| fixed_elo | 247 | 37 | 0.4774 | 0.6706 | 56.7% | 0.4496 to 0.5074 | 0.6405 to 0.7026 | 50.2% to 62.9% |
| market | 247 | 37 | 0.4652 | 0.6573 | 58.7% | 0.4447 to 0.4857 | 0.6357 to 0.6794 | 52.9% to 64.6% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 247 | 37 | 0.0066 | -0.0125 to 0.0244 | 0.0065 | -0.0153 to 0.0262 | 0.8 pp | -0.8 pp to 2.6 pp |
| market | 247 | 37 | 0.0188 | 0.0067 to 0.0307 | 0.0198 | 0.0068 to 0.0325 | -1.2 pp | -7.3 pp to 5.2 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 247 | 39.1% | 65.3% | 3.7% | 96.4% |
| fixed_elo | 247 | 22.7% | 86.1% | 10.4% | 56.7% |
| market | 247 | 28.6% | 78.2% | 8.2% | 67.6% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 238 | 51.8% | 51.7% | 45.4% to 58.0% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 14 | 33.4% | 21.4% | 7.6% to 47.6% |
| fixed_elo | 40%–60% | 140 | 51.1% | 46.4% | 38.4% to 54.7% |
| fixed_elo | 60%–80% | 90 | 66.9% | 65.6% | 55.3% to 74.6% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 19 | 35.9% | 36.8% | 19.1% to 59.0% |
| market (paired only) | 40%–60% | 167 | 50.6% | 47.9% | 40.5% to 55.4% |
| market (paired only) | 60%–80% | 61 | 66.2% | 68.9% | 56.4% to 79.1% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261117T225250467814Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
