# NFL recalibration development result

The one fixed chronological experiment completed in GitHub workflow 39468799797 (job 118787105270). The retained JSON records its semantic report, parsed from job stdout. CI reconstructs the pinned retrospective inputs and requires exact semantic equality; source files and incumbent models remain unchanged.

Fit: 1,280 games from 2014–2018. Calibration: 784 games from 2019–2021, 781 decisive. Evaluation: 815 games from 2022–2024, 813 decisive across 54 season/week blocks. Neither 2025 nor prospective 2026 is used.

| Decisive evaluation | Uncalibrated | Calibrated |
|---|---:|---:|
| Accuracy | 62.48% | 65.81% |
| Two-way Brier (0–2) | 0.449518 | 0.450904 |
| Conditional log loss | 0.640491 | 0.642486 |

Accuracy increased while both proper probability losses worsened slightly. The paired Brier difference is +0.001386, with a descriptive block-bootstrap 95% interval from -0.005823 to +0.008426. The paired log-loss difference is +0.001995, with interval -0.005992 to +0.009652. No adoption or demonstrated improvement is supported. Same-game untimestamped historical market Brier was 0.419788; it is an evaluation reference, not executable betting evidence.

The design followed prior historical/early prospective inspection, so these disjoint parameter-fitting roles are still retrospective development, not a fresh confirmatory holdout. This negative result is preserved without retuning the recipe against evaluation outcomes. Any future candidate needs its own protocol and new prospective evidence. NO_BET=true; actual wagers zero; promotion disabled.
