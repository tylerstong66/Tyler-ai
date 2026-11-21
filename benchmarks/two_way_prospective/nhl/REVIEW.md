# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **285** · Settled: **273** · Pending: **12**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-20T12:53:56.656574+00:00 (UTC).

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
| model | 273 | 40 | 0.4857 | 0.6788 | 57.1% | 0.4757 to 0.4955 | 0.6687 to 0.6887 | 51.8% to 62.7% |
| fixed_elo | 273 | 40 | 0.4818 | 0.6753 | 56.0% | 0.4548 to 0.5091 | 0.6465 to 0.7043 | 50.4% to 61.8% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 273 | 40 | 0.4857 | 0.6788 | 57.1% | 0.4757 to 0.4955 | 0.6687 to 0.6887 | 51.8% to 62.7% |
| fixed_elo | 273 | 40 | 0.4818 | 0.6753 | 56.0% | 0.4548 to 0.5091 | 0.6465 to 0.7043 | 50.4% to 61.8% |
| market | 273 | 40 | 0.4688 | 0.6610 | 57.1% | 0.4492 to 0.4875 | 0.6404 to 0.6806 | 51.4% to 62.8% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 273 | 40 | 0.0039 | -0.0135 to 0.0213 | 0.0035 | -0.0160 to 0.0224 | 1.1 pp | -0.4 pp to 2.7 pp |
| market | 273 | 40 | 0.0169 | 0.0056 to 0.0284 | 0.0178 | 0.0055 to 0.0302 | 0.0 pp | -5.6 pp to 6.0 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 273 | 39.1% | 65.3% | 3.7% | 96.7% |
| fixed_elo | 273 | 22.7% | 86.1% | 10.3% | 56.8% |
| market | 273 | 28.6% | 78.2% | 8.0% | 68.5% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 264 | 51.8% | 50.8% | 44.8% to 56.7% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 15 | 33.7% | 20.0% | 7.0% to 45.2% |
| fixed_elo | 40%–60% | 155 | 51.2% | 45.8% | 38.2% to 53.7% |
| fixed_elo | 60%–80% | 100 | 66.9% | 64.0% | 54.2% to 72.7% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 20 | 35.8% | 35.0% | 18.1% to 56.7% |
| market (paired only) | 40%–60% | 187 | 50.7% | 47.1% | 40.0% to 54.2% |
| market (paired only) | 60%–80% | 66 | 66.0% | 68.2% | 56.2% to 78.2% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261121T021532311550Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
