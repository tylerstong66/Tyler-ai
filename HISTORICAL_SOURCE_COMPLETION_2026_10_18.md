# Historical source acquisition completed — October 18, 2026

All declared 2024-training / 2025-validation provider request dates have been
retained and independently replayed from their original compressed responses:

| Cohort | Retained request dates | Source scope |
|---|---:|---|
| NBA | 490 / 490 | ESPN provider observations |
| NCAA FBS | 302 / 302 | ESPN provider observations |
| NCAA Division I men | 312 / 312 | ESPN provider observations |

The full daily archive contains **1,104 verified receipts / 17,187 distinct
provider game IDs**, with **0 repeated game observations and 0 detected
identity, split, date or final-observation chronology quarantines**. This is an
integrity audit of retained data, not proof of a complete official event census.

Independent NCAA-owned FBS acquisition also retained every declared week
request: **21 training and 21 validation receipts**. Original NCAA sources
contain **965 distinct training contests and 958 validation contests**, matching
the respective ESPN cohort counts. Equal counts do not prove identical events.

Under exact normalized university names, unique kickoff matching and original
source replay, the crosscheck derives **468 training / 450 validation agreeing
final scores**. **497 / 508** provider identities remain pending or unmatched;
these are not labeled incorrect results. The 2026-only school-alias mapping is
not reused for these older seasons. No score/model outcome selects an identity.

`benchmarks/college_nba_history_v1/SOURCE_COMPLETION_2026_10_18.json` records
coverage, crosscheck counts, guard states and a SHA256 digest over the sorted
index of all **2,292 original source/receipt files**. The original daily and
weekly files are append-only. A source-only data PR must pass full replay CI;
read-only post-merge receipt checks now trigger on historical data changes too.

No historical observation becomes a previously published pregame forecast.
Official schedule completeness, independent final certification, pregame
feature availability and model eligibility remain uncertified. Training,
evaluation, forecasts, promotion, production deployment and wagers stay off.

Further engineering priorities: resolve historical school identities from
season-specific original evidence; obtain independently replayable NBA and D1
source counterparts; preserve chronological feature and held-out evaluation
rules before any benchmark is accepted. NBA CDN acquisition remains HTTP 403.
Existing NFL/NHL/MLB forecasts and frozen challenger weights are unchanged.
