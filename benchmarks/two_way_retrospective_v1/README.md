# Frozen NHL/MLB retrospective replay

**NO BET / actual wagers $0.**

Fixed 2025-fitted model weights, evaluated on retained 2026-season finals eligible before each October 11 freeze. No fitting or parameter search occurs. Live prospective forecasts and results remain separate.

| Sport | Games | Date blocks | Model Brier | Fixed Elo Brier | Model log loss | Fixed Elo log loss | Model accuracy | Fixed Elo accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NHL | 83 | 12 | 0.484879 | 0.477938 | 0.677902 | 0.670298 | 60.2% | 59.0% |
| MLB | 2451 | 194 | 0.492624 | 0.492324 | 0.685725 | 0.685455 | 55.0% | 55.4% |

Brier and log loss evaluate probability quality; lower is better. Accuracy alone can favor a model with worse probability losses. The observed fitted-model mean losses are higher than fixed Elo in both leagues; these point estimates do not establish a statistically reliable difference.

## Paired differences and descriptive uncertainty

Model minus fixed Elo on the same games. Negative Brier/log loss favors the fitted model.

| Sport | Brier difference (95% interval) | Log-loss difference (95% interval) |
|---|---|---|
| NHL | 0.006942 (-0.030089 to 0.032742) | 0.007604 (-0.031412 to 0.035095) |
| MLB | 0.000301 (-0.002135 to 0.002941) | 0.000270 (-0.002226 to 0.002976) |

## Scope and reproduction

- NHL: 2026-09-29T21:00:00+00:00 through 2026-10-11T02:00:00+00:00 UTC; 0 ambiguous resumptions excluded from scoring. Outcome eligibility is before 2026-10-11T15:58:51.144676+00:00.
- MLB: 2026-03-26T00:05:00+00:00 through 2026-10-11T00:00:00+00:00 UTC; 1 ambiguous resumptions excluded from scoring. Outcome eligibility is before 2026-10-11T15:59:30.281973+00:00.

Inputs are pinned by hashes in [inputs.json](inputs.json). Compressed game snapshots retain the source repository commit and original observed-history hash. Per-game simulated cutoffs, features, probabilities and scores are in the corresponding compressed score files. These are reconstructions, never artifacts recorded before those historical games.

Run `python sports_two_way_replay.py --output /tmp/two-way-replay` from the repository root; compare its files with this directory. The command makes no network requests and does not write to prospective or private ledgers.

Retrospective reconstruction, not a blind holdout or prospective forecast. These outcomes existed before model freezing and this diagnostic was selected afterward. Revised historical snapshots cannot establish original publication times; kickoff plus 12 hours is the frozen availability assumption, not an observed final publication time. No historical market-price comparison, injury/lineup effects, model selection, promotion, wagers or profits are established. Block intervals are descriptive, not sequential tests.
