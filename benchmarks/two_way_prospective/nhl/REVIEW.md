# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **57** · Settled: **52** · Pending: **5**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-19T01:20:21.784950+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **collecting_forecasts**. This is separate from the cumulative 100-settlement flag.
Selected: 57 / 100; settled among selected: 52; pending among selected: 5.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 52 | 8 | 0.4685 | 0.6614 | 65.4% | 0.4508 to 0.4876 | 0.6436 to 0.6807 | 51.1% to 80.0% |
| fixed_elo | 52 | 8 | 0.4321 | 0.6222 | 61.5% | 0.3825 to 0.4843 | 0.5704 to 0.6768 | 45.4% to 75.8% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 52 | 8 | 0.4685 | 0.6614 | 65.4% | 0.4508 to 0.4876 | 0.6436 to 0.6807 | 51.1% to 80.0% |
| fixed_elo | 52 | 8 | 0.4321 | 0.6222 | 61.5% | 0.3825 to 0.4843 | 0.5704 to 0.6768 | 45.4% to 75.8% |
| market | 52 | 8 | 0.4425 | 0.6330 | 57.7% | 0.3985 to 0.4830 | 0.5872 to 0.6754 | 48.2% to 70.6% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 52 | 8 | 0.0364 | 0.0026 to 0.0686 | 0.0393 | 0.0029 to 0.0737 | 3.8 pp | 0.0 pp to 10.4 pp |
| market | 52 | 8 | 0.0260 | 0.0012 to 0.0544 | 0.0285 | 0.0019 to 0.0582 | 7.7 pp | -4.2 pp to 19.5 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 52 | 44.1% | 61.4% | 3.5% | 98.1% |
| fixed_elo | 52 | 34.7% | 79.3% | 10.0% | 53.8% |
| market | 52 | 34.3% | 76.0% | 8.2% | 71.2% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 0 | Unavailable | Unavailable | Unavailable |
| model | 40%–60% | 51 | 51.9% | 56.9% | 43.3% to 69.5% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 3 | 36.4% | 0.0% | 0.0% to 56.1% |
| fixed_elo | 40%–60% | 28 | 50.9% | 50.0% | 32.6% to 67.4% |
| fixed_elo | 60%–80% | 21 | 66.9% | 76.2% | 54.9% to 89.4% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 3 | 36.3% | 0.0% | 0.0% to 56.1% |
| market (paired only) | 40%–60% | 37 | 52.6% | 54.1% | 38.4% to 69.0% |
| market (paired only) | 60%–80% | 12 | 67.7% | 83.3% | 55.2% to 95.3% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261019T012020209472Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
