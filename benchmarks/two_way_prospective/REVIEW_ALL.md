# Prospective benchmark reviews

**NO BET — actual wagers $0.**

| Sport | Settled | Recorded | Pending | Market-paired | 100-game review | Report |
|---|---:|---:|---:|---:|---|---|
| NFL | 39 | 41 | 2 | 38 | collecting | [Review](../nfl_prospective_v2/REVIEW.md) |
| NHL | 98 | 102 | 4 | 98 | collecting | [Review](nhl/REVIEW.md) |
| MLB | 9 | 13 | 4 | 6 | collecting | [Review](mlb/REVIEW.md) |

## First-100-enrolled checkpoints

| Sport | Status | Selected | Settled in window | Pending in window |
|---|---|---:|---:|---:|
| NFL | collecting_forecasts | 41 | 39 | 2 |
| NHL | awaiting_selected_results | 100 | 98 | 2 |
| MLB | collecting_forecasts | 13 | 9 | 4 |

The fixed checkpoint waits for the first 100 enrolled forecasts to settle, even if later games finish sooner. Its saved inputs and report are checked on later runs and never silently replaced. [Checkpoint method](CHECKPOINT_METHOD.md). No automatic promotion or wagers.

[Forecast and odds coverage audit](COVERAGE_ALL.md)

Each sport is a separate prospective cohort. Counts are games, not the number of model scores. These cohorts are not pooled or described as unique games across cohorts.

Experimental descriptive results. NFL uncertainty uses season/week blocks; NHL/MLB use Eastern game-date blocks. Blocks can still be dependent. Intervals require at least five blocks and are unavailable below that; five blocks or 100 settled games does not establish a betting edge. Repeated monitoring intervals are not sequential significance tests. No model promotion, forecast changes, wagers, or profits are inferred.
