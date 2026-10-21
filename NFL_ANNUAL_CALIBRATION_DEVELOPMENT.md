# Annual chronological NFL recalibration development

The retained fixed-fit calibration experiment improved classification accuracy
but worsened Brier and log loss, so it was not adopted. Its base parameters were
fit only through 2018 and its calibrator only through 2021. This separate fixed
recipe tests annual updates without fitting any parameters on the year being
scored. The recipe and tests are committed before executing its real-data run.

| Evaluation season | Base fitting seasons | Calibration fitting seasons |
|---|---|---|
| 2022 | 2014–2018 | 2019–2021 |
| 2023 | 2014–2019 | 2020–2022 |
| 2024 | 2014–2020 | 2021–2023 |

Both penalties remain fixed at 0.01, with no grid or outcome-driven selection.
Each conditional logit calibrator uses only decisive games in its preceding
three seasons. The annual base-training-only smoothed tie prior is preserved
in calibrated and uncalibrated forecasts; ties remain in full three-outcome
scoring. Compare annual calibrated versus the same annual uncalibrated base,
using the same evaluation games and season/week blocks. Each fit is hashed
before evaluation and must remain unchanged. Report aggregate proper losses,
paired differences, uncertainty and separate yearly reliability diagnostics.

An earlier evaluation year can enter the next year's calibration role only
after it has finished. Synthetic tests change 2024 outcomes and verify no fitted
parameters change in any annual fold; changing 2022 can affect later fits but
cannot affect the 2022 fit. Original feature identities, numeric dimensions,
regular-season scope, chronological boundaries and pinned source hashes remain
validated. Seasons 2025 and live 2026 never enter fitting or evaluation.

Run `python sports_nfl_rolling_calibration.py`. Existing fixed-fit code, retained
results, live models, forecasts and outcomes are unchanged. The read-only NFL
development workflow retains both reports and checks tracked files remain
unchanged. No collector imports this module.

This is retrospective development designed after historical aggregate results
and early prospective results were inspected. Disjoint parameter fitting is
not an untouched confirmatory holdout. Historical source publication delays
remain assumptions; historical market prices are untimestamped references.
Even favorable losses cannot authorize promotion, model selection or wagering.
Any production candidate needs a separate frozen forward protocol and new
prospective games. NO_BET=true, actual wagers zero, promotion disabled.

The first actual run evaluated 815 games (813 decisive) across 54 season/week
blocks. Annual calibration worsened decisive Brier from 0.4487592 to 0.4516064
and log loss from 0.6398104 to 0.6430794. The paired Brier difference was
+0.0028472 (descriptive 95% interval -0.0017360 to +0.0071023); log-loss
difference +0.0032691 (-0.0022139 to +0.0083523). Classification accuracy rose
only from 63.96% to 64.45%. This provides no adoption support.

The complete retained report is in
`benchmarks/nfl_annual_calibration_development_v1/DEVELOPMENT_RESULT.json`.
Its local replay exactly matched the actual JSON emitted by successful GitHub
run 39594197538, job 119202341722, for recipe commit
`07dcbd2b4392b54c15079d4812b9ca6aa1f18427`. Tests and dedicated CI require
semantic equality with that full result. The fixed recipe remains unchanged
after this negative result; neither earlier experiment nor prospective ledger
is rewritten.
