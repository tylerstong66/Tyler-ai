# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **341** · Settled: **326** · Pending: **15**

100-settlement milestone: **ready_for_human_review**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-11-28T02:41:34.009659+00:00 (UTC).

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
| model | 326 | 46 | 0.4893 | 0.6824 | 56.4% | 0.4798 to 0.4983 | 0.6728 to 0.6914 | 51.2% to 61.7% |
| fixed_elo | 326 | 46 | 0.4920 | 0.6864 | 55.5% | 0.4656 to 0.5176 | 0.6584 to 0.7132 | 50.0% to 61.1% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 326 | 46 | 0.4893 | 0.6824 | 56.4% | 0.4798 to 0.4983 | 0.6728 to 0.6914 | 51.2% to 61.7% |
| fixed_elo | 326 | 46 | 0.4920 | 0.6864 | 55.5% | 0.4656 to 0.5176 | 0.6584 to 0.7132 | 50.0% to 61.1% |
| market | 326 | 46 | 0.4744 | 0.6667 | 57.1% | 0.4561 to 0.4916 | 0.6474 to 0.6849 | 51.9% to 61.9% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 326 | 46 | -0.0027 | -0.0194 to 0.0144 | -0.0040 | -0.0220 to 0.0146 | 0.9 pp | -0.3 pp to 2.3 pp |
| market | 326 | 46 | 0.0149 | 0.0052 to 0.0250 | 0.0156 | 0.0050 to 0.0266 | -0.6 pp | -5.6 pp to 4.7 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 326 | 39.1% | 65.3% | 3.8% | 96.9% |
| fixed_elo | 326 | 22.7% | 86.1% | 10.6% | 55.2% |
| market | 326 | 28.2% | 78.2% | 8.0% | 69.3% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 2 | 39.1% | 50.0% | 9.5% to 90.5% |
| model | 40%–60% | 316 | 52.1% | 50.6% | 45.1% to 56.1% |
| model | 60%–80% | 8 | 62.2% | 75.0% | 40.9% to 92.9% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 18 | 33.6% | 22.2% | 9.0% to 45.2% |
| fixed_elo | 40%–60% | 180 | 51.4% | 47.8% | 40.6% to 55.0% |
| fixed_elo | 60%–80% | 125 | 67.1% | 60.0% | 51.2% to 68.2% |
| fixed_elo | 80%–100% | 3 | 84.1% | 66.7% | 20.8% to 93.9% |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 24 | 35.6% | 41.7% | 24.5% to 61.2% |
| market (paired only) | 40%–60% | 226 | 51.1% | 46.0% | 39.6% to 52.5% |
| market (paired only) | 60%–80% | 76 | 65.9% | 69.7% | 58.7% to 78.9% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261128T024132513084Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
