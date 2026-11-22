# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **292** · Settled: **287** · Pending: **5**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-22T06:49:01.587395+00:00 (UTC).

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
| model | 287 | 41 | 0.4863 | 0.6794 | 57.5% | 0.4769 to 0.4963 | 0.6699 to 0.6895 | 52.2% to 62.8% |
| fixed_elo | 287 | 41 | 0.4833 | 0.6773 | 56.4% | 0.4578 to 0.5101 | 0.6499 to 0.7063 | 50.7% to 62.1% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 287 | 41 | 0.4863 | 0.6794 | 57.5% | 0.4769 to 0.4963 | 0.6699 to 0.6895 | 52.2% to 62.8% |
| fixed_elo | 287 | 41 | 0.4833 | 0.6773 | 56.4% | 0.4578 to 0.5101 | 0.6499 to 0.7063 | 50.7% to 62.1% |
| market | 287 | 41 | 0.4706 | 0.6629 | 57.5% | 0.4511 to 0.4888 | 0.6423 to 0.6822 | 51.9% to 62.7% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 287 | 41 | 0.0030 | -0.0142 to 0.0193 | 0.0022 | -0.0169 to 0.0204 | 1.0 pp | -0.4 pp to 2.6 pp |
| market | 287 | 41 | 0.0158 | 0.0054 to 0.0271 | 0.0165 | 0.0054 to 0.0286 | 0.0 pp | -5.4 pp to 5.6 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 287 | 39.1% | 65.3% | 3.7% | 96.5% |
| fixed_elo | 287 | 22.7% | 86.1% | 10.4% | 56.4% |
| market | 287 | 28.2% | 78.2% | 8.0% | 69.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 2 | 39.1% | 50.0% | 9.5% to 90.5% |
| model | 40%–60% | 277 | 51.9% | 51.3% | 45.4% to 57.1% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 16 | 33.0% | 25.0% | 10.2% to 49.5% |
| fixed_elo | 40%–60% | 162 | 51.3% | 46.3% | 38.8% to 54.0% |
| fixed_elo | 60%–80% | 106 | 66.9% | 64.2% | 54.7% to 72.6% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 21 | 35.4% | 38.1% | 20.8% to 59.1% |
| market (paired only) | 40%–60% | 198 | 50.9% | 47.5% | 40.6% to 54.4% |
| market (paired only) | 60%–80% | 68 | 65.9% | 69.1% | 57.4% to 78.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261122T151750217096Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
