# Publication of declared MLB source archives

The six existing hitter records for game 849815 were frozen by the existing
collector at 2026-10-19T20:00:51–20:00:57Z. They explicitly declare retained
original response archives, unlike the original 19 digest-only records. This
reader creates no forecasts and does not change either cohort.

The first report verifies six exact sealed JSON records and 15 distinct exact
compressed source archives: 21 immutable blobs. Every record's four source
receipt references replay through the existing original-archive and sealed
record checks. The archives' decompressed response SHA256 and canonical JSON
SHA256 must match their declared receipts.

GitHub created run 39325179589 at 2026-10-19T21:08:55Z, naming immutable commit
d07e0a8ce2b281715bba61f0feef62032a9e8230. That server observation follows all six
freezes and precedes each saved 2026-10-20T00:08:00Z start. The selected college/NBA
source workflow provides the server clock and commit binding only; its execution
is not an MLB audit. The separate reader checks every selected MLB blob.

```
python sports_mlb_archived_source_publication.py --recipe benchmarks/mlb_archived_source_publication_v1/first_cohort.recipe.json
python sports_mlb_archived_source_publication.py --replay benchmarks/mlb_archived_source_publication_v1/first_cohort.json
```

Replay freshly retrieves the run metadata and each immutable file. The API reader
requires exact regular-file path, size, Git blob SHA and decoded original bytes,
including the compressed archive bytes. It then replays source archives against
their sealed declarations. Archive blobs over 700 KB fail closed to preserve the
shared 1 MB HTTP response budget after base64 encoding. Future unrelated records
cannot silently expand this explicitly selected cohort. A saved report alone
does not certify publication chronology.

The initial live audit and its second replay used fresh GitHub run metadata
plus exact immutable Git objects retrieved over Git HTTPS. A connector cannot
return binary gzip file contents; the Git transport supplies those objects
without reconstructing or normalizing response bodies. The production CLI and
read-only CI use GitHub's native JSON/base64 Contents API for the same exact-byte
checks. CI replays the saved report with a read-only GitHub token.

This proves the presence of the selected declared bytes before saved starts.
It does not independently attest receipt clocks, response origin, public
visibility, actual first pitch, lineup correctness, every model input's semantic
processing, prediction quality or profitability. The original 19 records retain
their missing game-feed bodies and issue #98 stays open. No source receipt,
forecast, outcome, model setting or wagering control is changed. NO_BET is true.
