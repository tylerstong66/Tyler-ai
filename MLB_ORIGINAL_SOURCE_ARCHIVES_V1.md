# Original MLB hitter source retention

The default research batch reader now retains original StatsAPI response bytes
under `benchmarks/mlb_hitter_props_shadow_v1/source_archives/`, keyed by the
original body SHA256 and compressed with reproducible gzip metadata. Existing
normalized-JSON `response_sha256` receipts retain their original meaning. New
receipts additionally identify the raw-body digest and archive filename.

`verify` checks both the original response digest and the existing normalized
JSON digest. It rejects wrong origins, missing/legacy archives, corrupt gzip,
oversized expansion, invalid paths, symlinks and unexpected directory entries.
The batch audits existing archives before fetching. Identical raw bodies reuse
an existing file; original files and forecasts are never overwritten.

Publication occurs in two separate guarded commits. A dedicated source-only
addition guard verifies staged Git index bytes, regular-file mode, digest
filename and JSON payload before publishing source archives. The unchanged
forecast-only pregame guard then verifies new sealed forecasts and original
first-pitch timing before their separate publication. Source archiving does
not relax that prediction guard or authorize late publication.

This closes the response-retention gap for future MLB hitter captures. It does
not recreate missing old response bodies, independently attest publication
times, certify issue #98's older cross-cohort comparison, combine cohort scores,
rewrite start times or change frozen probability calculations. Existing digest-
only records remain explicitly unavailable for original-body replay.

All 455 offline sports tests passed; tests include original UTF-8 bytes,
idempotence, changed bodies, legacy absence, normalization mismatch, resource
bounds, path restrictions and invalid staged-index bytes. The app reader's
archive option is off by default; only the research batch enables it. No new
model, calibrated claim, promotion, production deployment or wager is enabled.
