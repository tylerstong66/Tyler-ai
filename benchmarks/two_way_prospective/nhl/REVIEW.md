# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **240** · Settled: **226** · Pending: **14**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-14T11:28:25.081687+00:00 (UTC).

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
| model | 226 | 34 | 0.4797 | 0.6727 | 59.3% | 0.4688 to 0.4906 | 0.6617 to 0.6837 | 53.7% to 65.3% |
| fixed_elo | 226 | 34 | 0.4646 | 0.6561 | 58.4% | 0.4354 to 0.4928 | 0.6248 to 0.6858 | 52.5% to 64.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 226 | 34 | 0.4797 | 0.6727 | 59.3% | 0.4688 to 0.4906 | 0.6617 to 0.6837 | 53.7% to 65.3% |
| fixed_elo | 226 | 34 | 0.4646 | 0.6561 | 58.4% | 0.4354 to 0.4928 | 0.6248 to 0.6858 | 52.5% to 64.7% |
| market | 226 | 34 | 0.4565 | 0.6478 | 58.8% | 0.4353 to 0.4756 | 0.6256 to 0.6677 | 52.1% to 65.4% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 226 | 34 | 0.0151 | -0.0023 to 0.0336 | 0.0166 | -0.0027 to 0.0365 | 0.9 pp | -0.8 pp to 2.6 pp |
| market | 226 | 34 | 0.0232 | 0.0114 to 0.0351 | 0.0249 | 0.0125 to 0.0377 | 0.4 pp | -5.6 pp to 7.0 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 226 | 39.1% | 65.3% | 3.7% | 97.3% |
| fixed_elo | 226 | 22.7% | 86.1% | 10.3% | 57.5% |
| market | 226 | 28.6% | 78.2% | 8.1% | 67.7% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 220 | 51.8% | 53.6% | 47.0% to 60.1% |
| model | 60%–80% | 5 | 62.3% | 100.0% | 56.6% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 13 | 32.9% | 23.1% | 8.2% to 50.3% |
| fixed_elo | 40%–60% | 130 | 51.2% | 47.7% | 39.3% to 56.2% |
| fixed_elo | 60%–80% | 81 | 66.9% | 69.1% | 58.4% to 78.1% |
| fixed_elo | 80%–100% | 2 | 84.1% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 18 | 35.6% | 33.3% | 16.3% to 56.3% |
| market (paired only) | 40%–60% | 153 | 50.7% | 49.7% | 41.9% to 57.5% |
| market (paired only) | 60%–80% | 55 | 65.9% | 74.5% | 61.7% to 84.2% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261114T112824338635Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
