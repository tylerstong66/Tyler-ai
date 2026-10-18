# Archived college final research receipts

`sports_college_final_receipts.py --capture <crosswalk capture timestamp>`
replays one explicit NCAA/ESPN identity receipt and its original linked source
manifests and compressed response bytes. It derives research-only agreeing
final scores after strict identity reconciliation. Original captures are never
rewritten. Existing derived output must reproduce byte-for-byte on repeat.

Both source capture timestamps must follow both saved scheduled starts; the
later source capture is corroboration availability, not the actual game end.
A source recorded after the crosswalk or a folder/timestamp mismatch fails
closed. ESPN endpoint/date/timestamp and archive closure are independently
replayed. NCAA persisted-query identity and exact sport/window URLs are checked.

Every output retains crosswalk/source manifest hashes and response digests.
Pending states, score conflicts, ambiguous identities and finals reported before
kickoff remain excluded. These are postgame observations, never pregame model
features. No attested historical pregame data or full schedule coverage is
established by matching scores. Independently certified official finals,
historical evaluation, training, forecasting and promotion remain disabled.
`NO_BET: true`, `actual_wagers: 0` remain enforced.

The scheduled source workflow publishes a derived capture only after successful
source/identity replay. Failed optional derivation does not publish its output.
The dedicated receipt CI runs parser, receipt, chronology and eligibility tests,
then replays the latest retained real source capture without fetching new data.

Local verification on 2026-10-18: 85 pipeline tests passed. Latest retained
crosswalk `20261018T171012515514Z` yielded 0 postgame final agreements and 4
pending/quarantined games. This is evidence coverage, not predictive accuracy.

## Version 2 receipts and multi-capture dataset

Receipt schema v2 adds exact NCAA school names and ESPN team IDs. It writes to
`college_final_research/captures_v2` and preserves existing v1 receipt bytes.
A strict bijection is required: two ESPN events cannot share one matched NCAA
contest in one capture. `sports_college_result_dataset.py` replays every explicit
saved crosswalk, deduplicates repeat observations and retains earliest source
corroboration availability plus each evidence digest. Changed scores, changed
identity/start fields, conflicting finals, and NCAA ID reuse across captures
quarantine the affected game(s); a newer label never silently replaces an older
one. Results are retained as CI/collection artifacts with a 30-day retention,
while original sources and per-capture derived receipts remain in git.

Aggregate source observations still cannot certify full schedule coverage,
independent publication time, historical pregame feature chronology, or model
quality. Training/evaluation/forecasting/promotion/wagering remain disabled.

Real multi-capture replay on October 18: 18 examined, 17 replayable, 1 explicitly
rejected original crosswalk whose report does not reproduce under current
identity policy; 23 distinct FBS final agreements, 0 quarantined accepted-game
identities, 198 pending capture observations. Pending observations are not
unique games. Incompatible saved reports never contribute labels; malformed
raw bytes or other receipt violations abort the build. No source archives or
legacy reports were rewritten. Later nonfinal regression also quarantines a
previously agreeing label, while genuine earlier pregame observations do not.
