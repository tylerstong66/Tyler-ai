# Historical FBS independent-source crosscheck

`sports_historical_fbs_crosscheck.py` joins original NCAA-owned week receipts
with original ESPN historical daily archives for one explicit train/validation
split. Every source is replayed before joining. Historical game-ID/split/date
quarantines are excluded; changed NCAA records or changed ESPN school identity
also remain excluded.

Historical school matching uses exact normalized school names and the existing
unique 30-minute kickoff / 72-hour ambiguity gates. It explicitly disables the
school-alias mapping reviewed only for 2026. No result, score, preferred winner
or model confidence chooses an identity. One NCAA contest cannot serve multiple
ESPN event IDs. Both sources must report the same valid final, and both source
observation times must follow both saved scheduled starts.

Every agreeing result retains both game IDs, exact source receipt/response
SHA256 digests and the later corroboration-availability timestamp. These are
postgame labels acquired in 2026; they are never pregame feature observations or
historical published forecasts. Matching source reports do not certify complete
schedule coverage, historical feature chronology, profitability or model skill.

Initial retained-data replay at base `5b30d0e`: 248 NCAA IDs, 965 ESPN training
IDs, 118 final agreements, 847 unmatched/pending provider identities. This is a
conservative subset, not 847 incorrect results. Missing historical name aliases
and not-yet-acquired NCAA weeks remain unresolved. All 449 offline sports tests
passed. Existing 2026 receipt policy remains the default and is unchanged.

CI and the historical collector retain the crosscheck as a 30-day artifact.
Training, evaluation, forecasts, promotion, production deployment and wagers
remain disabled; NO_BET is true and actual_wagers is zero.

Fresh replay after PR #131's post-merge acquisition: 426 NCAA training contest
IDs, 965 ESPN training IDs, 208 agreeing finals and 757 pending/unmatched IDs.
The broader identity audit verified 570 daily receipts and 10,787 provider IDs
with no detected quarantines. Validation source collection had begun (39 FBS
and 34 D1 dates); no model was fitted, tuned or evaluated on those observations.
