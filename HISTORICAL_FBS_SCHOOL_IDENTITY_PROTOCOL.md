# Source-backed historical FBS school spelling policy

The default v1 historical reader continues using exact normalized school names,
with no 2026 alias dictionary. `--verified-school-aliases` separately opts into
v2 identity metadata frozen in `school_identity_v1/NCAAF_FBS.json`.

The 83 entries explicitly associate institutional names, such as `Penn St.` /
`Penn State`, `Miami (FL)` / `Miami`, and `Southern California` / `USC`. Each
entry cites an actual 2024 and 2025 NCAA original contest and ESPN original
event, including school spelling, NCAA school slug, ESPN team ID, side,
receipt digest and raw-response digest. These references attest that the
reviewed spellings occur in both historical source splits. The institutional
name equivalence is an explicit review decision; references alone do not prove
semantic equivalence. Scores, winners and forecasts do not select identities.

The loader pins the reviewed manifest digest, replays every cited original
source receipt, verifies referenced schools/team IDs against original bytes,
requires stable NCAA slugs and ESPN IDs across seasons, and rejects ambiguous
or duplicate mappings. Penn / Pennsylvania and Saint Francis / St. Francis
(PA) were omitted because both source-season spellings were not available.
No runtime abbreviation expansion, edit distance, mascot stripping or inferred
school aliases are used. No D1 men's alias policy is enabled.

A game still needs both school names, a unique NCAA contest within 30 minutes,
no competing identity within 72 hours, a bijective provider/official ID join,
matching valid finals, original receipt digests and postgame chronology.
Unknown names and kickoff drift remain pending. The v2 report cites its exact
identity-manifest digest; original source files and v1 receipts are unchanged.

Reproduced from retained 2024/2025 sources on 2026-10-18:

| Source split | Exact v1 agreements | Reviewed v2 agreements | v2 pending |
| --- | ---: | ---: | ---: |
| Training source season | 468 | 951 | 14 |
| Validation source season | 450 | 925 | 33 |

All v1 agreements remain in v2. Training pending includes 10 kickoff drifts
and four unmatched identities. Validation pending includes 16 kickoff drifts
and 17 unmatched identities. Pending cases are not score-error findings.

These October 2026 source observations do not attest pregame knowledge in
2024/2025. No model training, evaluation, prediction, official-final grading,
wagering or promotion is enabled. `NO_BET: true`, `actual_wagers: 0`.

```
python -m unittest -v test_sports_historical_school_identities
python sports_historical_fbs_crosscheck.py --verified-school-aliases --split train
python sports_historical_fbs_crosscheck.py --verified-school-aliases --split validation
```
