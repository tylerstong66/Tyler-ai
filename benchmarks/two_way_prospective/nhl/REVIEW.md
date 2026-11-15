# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **245** · Settled: **240** · Pending: **5**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-15T10:54:09.981315+00:00 (UTC).

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
| model | 240 | 35 | 0.4818 | 0.6748 | 57.9% | 0.4709 to 0.4926 | 0.6638 to 0.6856 | 51.8% to 64.1% |
| fixed_elo | 240 | 35 | 0.4715 | 0.6634 | 57.1% | 0.4419 to 0.5015 | 0.6317 to 0.6953 | 50.8% to 63.4% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 240 | 35 | 0.4818 | 0.6748 | 57.9% | 0.4709 to 0.4926 | 0.6638 to 0.6856 | 51.8% to 64.1% |
| fixed_elo | 240 | 35 | 0.4715 | 0.6634 | 57.1% | 0.4419 to 0.5015 | 0.6317 to 0.6953 | 50.8% to 63.4% |
| market | 240 | 35 | 0.4596 | 0.6509 | 58.8% | 0.4391 to 0.4794 | 0.6296 to 0.6715 | 52.4% to 64.8% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 240 | 35 | 0.0103 | -0.0091 to 0.0291 | 0.0114 | -0.0098 to 0.0320 | 0.8 pp | -0.8 pp to 2.6 pp |
| market | 240 | 35 | 0.0222 | 0.0108 to 0.0337 | 0.0239 | 0.0118 to 0.0359 | -0.8 pp | -6.8 pp to 5.7 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 240 | 39.1% | 65.3% | 3.7% | 97.1% |
| fixed_elo | 240 | 22.7% | 86.1% | 10.3% | 56.7% |
| market | 240 | 28.6% | 78.2% | 8.1% | 67.9% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 233 | 51.8% | 51.1% | 44.7% to 57.4% |
| model | 60%–80% | 6 | 62.2% | 100.0% | 61.0% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 14 | 33.4% | 21.4% | 7.6% to 47.6% |
| fixed_elo | 40%–60% | 136 | 51.2% | 45.6% | 37.5% to 54.0% |
| fixed_elo | 60%–80% | 88 | 66.8% | 65.9% | 55.5% to 75.0% |
| fixed_elo | 80%–100% | 2 | 84.1% | 100.0% | 34.2% to 100.0% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 18 | 35.6% | 33.3% | 16.3% to 56.3% |
| market (paired only) | 40%–60% | 163 | 50.6% | 47.2% | 39.7% to 54.9% |
| market (paired only) | 60%–80% | 59 | 65.9% | 71.2% | 58.6% to 81.2% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261115T174247001299Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
