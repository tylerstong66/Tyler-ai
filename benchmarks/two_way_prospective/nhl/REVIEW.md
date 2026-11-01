# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **147** · Settled: **142** · Pending: **5**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-01T07:34:03.797365+00:00 (UTC).

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
| model | 142 | 21 | 0.4811 | 0.6741 | 59.2% | 0.4676 to 0.4954 | 0.6606 to 0.6886 | 51.4% to 67.5% |
| fixed_elo | 142 | 21 | 0.4659 | 0.6581 | 57.7% | 0.4298 to 0.5051 | 0.6199 to 0.6996 | 49.6% to 66.4% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 142 | 21 | 0.4811 | 0.6741 | 59.2% | 0.4676 to 0.4954 | 0.6606 to 0.6886 | 51.4% to 67.5% |
| fixed_elo | 142 | 21 | 0.4659 | 0.6581 | 57.7% | 0.4298 to 0.5051 | 0.6199 to 0.6996 | 49.6% to 66.4% |
| market | 142 | 21 | 0.4590 | 0.6506 | 58.5% | 0.4325 to 0.4853 | 0.6232 to 0.6782 | 50.5% to 66.9% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 142 | 21 | 0.0152 | -0.0097 to 0.0385 | 0.0161 | -0.0110 to 0.0411 | 1.4 pp | -1.3 pp to 4.1 pp |
| market | 142 | 21 | 0.0221 | 0.0065 to 0.0369 | 0.0235 | 0.0069 to 0.0391 | 0.7 pp | -6.6 pp to 8.2 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 142 | 39.1% | 61.4% | 3.5% | 98.6% |
| fixed_elo | 142 | 22.7% | 79.3% | 10.0% | 56.3% |
| market | 142 | 28.6% | 77.2% | 8.2% | 66.2% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 140 | 52.1% | 58.6% | 50.3% to 66.4% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 6 | 32.1% | 16.7% | 3.0% to 56.4% |
| fixed_elo | 40%–60% | 80 | 50.9% | 55.0% | 44.1% to 65.4% |
| fixed_elo | 60%–80% | 56 | 66.8% | 67.9% | 54.8% to 78.6% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 12 | 35.9% | 41.7% | 19.3% to 68.0% |
| market (paired only) | 40%–60% | 94 | 51.4% | 53.2% | 43.2% to 63.0% |
| market (paired only) | 60%–80% | 36 | 65.5% | 77.8% | 61.9% to 88.3% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261101T151004887462Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
