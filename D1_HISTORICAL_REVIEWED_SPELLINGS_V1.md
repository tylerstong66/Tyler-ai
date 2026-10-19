# Separate reviewed historical D1 source spellings

The opt-in command
`python sports_historical_fbs_crosscheck.py --league NCAAM_D1 --verified-school-aliases --split train`
(or `--split validation`) replays the separate
`tyler-historical-d1-reviewed-identity-crosscheck-v3` report. Default exact-name
replay and the historical FBS policy remain unchanged.

The explicit 127-entry manifest is pinned by SHA256. Its source review packet
and every candidate evidence record are independently rederived from original
receipts and checked against their saved hashes on each use. Entries cannot be
added by fuzzy rules or from newly generated candidates. Only these reviewed
source spellings participate; score agreement never selects an alias.

The source packet supports each name pair with at least two distinct games and
two exact-named opponents in each of the 2024 and 2025 seasons, stable NCAA
slugs/ESPN team IDs, exact UTC tipoffs and home/away orientation. Competing
institutions, insufficient evidence, reused IDs and cross-season game-ID
collisions remain excluded. Both source-content seals must still verify.

This policy reconciles the source spellings. It does not certify an institution,
Division I membership (including visitors), complete schedules, official outcome
grading, historical pregame publication, training or model evaluation. It is
separate from prediction/runtime team aliases and enables no forecasts or wagers.

October 19 replay produces 6,047 training / 5,977 validation final agreements,
versus 2,965 / 2,954 under default exact names. Changed starts, nonfinals,
unmatched identities and conflicting scores remain pending. The original tied
final quarantine remains effective. The reviewed policy exposes one score
disagreement in each split; neither becomes an accepted result.

Use `python sports_historical_college_disputes.py --verified-school-aliases --split train`
(or `--split validation`) to retain both providers' original claims for those
newly recognized disputes. The separate v2 dispute report links the reviewed
manifest digest; default v1 diagnostic output remains unchanged.
