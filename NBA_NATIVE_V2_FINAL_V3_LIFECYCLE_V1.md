# Native-v2 frozen features and v3 postgame sources

`python sports_nba_native_v2_final_v3_cohort.py` independently replays the newer
native-v2 frozen feature protocol and compares those records with the latest
retained v3 NBA final page and independently retained ESPN capture. It writes no
features, forecasts, settlements or outcomes.

The existing `sports_nba_v3_feature_cohort.py` deliberately retains its original
v1 feature reader. Its counts must not be used as the denominator for native-v2
features. The new report pins `NATIVE_DAILY_V2_ONLY`, the v2 protocol SHA-256 and
record root, and the v3 postgame receipt schema. Legacy outputs remain unchanged.

At the October 24 retained snapshot, using native capture
`20261024T163520206576Z` and provider capture `20261024T163445111625Z`:

| Separate feature cohort | Frozen records | Matching postgame research observations | Outcomes enrolled |
| --- | ---: | ---: | ---: |
| Original v1 features, existing v3 audit | 16 | 0 | 0 |
| Native-v2 features, new audit | 29 | 12 | 0 |

The other 17 native-v2 records are outside that page's requested Eastern date,
October 23. They remain pending; this does not imply cancellation or loss.
The report covers one recent date, not every frozen game's complete lifecycle.
Counts from the two feature protocols must not be pooled.

Source comparison preserves exact frozen starts, team/provider identities,
original-byte digests, actual-end/source-observation ordering and conflict
quarantine. Corrupt native-v2 records fail before final comparison; missing
native-v3 receipts never fall back to older feature or postgame protocols.

The scheduled college/NBA workflow uploads the new report separately and records
separate `native_v2_features_v3_*` status fields. The original `nba_v3_*` fields
retain their older-cohort meaning. The integrated offline workflow also replays
and retains the new report, requiring unchanged tracked evidence.

These are frozen feature observations, not enrolled model predictions.
Independent official-final certification, publication attestation, complete
schedule coverage, training, prediction grading, promotion and wagering remain
disabled. `NO_BET=true`, actual wagers zero, outcomes enrolled zero.
