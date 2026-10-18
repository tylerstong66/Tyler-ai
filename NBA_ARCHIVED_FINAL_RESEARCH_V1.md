# NBA archived final research replay

`sports_nba_final_receipts.py` replays the latest explicit saved NBA-controlled
schedule receipt and its SHA-linked ESPN archive. Final agreement requires a
unique, one-to-one official game mapping, regular/playoff stage agreement,
NBA game-ID season agreement, known non-postponed status, two valid equal
non-tied scores, and both source observations later than both saved starts.
Changed score or identity is never resolved by selecting a preferred source.

Official endpoint, manifest timestamps, capture directory identity, closed NBA
archive file set, raw response digests and linked ESPN capture audit are checked.
The later retrieval time denotes corroboration availability, not the actual
final horn or historical pregame information. Output retains exact official and
ESPN IDs, team identities, scores and source manifest/response hashes.

No NBA-owned captures are present in the current repository. Source collection
run 39148942458 hit HTTP 403 at the official NBA CDN. The script emits explicit
`NO_ARCHIVED_INDEPENDENT_NBA_SOURCE`, false archive verification and 0 final
agreements in that state. Successful software execution cannot imply the
independent source was acquired. Network source collection is not weakened.

Both CI and scheduled research collection attach a 30-day replay/status artifact.
If a future retained archive is corrupt, replay fails instead of reporting it
as simply unavailable. No source bytes are rewritten; no forecasts, model
training/evaluation, promotions, production deployment or actual wagers occur.

Local combined NCAA/NBA source suite: 107 tests passed on October 18, 2026.
NBA-specific 15 tests passed including synthetic archived finals and edge cases;
these fixtures demonstrate software behavior, not live result verification.
