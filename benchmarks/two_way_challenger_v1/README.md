# NHL/MLB challenger development comparison

**NO BET / actual wagers $0. No model promotion.**

Fit only on 2024-season regular games; evaluate on 2025-season regular games with delayed rolling Elo. No 2026-season replay input or live fitted weights are read. Candidate family was fixed before this run, after inspecting the 2026 replay; this is not preregistered or blind.

| Sport | Candidate | Training games | Validation games | Brier | Log loss | Accuracy |
|---|---|---:|---:|---:|---:|---:|
| NHL | fixed_elo | 1312 | 1312 | 0.504164 | 0.698364 | 53.8% |
| NHL | ridge_recipe | 1312 | 1312 | 0.497704 | 0.690946 | 54.7% |
| NHL | elo_prior_calibration | 1312 | 1312 | 0.499497 | 0.692987 | 53.8% |
| MLB | fixed_elo | 2422 | 2421 | 0.487608 | 0.680420 | 55.6% |
| MLB | ridge_recipe | 2422 | 2421 | 0.488729 | 0.681754 | 56.1% |
| MLB | elo_prior_calibration | 2422 | 2421 | 0.487997 | 0.680840 | 55.4% |

Brier (two-outcome sum) and log loss: lower is better. The existing ridge recipe is re-fitted on 2024 here; these scores do not evaluate the live 2025-fitted model.

## Paired log-loss differences versus fixed Elo

Same validation games, Eastern-date block bootstrap; negative favors the candidate. Intervals are descriptive and unadjusted for candidate selection.

| Sport | Candidate | Mean difference | 95% interval |
|---|---|---:|---|
| NHL | ridge_recipe | -0.007418 | -0.012959 to -0.001994 |
| NHL | elo_prior_calibration | -0.005377 | -0.008314 to -0.002501 |
| MLB | ridge_recipe | 0.001335 | -0.001828 to 0.004639 |
| MLB | elo_prior_calibration | 0.000421 | -0.000753 to 0.001550 |

## Development selection and scope

Selection minimizes 2025 mean log loss across the three fixed candidates, with listed order breaking exact ties. This selects on validation and does not create a new independent test. No refitting on 2025, future enrollment, deployment, or changes to live assets occur.

- NHL: selected `ridge_recipe`; fit 2024-10-04T17:00:00+00:00 through 2025-04-18T01:30:00+00:00; validate 2025-10-07T21:00:00+00:00 through 2026-04-17T02:00:00+00:00; 0 ambiguous regular-season resumptions excluded across both seasons.
- MLB: selected `fixed_elo`; fit 2024-03-20T10:05:00+00:00 through 2024-09-30T17:15:00+00:00; validate 2025-03-18T10:10:00+00:00 through 2025-09-28T19:20:00+00:00; 7 ambiguous regular-season resumptions excluded across both seasons.

## Methods and reproduction

`fixed_elo` retains the frozen league K, home offset, and offseason regression. `ridge_recipe` uses the existing intercept + rating-difference/200 logistic fit, L2=0.01 with slope prior zero. `elo_prior_calibration` fits intercept + fixed-Elo logit with the same penalty, shrinking the slope toward one; the intercept is unpenalized. No hyperparameter grid or probability clipping is selected. Equal initial ratings of 1500 mean early 2024 has no earlier-season warmup. All finals, including playoffs and ambiguous resumptions, may update Elo only after their retained start plus 12 hours; ambiguous resumptions are never fitting/scoring examples.

Run `python sports_two_way_challenger.py --output /tmp/two-way-challenger`. [protocol.json](protocol.json) pins all historical inputs and rules. JSON reports retain fitted parameters, calibration bins, paired Brier/log-loss/accuracy estimates and per-game score hashes; compressed score files retain reconstructed probabilities and features. The command is offline and never writes to live model, forecast, or result paths.

- Years denote league season labels, not calendar-year boundaries: NHL validation runs October 2025 through April 2026.
- 2024 starts with equal 1500 ratings: no earlier warmup archive is used.
- 2025 was already training data for the live baseline; this is not independent validation of that baseline.
- Earlier validation results may update Elo after the frozen delay; validation outcomes never fit calibration parameters.
- Historical schedules/results may have been revised and do not prove original publication times.
- Selection on these validation scores has selection bias; paired intervals are descriptive and unadjusted.
- Selected parameters are a development artifact trained on 2024 only, not a deployed or prospective model.
- No market-price, lineup, injury, profitability or betting-edge evaluation. Any future model needs separate freezing and prospective enrollment.
