# Current MLB archive content inventory

`sports_mlb_legacy_source_inventory.py` compares verified current archives with
normalized response digests in an explicitly selected set of sealed hitter
records. It reads files only. Selection requires exact original file SHA256s;
the CLI can extract that selection from the existing publication report without
reusing the report as fresh proof of server observation.

```
python sports_mlb_legacy_source_inventory.py --cohort-report benchmarks/mlb_cohort_publication_v1/first_three_games.json
```

The October 19 snapshot selects the original 19 hitter records and verifies all
18 currently retained source archives. Of 76 original receipt references,
36 have current canonical-JSON matches: 12 active-roster references and 24
hitter-history references. Seven roster references, 14 history references and
all 19 pregame game-feed references have no current match. Repeated receipt
references are counted separately; these are not 36 distinct responses.

A canonical match means that a current archive parses to JSON with the same
normalization digest. Differently formatted original response bytes can share
that digest. The inventory lists every matching candidate instead of choosing
one as the original. It does not attest the candidate's source URL, original
wire bytes, upstream publication time, or availability at the original freeze.
It does not infer lineup confirmation or replay missing pregame game bodies.

Receipts that explicitly declare an original archive continue through the
existing strict replay reader. Corrupt, oversized, unexpected or symlinked
archives fail the entire inventory, including files with no receipt match.
Changed original records fail their selected file digest and original seal
checks. The report is a current inventory snapshot; future source additions can
change its matches. Recompute it rather than treating it as an immutable source
availability certificate.

The saved snapshot is
`benchmarks/mlb_legacy_source_inventory_v1/first_cohort.json`. Original forecasts,
receipt fields, schedules and publication reports are unchanged. Issue #98 and
the source-completeness gap remain open. No forecasts, accuracy measures,
training, model promotion or wagers are produced. NO_BET remains true.
