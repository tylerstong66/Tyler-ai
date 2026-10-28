# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **118** · Settled: **114** · Pending: **4**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-28T09:40:39.438847+00:00 (UTC).

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
| model | 114 | 17 | 0.4874 | 0.6805 | 57.9% | 0.4720 to 0.5035 | 0.6650 to 0.6967 | 49.0% to 67.1% |
| fixed_elo | 114 | 17 | 0.4820 | 0.6753 | 56.1% | 0.4395 to 0.5270 | 0.6306 to 0.7228 | 45.9% to 66.0% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 114 | 17 | 0.4874 | 0.6805 | 57.9% | 0.4720 to 0.5035 | 0.6650 to 0.6967 | 49.0% to 67.1% |
| fixed_elo | 114 | 17 | 0.4820 | 0.6753 | 56.1% | 0.4395 to 0.5270 | 0.6306 to 0.7228 | 45.9% to 66.0% |
| market | 114 | 17 | 0.4741 | 0.6662 | 54.4% | 0.4482 to 0.5022 | 0.6394 to 0.6956 | 46.6% to 61.9% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 114 | 17 | 0.0054 | -0.0237 to 0.0321 | 0.0052 | -0.0262 to 0.0340 | 1.8 pp | -1.6 pp to 5.2 pp |
| market | 114 | 17 | 0.0134 | -0.0041 to 0.0267 | 0.0143 | -0.0041 to 0.0287 | 3.5 pp | -2.9 pp to 10.3 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 114 | 39.1% | 61.4% | 3.5% | 98.2% |
| fixed_elo | 114 | 22.7% | 79.3% | 9.8% | 57.0% |
| market | 114 | 28.6% | 76.0% | 7.9% | 69.3% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 112 | 51.9% | 58.0% | 48.8% to 66.8% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 6 | 32.1% | 16.7% | 3.0% to 56.4% |
| fixed_elo | 40%–60% | 65 | 51.0% | 58.5% | 46.3% to 69.6% |
| fixed_elo | 60%–80% | 43 | 66.5% | 62.8% | 47.9% to 75.6% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 11 | 35.5% | 36.4% | 15.2% to 64.6% |
| market (paired only) | 40%–60% | 79 | 51.9% | 57.0% | 46.0% to 67.3% |
| market (paired only) | 60%–80% | 24 | 65.3% | 70.8% | 50.8% to 85.1% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261028T213915701868Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
