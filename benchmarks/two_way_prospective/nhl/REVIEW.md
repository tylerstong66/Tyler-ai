# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **129** · Settled: **118** · Pending: **11**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-29T08:29:49.361304+00:00 (UTC).

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
| model | 118 | 18 | 0.4852 | 0.6782 | 59.3% | 0.4694 to 0.5007 | 0.6624 to 0.6939 | 50.0% to 69.5% |
| fixed_elo | 118 | 18 | 0.4754 | 0.6685 | 57.6% | 0.4310 to 0.5193 | 0.6218 to 0.7147 | 47.6% to 68.2% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 118 | 18 | 0.4852 | 0.6782 | 59.3% | 0.4694 to 0.5007 | 0.6624 to 0.6939 | 50.0% to 69.5% |
| fixed_elo | 118 | 18 | 0.4754 | 0.6685 | 57.6% | 0.4310 to 0.5193 | 0.6218 to 0.7147 | 47.6% to 68.2% |
| market | 118 | 18 | 0.4689 | 0.6609 | 55.1% | 0.4401 to 0.4976 | 0.6309 to 0.6909 | 47.2% to 63.1% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 118 | 18 | 0.0098 | -0.0188 to 0.0386 | 0.0097 | -0.0210 to 0.0404 | 1.7 pp | -1.6 pp to 4.9 pp |
| market | 118 | 18 | 0.0163 | -0.0010 to 0.0312 | 0.0174 | -0.0008 to 0.0333 | 4.2 pp | -1.8 pp to 11.2 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 118 | 39.1% | 61.4% | 3.5% | 98.3% |
| fixed_elo | 118 | 22.7% | 79.3% | 9.9% | 56.8% |
| market | 118 | 28.6% | 76.0% | 8.0% | 67.8% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 116 | 52.0% | 59.5% | 50.4% to 68.0% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 6 | 32.1% | 16.7% | 3.0% to 56.4% |
| fixed_elo | 40%–60% | 67 | 51.3% | 59.7% | 47.7% to 70.6% |
| fixed_elo | 60%–80% | 45 | 66.4% | 64.4% | 49.8% to 76.8% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 11 | 35.5% | 36.4% | 15.2% to 64.6% |
| market (paired only) | 40%–60% | 80 | 51.8% | 57.5% | 46.6% to 67.7% |
| market (paired only) | 60%–80% | 27 | 65.3% | 74.1% | 55.3% to 86.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261029T082947213247Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
