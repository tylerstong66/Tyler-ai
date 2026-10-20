# NFL chronological recalibration development

This offline experiment investigates probability calibration without fitting on the current prospective cohort. Existing v1/v2 models, forecasts, outcomes and collection remain unchanged.

The fixed recipe uses opponent-adjusted historical features already defined by the efficiency module. Fit the base logistic model on regular-season 2014–2018 games with L2 penalty 0.01. Fit a two-parameter conditional logit calibrator only on 2019–2021 decisive games, also with L2 penalty 0.01. Freeze both parameter sets before evaluating 2022–2024 games. Preserve the training-only tie prior; retain ties in three-outcome evaluation and exclude them from conditional home/away calibration. No grid or candidate selection uses the evaluation role.

Reconstruct features from the pinned schedule and 2010–2024 team-stat bytes. The existing 24-hour result and 48-hour stats delays are assumptions, not proof of historical publication timing. Seasons 2025 and 2026 are excluded. Report full three-outcome scores, decisive conditional scores, identical priced-game comparisons, fixed-bin reliability and paired calibrated-minus-base differences, clustered by season/week.

The design was chosen after historical aggregate results and early prospective outcomes had been inspected. Disjoint fitting and evaluation roles prevent parameter leakage, but do not make this a new confirmatory holdout. Any apparent gain is retrospective development evidence only. Untimestamped historical prices cannot establish executable odds, ROI or value. No automatic selection, live enrollment, forecast rewrite, promotion or wager is enabled.

Run `python -m unittest test_sports_nfl_calibration_development` and `python sports_nfl_calibration_development.py`. The read-only CI workflow preserves the derived report, checks unchanged tracked inputs and never publishes model weights to production. Tests mutate evaluation labels and demonstrate unchanged fitted parameters, exclude 2025/live 2026, preserve tie probability, and reject overlapping fitting roles and changed pinned source bytes.

After inspecting this one fixed development result, a future improvement would need a separately frozen forward-only protocol and new games, with its own activation time and untouched incumbent comparison. Existing early results cannot be relabeled as a fresh test. NO_BET is true, actual wagers are zero, and promotion is disabled.
