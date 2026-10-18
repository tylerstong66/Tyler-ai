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
