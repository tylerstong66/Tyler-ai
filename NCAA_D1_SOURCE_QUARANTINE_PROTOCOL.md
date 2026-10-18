# Malformed NCAA D1 reported finals remain quarantined

The original strict NCAA parser continues rejecting tied reported finals. It
now raises a dedicated `TiedNcaaFinalError` (a `ValueError` subclass), allowing
historical D1 acquisition to distinguish this exact source defect from other
schema, identity, chronology or transport failures.

A v2 daily source receipt retains the entire original response and SHA-256,
its normal valid contests, and an explicit per-contest quarantine for a tied
reported final. The rejected contest keeps its original source state, scores,
school names, kickoff and canonical contest digest. It never enters the list
of normalized valid results. Identity and day/season checks still apply to the
quarantined contest; duplicate IDs or any other malformed sibling fail the
whole batch. Existing valid v1 receipts remain unchanged and replay strictly.

Replay recomputes the quarantine directly from the original bytes. Removing,
editing or promoting a quarantined row fails verification. The dataset reader
excludes a quarantined NCAA ID across every retained source day, even if a
different observation reports a valid score for that same ID. Reports expose
quarantine IDs and their exact source references. Original 0-0 values are
never replaced with another provider's scores.

## Observed source anomaly

The retained March 11, 2025 NCAA response reports contest 6442390,
UTEP vs Sam Houston, as `F` at 0-0. The original ESPN response for event
401744545 reports 79-65; both saved scheduled starts are 2025-03-11 22:30 UTC.
That disagreement remains unverified. The original NCAA response contains
23 other structurally valid contests; retaining those observations does not
certify their scores until the separate independent-source replay succeeds.

This source day uses `tyler-ncaa-owned-d1-history-day-v2`; original bytes and
its quarantine are reviewable together under the historical NCAA-owned D1
training source directory. Acquisition can move to later missing dates while
preserving the anomaly. Source retention coverage is not official schedule
completeness or a count of eligible result labels.

All research restrictions remain: no model training, historical evaluation,
forecasts, grading, promotion, deployment or wagers. `NO_BET: true` and
`actual_wagers: 0`.

```
python -m unittest -v test_sports_ncaa_d1_source_quarantine test_sports_historical_d1_crosscheck
python sports_historical_fbs_crosscheck.py --league NCAAM_D1 --split train
python sports_historical_fbs_crosscheck.py --league NCAAM_D1 --split validation
```
