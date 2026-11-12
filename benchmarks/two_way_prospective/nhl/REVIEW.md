# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **224** · Settled: **213** · Pending: **11**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-12T11:11:21.986091+00:00 (UTC).

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
| model | 213 | 32 | 0.4789 | 0.6718 | 59.6% | 0.4674 to 0.4900 | 0.6602 to 0.6830 | 53.3% to 66.5% |
| fixed_elo | 213 | 32 | 0.4623 | 0.6537 | 58.7% | 0.4318 to 0.4922 | 0.6213 to 0.6857 | 52.0% to 65.6% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 213 | 32 | 0.4789 | 0.6718 | 59.6% | 0.4674 to 0.4900 | 0.6602 to 0.6830 | 53.3% to 66.5% |
| fixed_elo | 213 | 32 | 0.4623 | 0.6537 | 58.7% | 0.4318 to 0.4922 | 0.6213 to 0.6857 | 52.0% to 65.6% |
| market | 213 | 32 | 0.4547 | 0.6459 | 59.6% | 0.4334 to 0.4755 | 0.6236 to 0.6677 | 52.7% to 66.1% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 213 | 32 | 0.0166 | -0.0022 to 0.0358 | 0.0181 | -0.0021 to 0.0392 | 0.9 pp | -0.9 pp to 2.9 pp |
| market | 213 | 32 | 0.0242 | 0.0110 to 0.0367 | 0.0259 | 0.0121 to 0.0391 | 0.0 pp | -6.3 pp to 6.8 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 213 | 39.1% | 65.3% | 3.6% | 97.2% |
| fixed_elo | 213 | 22.7% | 86.1% | 10.2% | 58.2% |
| market | 213 | 28.6% | 78.2% | 8.0% | 68.5% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 207 | 51.9% | 55.1% | 48.3% to 61.7% |
| model | 60%–80% | 5 | 62.3% | 100.0% | 56.6% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 9 | 32.7% | 22.2% | 6.3% to 54.7% |
| fixed_elo | 40%–60% | 124 | 51.1% | 48.4% | 39.8% to 57.1% |
| fixed_elo | 60%–80% | 78 | 67.0% | 70.5% | 59.6% to 79.5% |
| fixed_elo | 80%–100% | 2 | 84.1% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 15 | 36.0% | 40.0% | 19.8% to 64.3% |
| market (paired only) | 40%–60% | 146 | 50.7% | 50.0% | 42.0% to 58.0% |
| market (paired only) | 60%–80% | 52 | 66.1% | 76.9% | 63.9% to 86.3% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261112T185725884729Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
