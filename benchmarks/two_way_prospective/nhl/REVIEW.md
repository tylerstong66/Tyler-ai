# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **300** · Settled: **299** · Pending: **1**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-24T10:55:34.991072+00:00 (UTC).

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
| model | 299 | 43 | 0.4864 | 0.6795 | 57.9% | 0.4768 to 0.4954 | 0.6698 to 0.6886 | 52.9% to 63.0% |
| fixed_elo | 299 | 43 | 0.4839 | 0.6780 | 56.9% | 0.4583 to 0.5083 | 0.6502 to 0.7043 | 51.4% to 62.1% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 299 | 43 | 0.4864 | 0.6795 | 57.9% | 0.4768 to 0.4954 | 0.6698 to 0.6886 | 52.9% to 63.0% |
| fixed_elo | 299 | 43 | 0.4839 | 0.6780 | 56.9% | 0.4583 to 0.5083 | 0.6502 to 0.7043 | 51.4% to 62.1% |
| market | 299 | 43 | 0.4703 | 0.6626 | 57.2% | 0.4524 to 0.4874 | 0.6437 to 0.6808 | 52.0% to 62.6% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 299 | 43 | 0.0025 | -0.0132 to 0.0183 | 0.0015 | -0.0159 to 0.0197 | 1.0 pp | -0.4 pp to 2.5 pp |
| market | 299 | 43 | 0.0161 | 0.0058 to 0.0268 | 0.0168 | 0.0057 to 0.0282 | 0.7 pp | -4.7 pp to 6.1 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 299 | 39.1% | 65.3% | 3.7% | 96.7% |
| fixed_elo | 299 | 22.7% | 86.1% | 10.5% | 55.5% |
| market | 299 | 28.2% | 78.2% | 8.0% | 68.6% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 2 | 39.1% | 50.0% | 9.5% to 90.5% |
| model | 40%–60% | 289 | 52.0% | 51.2% | 45.5% to 56.9% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 18 | 33.6% | 22.2% | 9.0% to 45.2% |
| fixed_elo | 40%–60% | 166 | 51.4% | 47.0% | 39.5% to 54.6% |
| fixed_elo | 60%–80% | 112 | 67.2% | 63.4% | 54.2% to 71.7% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 22 | 35.4% | 36.4% | 19.7% to 57.0% |
| market (paired only) | 40%–60% | 205 | 50.9% | 47.3% | 40.6% to 54.1% |
| market (paired only) | 60%–80% | 72 | 65.9% | 69.4% | 58.0% to 78.9% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261124T211143762132Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
