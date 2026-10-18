# Tyler AI continuation — October 18, 2026

Published research milestones in this Work session:

- PR #125: archived NCAA/ESPN final receipts with postgame observation chronology.
- PR #126: unique cross-capture result observations, score/identity drift quarantine and v2 receipt preservation.
- PR #127: NBA-specific final receipt replay, explicitly unavailable with no official NBA archive.
- PR #128: linked-capture replay optimization and D1 end-to-end regressions.

Each merged PR's checks and post-merge workflows were independently verified successful. Optional NBA acquisition still returned HTTP 403; successful overall collection is not evidence of successful NBA-source acquisition.

PR #129 combines bounded historical gzip replay/safety guards with 60 newly retrieved provider-only dates (20 per league), original compressed responses and digest-linked daily receipts. All 390 retained historical daily receipts were reverified locally. Coverage advances to NBA 130/490, FBS 130/302 and D1 men 130/312 declared dates. Daily retrieval is not proof of complete official event schedules. No historical record is a pregame forecast.

Validation: all 435 offline sports tests passed; 23 unique raw-replayed FBS final agreements remain research-only, with one older crosswalk explicitly excluded as nonreproducible under the current identity policy. No final label was inferred for current NBA or D1 data. The aggregate receipt artifact was downloaded from run 39149408808 and verified as 23 games / zero wagers.

Next high-value work: finish closed-season historical acquisition in bounded batches, audit game IDs and event chronology across train/validation archives, and resolve official NBA source availability before any model evaluation. Keep existing prospective NFL/NHL/MLB cohorts and frozen challenger weights unchanged; follow original first-100 checkpoint protocols. Issue #98 remains a separate MLB cross-cohort schedule-drift integrity question.

Always retain NO_BET=true, actual_wagers=0, no automatic promotion, no production deployment and no unverified training/evaluation authorization. Repository research changes do not imply an updated Render runtime.

## Subsequent verified continuation

PR #129 merged after all 12 head checks passed; all post-merge workflows and
its historical fetch/publication job succeeded. Its automatic collector added
another 60 dates, bringing retained provider coverage to 150 dates per sport.
The new historical game-identity audit replayed all 450 daily receipts and
8,306 provider IDs without detected duplicate, split or date contamination.
Validation source coverage was still zero at that snapshot. Offline sports
suite now passes 440 tests. The audit remains research-only, with all training,
evaluation, forecasting, promotion and wagering disabled.

## Completed raw-source acquisition and additional published engineering

PRs #125–#134 shipped archived NCAA/ESPN final replay, result deduplication,
NBA final replay, bounded linear audits, complete-split acquisition support,
independent NCAA history and exact-name historical final crosschecks. Every
merged head passed its relevant CI; post-merge workflows were verified. All
455 offline sports tests passed after the MLB response-retention addition.

PR #134 preserves original MLB response bodies for future hitter captures with
a separate staged-source guard, then the unchanged forecast-only pregame guard.
Its post-merge collector published four original response archives, all replayed
from a fresh checkout. Older digest-only source gaps and issue #98 remain
explicitly unresolved; no old forecasts or source times were rewritten.

A bounded local acquisition continuation has now completed all 1,104 historical
provider date requests and 42 independent NCAA FBS week requests. Full replay:
17,187 provider IDs, no detected identity/split/date quarantines; strict FBS
final agreement 468 training / 450 validation. See
`HISTORICAL_SOURCE_COMPLETION_2026_10_18.md` and the sealed completion JSON.
Do not confuse complete request-date retention with certified event coverage,
accepted pregame features, model evaluation or an established betting edge.

## NBA-owned historical source access and replay

Closed-season NBA Stats public access succeeded using the published nba_api
1.11.4 request profile, while the old CDN endpoint remained unavailable.
Original 2024-25 and 2025-26 responses are retained separately with pinned
league/season identity, exact raw digests and observation chronology. Full
original-source crosschecks yield 1,185 and 1,203 strict agreeing NBA/ESPN
research finals respectively. Pending identities remain excluded, including
four 2026 All-Star team-code games. Existing ambiguity safeguards and all
model/wagering restrictions remain in effect. See
`NBA_HISTORICAL_OWNED_SOURCE_PROTOCOL.md` for scope, counts and replay commands.
