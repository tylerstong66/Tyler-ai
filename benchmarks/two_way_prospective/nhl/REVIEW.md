# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **240** · Settled: **227** · Pending: **13**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-14T22:24:31.619224+00:00 (UTC).

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
| model | 227 | 35 | 0.4789 | 0.6719 | 59.5% | 0.4680 to 0.4899 | 0.6608 to 0.6829 | 53.7% to 65.4% |
| fixed_elo | 227 | 35 | 0.4631 | 0.6545 | 58.6% | 0.4345 to 0.4916 | 0.6241 to 0.6850 | 52.5% to 64.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 227 | 35 | 0.4789 | 0.6719 | 59.5% | 0.4680 to 0.4899 | 0.6608 to 0.6829 | 53.7% to 65.4% |
| fixed_elo | 227 | 35 | 0.4631 | 0.6545 | 58.6% | 0.4345 to 0.4916 | 0.6241 to 0.6850 | 52.5% to 64.7% |
| market | 227 | 35 | 0.4551 | 0.6462 | 59.0% | 0.4353 to 0.4745 | 0.6254 to 0.6665 | 52.4% to 65.5% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 227 | 35 | 0.0158 | -0.0021 to 0.0338 | 0.0173 | -0.0024 to 0.0369 | 0.9 pp | -0.8 pp to 2.7 pp |
| market | 227 | 35 | 0.0238 | 0.0118 to 0.0357 | 0.0257 | 0.0131 to 0.0381 | 0.4 pp | -5.5 pp to 6.7 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 227 | 39.1% | 65.3% | 3.7% | 96.9% |
| fixed_elo | 227 | 22.7% | 86.1% | 10.4% | 57.3% |
| market | 227 | 28.6% | 78.2% | 8.2% | 67.4% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 220 | 51.8% | 53.6% | 47.0% to 60.1% |
| model | 60%–80% | 6 | 62.2% | 100.0% | 61.0% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 13 | 32.9% | 23.1% | 8.2% to 50.3% |
| fixed_elo | 40%–60% | 130 | 51.2% | 47.7% | 39.3% to 56.2% |
| fixed_elo | 60%–80% | 82 | 67.0% | 69.5% | 58.9% to 78.4% |
| fixed_elo | 80%–100% | 2 | 84.1% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 18 | 35.6% | 33.3% | 16.3% to 56.3% |
| market (paired only) | 40%–60% | 153 | 50.7% | 49.7% | 41.9% to 57.5% |
| market (paired only) | 60%–80% | 56 | 66.0% | 75.0% | 62.3% to 84.5% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261114T222430382994Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
