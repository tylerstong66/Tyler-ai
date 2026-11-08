# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **197** · Settled: **193** · Pending: **4**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-08T23:43:19.125022+00:00 (UTC).

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
| model | 193 | 29 | 0.4783 | 0.6713 | 60.1% | 0.4662 to 0.4908 | 0.6591 to 0.6839 | 53.8% to 66.5% |
| fixed_elo | 193 | 29 | 0.4613 | 0.6527 | 59.1% | 0.4292 to 0.4948 | 0.6185 to 0.6885 | 52.1% to 65.7% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 193 | 29 | 0.4783 | 0.6713 | 60.1% | 0.4662 to 0.4908 | 0.6591 to 0.6839 | 53.8% to 66.5% |
| fixed_elo | 193 | 29 | 0.4613 | 0.6527 | 59.1% | 0.4292 to 0.4948 | 0.6185 to 0.6885 | 52.1% to 65.7% |
| market | 193 | 29 | 0.4534 | 0.6445 | 59.1% | 0.4300 to 0.4767 | 0.6202 to 0.6688 | 51.7% to 65.9% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 193 | 29 | 0.0170 | -0.0042 to 0.0373 | 0.0185 | -0.0047 to 0.0407 | 1.0 pp | -1.0 pp to 3.0 pp |
| market | 193 | 29 | 0.0249 | 0.0118 to 0.0379 | 0.0268 | 0.0129 to 0.0405 | 1.0 pp | -5.6 pp to 7.3 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 193 | 39.1% | 65.3% | 3.7% | 96.9% |
| fixed_elo | 193 | 22.7% | 86.1% | 10.4% | 56.5% |
| market | 193 | 28.6% | 78.2% | 8.3% | 65.8% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 187 | 52.0% | 56.1% | 49.0% to 63.1% |
| model | 60%–80% | 5 | 62.3% | 100.0% | 56.6% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 9 | 32.7% | 22.2% | 6.3% to 54.7% |
| fixed_elo | 40%–60% | 109 | 51.1% | 51.4% | 42.1% to 60.6% |
| fixed_elo | 60%–80% | 73 | 67.1% | 68.5% | 57.1% to 78.0% |
| fixed_elo | 80%–100% | 2 | 84.1% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 15 | 36.0% | 40.0% | 19.8% to 64.3% |
| market (paired only) | 40%–60% | 127 | 50.9% | 51.2% | 42.6% to 59.7% |
| market (paired only) | 60%–80% | 51 | 66.2% | 76.5% | 63.2% to 86.0% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261108T234318288825Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
