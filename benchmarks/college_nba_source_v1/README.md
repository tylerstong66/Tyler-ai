# NCAA FBS, men's Division I basketball, and NBA — research evidence v1

**Stage: source onboarding only. This is not a predictive model. No bets, model promotions, historical backfill of predictions, or production Render deployment.**

Three separated cohorts are observed:

| Cohort | ESPN provider schedule scope | 2026–27 window |
|---|---|---|
| `NCAAF_FBS` | College football; `groups=80&limit=500` (FBS-associated games, which can include FCS opponents) | Aug 2026–Jan 2027 |
| `NCAAM_D1` | NCAA men's Division I basketball; `groups=50&limit=500` (D1-associated games, not a certified complete NCAA slate) | Begin capturing October 30 for November 2 opener |
| `NBA` | NBA scoreboard; `limit=500`, **not** NCAA grouped | Begin capturing October 17 for October 20 opener |

## Automated research-only collection

`.github/workflows/college_nba_source_observation.yml` runs three times per
day (approximately 05:10, 13:10, and 21:10 UTC; GitHub cron may delay). It
captures up to four provider-scheduled calendar dates (UTC day plus three),
grouped separately by league. Raw ESPN JSON is archived as timestamped gzip
along with each source URL, original-response SHA-256, response timestamp,
normalized game identities, provider season stage, observed state and numeric
scores only when that *provider* claims a completed, decisive result.

A snapshot is built and validated in memory before any files are written.
Two different retained representations for a game (including a reschedule or
different final/status) are explicitly **quarantined** with both original
source-day observations; there is no arbitrary date preference and no
retroactive timestamp rewrite. A returned provider slate at the 500-event
cap, or a claimed greater event count than provided, causes collection failure
rather than an unsupported statement of coverage completeness. Unknown
season type is excluded, **not** assumed regular season. NBA preseason and
college nonregular competitions are excluded.

## Saved-source integrity audit

Before any new observation batch is committed, an independent saved-data
reader (`sports_expansion_audit.py`) re-opens **every** archived ESPN
`.json.gz` response in the repository, verifies its original response
SHA-256, fully re-parses every game, recomputes the date-conflict quarantine
and checks the no-forecast/no-scoring/no-wager guards. It rejects tampered
receipts, missing/untracked files, mismatched dates, changed identifiers,
overwritten result labels and malformed capture names. It then publishes
`COVERAGE.latest.json` with verified capture counts, provider game
observations and **provider-reported but not independently official** finals.
The scheduled workflow commits only if both the new capture and this
entire archive replay pass.

This audit independently reproduces *archived ESPN evidence*, but is **not**
an independent NCAA/NBA governing-body verification. Training and grading
remain disabled until a separate original-source validator and a season-aware
time-split benchmark pass.

ESPN is a **media data provider, not the independent official NCAA/NBA final
authority**. A provider-reported final is source evidence only. Prior to
launching any scores, separate official-result cross-checks and saved source
identity/time validation must be completed for each league, including
postponements, NCAA neutral-site and multi-overtime games, NBA Cup
nonregular/exhibition events, and college team membership. Historical
training must use only information published before each forecast and be
season/time-split; no other sport's coefficients may be inherited.

The collector intentionally has
`forecasting_enabled=false`, `official_final_scoring_enabled=false`,
`model_training_enabled=false`, `promotion_allowed=false`,
`NO_BET=true`, and `actual_wagers=0`. The next development phase
requires historical-team coverage, separate independently validated baselines,
freeze-before-kickoff evidence, official outcome verification and leakage tests
before enabling prospective paper model comparisons.

No actual wagers or sportsbook account/API access are used.
