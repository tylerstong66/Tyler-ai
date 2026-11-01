# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **147** · Settled: **144** · Pending: **3**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-01T23:36:14.896894+00:00 (UTC).

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
| model | 144 | 22 | 0.4802 | 0.6732 | 59.0% | 0.4668 to 0.4942 | 0.6597 to 0.6874 | 51.4% to 67.1% |
| fixed_elo | 144 | 22 | 0.4645 | 0.6564 | 57.6% | 0.4274 to 0.5028 | 0.6175 to 0.6969 | 49.3% to 66.3% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 144 | 22 | 0.4802 | 0.6732 | 59.0% | 0.4668 to 0.4942 | 0.6597 to 0.6874 | 51.4% to 67.1% |
| fixed_elo | 144 | 22 | 0.4645 | 0.6564 | 57.6% | 0.4274 to 0.5028 | 0.6175 to 0.6969 | 49.3% to 66.3% |
| market | 144 | 22 | 0.4573 | 0.6489 | 58.3% | 0.4311 to 0.4835 | 0.6216 to 0.6762 | 50.4% to 66.9% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 144 | 22 | 0.0157 | -0.0086 to 0.0398 | 0.0168 | -0.0094 to 0.0427 | 1.4 pp | -1.3 pp to 4.0 pp |
| market | 144 | 22 | 0.0229 | 0.0084 to 0.0375 | 0.0243 | 0.0091 to 0.0397 | 0.7 pp | -7.0 pp to 8.0 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 144 | 39.1% | 62.9% | 3.6% | 97.9% |
| fixed_elo | 144 | 22.7% | 82.1% | 10.2% | 56.2% |
| market | 144 | 28.6% | 77.2% | 8.2% | 66.0% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 141 | 52.1% | 58.2% | 49.9% to 66.0% |
| model | 60%–80% | 2 | 62.1% | 100.0% | 34.2% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 6 | 32.1% | 16.7% | 3.0% to 56.4% |
| fixed_elo | 40%–60% | 81 | 51.0% | 54.3% | 43.5% to 64.7% |
| fixed_elo | 60%–80% | 56 | 66.8% | 67.9% | 54.8% to 78.6% |
| fixed_elo | 80%–100% | 1 | 82.1% | 100.0% | 20.7% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 12 | 35.9% | 41.7% | 19.3% to 68.0% |
| market (paired only) | 40%–60% | 95 | 51.4% | 52.6% | 42.7% to 62.4% |
| market (paired only) | 60%–80% | 37 | 65.6% | 78.4% | 62.8% to 88.6% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261101T233613778784Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
