# Separate FBS and D1 source-backed feature diagnostics

Run `python sports_historical_college_features.py --league NCAAF_FBS --split train`
or select `NCAAM_D1` and/or `validation`. Each invocation verifies both source
content seals, the sport's reviewed spelling manifest, original NCAA/ESPN
receipts, and their agreeing final-result subset. The feature adapter rechecks
receipt/response hashes against the crosscheck before reading original team IDs
or source starts. No model is fitted or evaluated.

The sport-specific fixed windows are four prior corroborated games for FBS and
eight for D1. They describe mean points scored, allowed and margin, plus days
between the target start and latest eligible prior start. These are plain team
form summaries, without learned coefficients, odds or probability estimates.
Each sport and source-season split has its own fresh state.

Two separate views use the same cutoff, one second before the earlier source
scheduled start. `observed_receipt_time` accepts a result only once both original
sources were observed. `reconstructed_24h` assumes availability 24 hours after
the later source start, and **does not attest historical publication time**.
The current target, future games and not-yet-available results cannot enter its
features. Late receipts are ordered by underlying event time when selecting the
most recent eligible window. No missing average or days-between-starts value is
filled with zero. Days between starts are not measured rest after completion.

Source-game indexes and SHA256 links retain the exact source agreement, NCAA
and ESPN claim digests, original team IDs, target and prior game identities,
receipt references and availability times. Each output also binds its protocol,
crosscheck report and reviewed institutional-spelling manifest.

| Scope | Corroborated targets | Both-team reconstructed history | Both-team observed-receipt history |
|---|---:|---:|---:|
| FBS training | 951 | 813 | 0 |
| FBS validation | 925 | 782 | 0 |
| D1 training | 6,047 | 5,657 | 0 |
| D1 validation | 5,977 | 5,550 | 0 |

These October 19 counts describe only the corroborated subset. Missing results,
conflicting scores, nonfinals, changed starts and identity ambiguity remain
excluded. The subset is not a certified full schedule or institutional membership
list. Visiting schools may be outside the named division. Retrospective source
captures do not become original pregame feature records or paper forecasts.
All training/evaluation, forecast, promotion, runtime activation and wager gates
remain disabled. CI retains four separately scoped diagnostics for 30 days.
