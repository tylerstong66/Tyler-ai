# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **200** · Settled: **197** · Pending: **3**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-09T06:30:07.280752+00:00 (UTC).

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
| model | 197 | 29 | 0.4781 | 0.6710 | 60.4% | 0.4663 to 0.4902 | 0.6591 to 0.6833 | 54.1% to 66.8% |
| fixed_elo | 197 | 29 | 0.4603 | 0.6517 | 59.4% | 0.4288 to 0.4932 | 0.6183 to 0.6866 | 52.6% to 65.9% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 197 | 29 | 0.4781 | 0.6710 | 60.4% | 0.4663 to 0.4902 | 0.6591 to 0.6833 | 54.1% to 66.8% |
| fixed_elo | 197 | 29 | 0.4603 | 0.6517 | 59.4% | 0.4288 to 0.4932 | 0.6183 to 0.6866 | 52.6% to 65.9% |
| market | 197 | 29 | 0.4542 | 0.6454 | 58.9% | 0.4319 to 0.4768 | 0.6220 to 0.6689 | 51.7% to 65.7% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 197 | 29 | 0.0177 | -0.0030 to 0.0377 | 0.0193 | -0.0033 to 0.0410 | 1.0 pp | -1.0 pp to 2.9 pp |
| market | 197 | 29 | 0.0238 | 0.0105 to 0.0368 | 0.0257 | 0.0116 to 0.0393 | 1.5 pp | -4.6 pp to 7.6 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 197 | 39.1% | 65.3% | 3.7% | 97.0% |
| fixed_elo | 197 | 22.7% | 86.1% | 10.4% | 56.9% |
| market | 197 | 28.6% | 78.2% | 8.2% | 66.5% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 191 | 51.9% | 56.5% | 49.5% to 63.4% |
| model | 60%–80% | 5 | 62.3% | 100.0% | 56.6% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 9 | 32.7% | 22.2% | 6.3% to 54.7% |
| fixed_elo | 40%–60% | 112 | 51.0% | 51.8% | 42.6% to 60.8% |
| fixed_elo | 60%–80% | 74 | 67.1% | 68.9% | 57.7% to 78.3% |
| fixed_elo | 80%–100% | 2 | 84.1% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 15 | 36.0% | 40.0% | 19.8% to 64.3% |
| market (paired only) | 40%–60% | 131 | 50.8% | 51.9% | 43.4% to 60.3% |
| market (paired only) | 60%–80% | 51 | 66.2% | 76.5% | 63.2% to 86.0% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261109T173001044103Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
