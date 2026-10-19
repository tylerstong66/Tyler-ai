# NBA pregame reference feature observations v1

**Features only: no predictions, odds, fitted model, evaluation, activation or wagers.**

The digest-pinned `protocol.json` specifies the 2026–27 regular-season target
cohort and the last ten corroborated 2025–26 source results per team. These are
previous-season reference summaries, distinct from the same-season historical
diagnostic recipe. They do not model roster, coach or injury changes and must
not be fed silently into a differently defined trained model.

Run `python sports_nba_pregame_features.py` to verify every existing observation
before preparing a new batch. Run `--audit-only` to replay saved records without
creating anything. The existing source-observation workflow collects after a
successful NBA source step and publishes feature files only if collection
succeeds. It never stages a failed feature batch.

Each target must have a unique independently replayed NBA/ESPN schedule match,
both providers still pending/pregame, a regular-season identity and nonpostponed
status. Both saved starts must be after the actual collection freeze. Both
schedule captures must precede the freeze and be at most twelve hours old then.
The full original current NBA response and the linked provider bytes are replayed;
unassigned Cup slots cannot become targets.

Both historical source-content seals and the fixed prior-season crosscheck
verify before any reference feature is used. Each team's ten retained reference
results must have been observed in both sources by the freeze. Their original
agreement rows, hashes and source receipts accompany mean points scored,
allowed, margin and days since the latest prior start. Missing, late or duplicate
reference results cannot be replaced with fabricated inputs.

Files under `records/` are created exclusively once per NBA game ID. Existing
observations are checked against their original capture, feature freeze,
reference-report digest, protocol and derived values. Rehashed tampering still
fails source replay. A later source capture, start change or postgame audit never
rewrites an original file. Current/future target outcomes are never consumed.

The first October 19 batch froze 16 observations before their saved October
20–22 Eastern-date starts, with ten source-backed prior results for each team. A repeated
collection verified all sixteen and created no replacements. These are original
feature observations, **not sixteen forecasts**. The stored freeze is an
application record, not independent GitHub publication-time attestation or a
database-enforced immutable ledger. Full schedule and membership certification,
model training, prediction generation, promotion and wagers remain disabled.
