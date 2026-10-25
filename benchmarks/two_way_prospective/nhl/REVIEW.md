# NHL prospective benchmark review

**NO BET — actual wagers $0.**

Recorded: **100** · Settled: **97** · Pending: **3**

100-settlement milestone: **collecting**. This flag requests human review; it does not authorize model promotion or wagering.

Latest result verified: 2026-10-25T22:33:49.924589+00:00 (UTC).

Brier is the sum over outcomes (range 0–2); lower Brier and log loss are better.
Accuracy uses the highest-probability outcome. Two-way ties at 50% select home; NFL three-way ties in probability use home, away, tie order.

Uncertainty unit: Eastern scheduled game date. CIs require at least 5 blocks.

## First-100-enrolled checkpoint

Status: **awaiting_selected_results**. This is separate from the cumulative 100-settlement flag.
Selected: 100 / 100; settled among selected: 97; pending among selected: 3.
First 100 by recorded_at in UTC, then game_id; never by outcome, price or settlement order.

## All decisive games — conditional two-way scores

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 97 | 15 | 0.4830 | 0.6761 | 60.8% | 0.4673 to 0.4984 | 0.6602 to 0.6915 | 51.2% to 71.3% |
| fixed_elo | 97 | 15 | 0.4689 | 0.6616 | 59.8% | 0.4257 to 0.5118 | 0.6159 to 0.7072 | 49.6% to 69.9% |

## Same-game comparisons with saved market odds — decisive games only

| Model | Games | Blocks | Brier | Log loss | Accuracy | 95% Brier CI | 95% Log loss CI | 95% Accuracy CI |
|---|---:|---:|---:|---:|---:|---|---|---|
| model | 97 | 15 | 0.4830 | 0.6761 | 60.8% | 0.4673 to 0.4984 | 0.6602 to 0.6915 | 51.2% to 71.3% |
| fixed_elo | 97 | 15 | 0.4689 | 0.6616 | 59.8% | 0.4257 to 0.5118 | 0.6159 to 0.7072 | 49.6% to 69.9% |
| market | 97 | 15 | 0.4640 | 0.6558 | 56.7% | 0.4346 to 0.4924 | 0.6251 to 0.6856 | 49.1% to 65.1% |

NFL ties are included in three-outcome scores and excluded from all decisive and market-paired metrics. Unpriced games remain in the all-game model evaluation.

## Paired differences

Model minus baseline on the same games. Negative Brier/log loss favors the model; positive accuracy favors the model.

| Baseline | Games | Blocks | Brier difference | 95% CI | Log loss difference | 95% CI | Accuracy difference | 95% CI |
|---|---:|---:|---:|---|---:|---|---:|---|
| fixed_elo | 97 | 15 | 0.0141 | -0.0137 to 0.0419 | 0.0145 | -0.0157 to 0.0446 | 1.0 pp | -2.4 pp to 4.8 pp |
| market | 97 | 15 | 0.0190 | 0.0034 to 0.0349 | 0.0203 | 0.0033 to 0.0371 | 4.1 pp | -2.5 pp to 11.3 pp |

## Forecast probability concentration — same priced decisive games

Home-win spread is descriptive only. Forecasts nearer 50% are not inherently better or worse; read alongside calibration and Brier.

| Source | Games | Minimum | Maximum | Mean distance from 50% | Share at 40–60% |
|---|---:|---:|---:|---:|---:|
| model | 97 | 39.1% | 61.4% | 3.5% | 97.9% |
| fixed_elo | 97 | 22.7% | 79.3% | 9.8% | 56.7% |
| market | 97 | 28.6% | 76.0% | 8.0% | 70.1% |

## Calibration

Conditional sections compare home-win probabilities on decisive games. NFL full-outcome sections include every settled game and ties.
Fixed five bins; the upper endpoint belongs to the next bin, except 100%. Wilson rate intervals assume independent games and are descriptive only.

| Model / outcome | Probability bin | Games | Mean probability | Observed rate | Wilson 95% observed-rate interval |
|---|---|---:|---:|---:|---|
| model | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| model | 20%–40% | 1 | 39.1% | 0.0% | 0.0% to 79.3% |
| model | 40%–60% | 95 | 51.8% | 62.1% | 52.1% to 71.2% |
| model | 60%–80% | 1 | 61.4% | 100.0% | 20.7% to 100.0% |
| model | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| fixed_elo | 20%–40% | 5 | 32.0% | 20.0% | 3.6% to 62.4% |
| fixed_elo | 40%–60% | 55 | 50.7% | 61.8% | 48.6% to 73.5% |
| fixed_elo | 60%–80% | 37 | 66.4% | 67.6% | 51.5% to 80.4% |
| fixed_elo | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 0%–20% | 0 | Unavailable | Unavailable | Unavailable |
| market (paired only) | 20%–40% | 9 | 35.5% | 33.3% | 12.1% to 64.6% |
| market (paired only) | 40%–60% | 68 | 52.2% | 61.8% | 49.9% to 72.4% |
| market (paired only) | 60%–80% | 20 | 65.8% | 75.0% | 53.1% to 88.8% |
| market (paired only) | 80%–100% | 0 | Unavailable | Unavailable | Unavailable |

## Collection evidence

Latest saved manifest: benchmarks/two_way_prospective/nhl/captures/20261025T223348874991Z/manifest.json.
Manifest completion field: True. Errors: []. Exclusions: [{"game_id": "2026020182", "reason": "Official/ESPN venue disagreement"}].
Optional availability errors: [].
Newer saved collection failure: null.
Manifest completion alone does not imply absence of per-game errors.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
