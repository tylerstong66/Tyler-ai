# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **226** · Settled: **224** · Pending: **2**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-13T07:58:42.885062+00:00 (UTC).

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
| model | 224 | 33 | 0.4796 | 0.6725 | 59.4% | 0.4692 to 0.4900 | 0.6621 to 0.6831 | 53.6% to 65.4% |
| fixed_elo | 224 | 33 | 0.4640 | 0.6555 | 58.5% | 0.4361 to 0.4917 | 0.6263 to 0.6850 | 52.2% to 64.8% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 224 | 33 | 0.4796 | 0.6725 | 59.4% | 0.4692 to 0.4900 | 0.6621 to 0.6831 | 53.6% to 65.4% |
| fixed_elo | 224 | 33 | 0.4640 | 0.6555 | 58.5% | 0.4361 to 0.4917 | 0.6263 to 0.6850 | 52.2% to 64.8% |
| market | 224 | 33 | 0.4561 | 0.6474 | 58.9% | 0.4369 to 0.4766 | 0.6273 to 0.6684 | 52.2% to 65.2% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 224 | 33 | 0.0156 | -0.0018 to 0.0333 | 0.0171 | -0.0020 to 0.0363 | 0.9 pp | -0.8 pp to 2.6 pp |
| market | 224 | 33 | 0.0234 | 0.0110 to 0.0353 | 0.0252 | 0.0121 to 0.0376 | 0.4 pp | -5.8 pp to 6.9 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 224 | 39.1% | 65.3% | 3.6% | 97.3% |
| fixed_elo | 224 | 22.7% | 86.1% | 10.3% | 58.0% |
| market | 224 | 28.6% | 78.2% | 8.0% | 68.3% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 218 | 51.8% | 54.1% | 47.5% to 60.6% |
| model | 60%–80% | 5 | 62.3% | 100.0% | 56.6% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 12 | 32.7% | 25.0% | 8.9% to 53.2% |
| fixed_elo | 40%–60% | 130 | 51.2% | 47.7% | 39.3% to 56.2% |
| fixed_elo | 60%–80% | 80 | 67.0% | 70.0% | 59.2% to 78.9% |
| fixed_elo | 80%–100% | 2 | 84.1% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 17 | 35.8% | 35.3% | 17.3% to 58.7% |
| market (paired only) | 40%–60% | 153 | 50.7% | 49.7% | 41.9% to 57.5% |
| market (paired only) | 60%–80% | 54 | 65.9% | 75.9% | 63.1% to 85.4% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261113T075842134702Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
