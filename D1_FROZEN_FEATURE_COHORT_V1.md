# Frozen D1 feature lifecycle

`sports_d1_feature_cohort.py` reads the original append-only D1 reference-feature
records and source archives. It records pending state, signed schedule drift,
identity quarantine and corroborated final source observations without creating
predictions or computing accuracy.

```
python sports_d1_feature_cohort.py
```

The reader replays the pinned reference protocol, historical source seals and
each original feature's source crosswalk before interpreting later observations.
Latest source clocks cannot be in the future. Source-age flags remain explicit;
passing a saved start is not evidence of actual tipoff or a final result.

Final observations retain both original game IDs, provider team IDs and NCAA
school identities. Both final source observations must follow the feature
freeze, both original saved starts and both reported final starts. Ties, invalid
scores, duplicate result IDs, unreplayed sources and evaluation-authorized rows
fail closed. Source identity changes and dataset quarantines withhold results.
Later absence from the current slate does not cancel a preserved earlier
agreement. None of these observations rewrites the original feature bytes.

FBS and D1 share `sports_college_feature_cohort_core.py` for these checks. The
wrappers pin separate league/protocol scopes and report schemas; a D1 wrapper
cannot use the FBS protocol. FBS retains its exact existing report fields and
kickoff disclaimer, while D1 reports an unattested actual-tipoff flag. A fixed-
clock real-source comparison preserved the full existing five-record FBS report
under canonical JSON after extracting the shared code.

The October 19 D1 replay has zero frozen records, zero pending records and zero
result observations. This is an empty cohort, not evidence of season coverage.
Future D1 records require separate publication chronology evidence. Source
workflow artifacts and step outcomes expose this audit independently from new
feature collection. Default execution is read-only; no model, forecast,
historical evaluation, promotion or wagering behavior is enabled.
