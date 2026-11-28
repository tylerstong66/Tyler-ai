# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **342** · Settled: **329** · Pending: **13**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-28T11:45:29.151216+00:00 (UTC).

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
| model | 329 | 46 | 0.4903 | 0.6834 | 55.9% | 0.4800 to 0.5002 | 0.6730 to 0.6934 | 50.3% to 61.6% |
| fixed_elo | 329 | 46 | 0.4951 | 0.6896 | 55.0% | 0.4667 to 0.5235 | 0.6593 to 0.7198 | 49.1% to 60.8% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 329 | 46 | 0.4903 | 0.6834 | 55.9% | 0.4800 to 0.5002 | 0.6730 to 0.6934 | 50.3% to 61.6% |
| fixed_elo | 329 | 46 | 0.4951 | 0.6896 | 55.0% | 0.4667 to 0.5235 | 0.6593 to 0.7198 | 49.1% to 60.8% |
| market | 329 | 46 | 0.4766 | 0.6690 | 56.5% | 0.4565 to 0.4955 | 0.6482 to 0.6887 | 51.3% to 61.6% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 329 | 46 | -0.0048 | -0.0232 to 0.0136 | -0.0062 | -0.0262 to 0.0137 | 0.9 pp | -0.3 pp to 2.3 pp |
| market | 329 | 46 | 0.0137 | 0.0032 to 0.0245 | 0.0144 | 0.0030 to 0.0259 | -0.6 pp | -5.5 pp to 4.7 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 329 | 39.1% | 65.3% | 3.8% | 97.0% |
| fixed_elo | 329 | 22.7% | 86.1% | 10.6% | 55.0% |
| market | 329 | 28.2% | 78.2% | 8.0% | 69.3% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 2 | 39.1% | 50.0% | 9.5% to 90.5% |
| model | 40%–60% | 319 | 52.1% | 50.2% | 44.7% to 55.6% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 18 | 33.6% | 22.2% | 9.0% to 45.2% |
| fixed_elo | 40%–60% | 181 | 51.5% | 47.5% | 40.4% to 54.8% |
| fixed_elo | 60%–80% | 127 | 67.1% | 59.1% | 50.4% to 67.2% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 24 | 35.6% | 41.7% | 24.5% to 61.2% |
| market (paired only) | 40%–60% | 228 | 51.2% | 45.6% | 39.3% to 52.1% |
| market (paired only) | 60%–80% | 77 | 65.9% | 68.8% | 57.8% to 78.1% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261128T114527940167Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
