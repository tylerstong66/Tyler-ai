# Read-only frozen NBA feature lifecycle under recent native sources

The v2 lifecycle view replays all original feature records, original schedule
dependencies and historical seals. It also exactly replays the recent native
postgame receipt and independently audits the latest retained ESPN responses.
Original features, starts and source receipts are never rewritten.

The comparison reuses the conservative frozen-identity lifecycle checks:
same NBA/ESPN IDs, both teams and orientation, ESPN team IDs, regular-season
scope, unique current identity, agreeing final scores, and observations after
the freeze and both original/current saved starts. The native version also
requires exact current UTC tipoff agreement and both source observations at
or after the NBA source-reported actual end. Current schedule drift remains
visible against the original saved starts.

The source covers one requested recent Eastern date. Records outside that
date are identified explicitly; missing games never imply cancellation or
a replacement identity. A rescheduled game actually present on the requested
page can still be inspected under all original/current chronology checks.
An empty, unsupported or absent native page provides no final evidence.
The newest native page is used as-is, with no silent fallback to an older
successful page.

The report retains original record hashes, native original-body and manifest
hashes, independent provider manifest hash, actual observation clocks,
source ages and page status. Results are corroborated source observations
associated with feature records, not graded predictions or an outcome ledger.
No accuracy, betting return, feature backfill, training or promotion is enabled.
Independent source-origin/clock and publication attestations remain separate.

The existing source workflow uploads this read-only report and records its
audit outcome separately. Offline integrated CI also replays the actual
retained native receipts and view and requires unchanged tracked inputs.

NO_BET=true; actual wagers zero.
