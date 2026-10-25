# Sports Betting Analyst v1 — verified handoff (2026-10-25)

## October 25 — canonical source identity safeguards

Merged #265 at `e716b4e2f9699cb6224ee5db846ce967aa9b9d02` after all 14 exact-head PR workflows passed. The separate FBS, D1 and NBA ESPN source reader now rejects Unicode/noncanonical game and team IDs and non-ASCII final-score digits; adversarial tests cover all three leagues, failed-batch no-write and rehashed archived replay. This is provider-source integrity only, not independently certified official outcomes. The original source archives and frozen features were not rewritten.

The next independent NCAA-owned reader review addresses the same Unicode ID/score ambiguity and historical kickoff-epoch normalization in FBS and D1. This follow-on change must pass its own exact-head CI before merge; no model-training, outcome-grading or prospective forecast eligibility is inferred. NFL/NHL/MLB research ledgers, NHL first-100 policy, sportsbook-price blocker #217 and MLB drift issue #98 remain separate. NO_BET=true, actual wagers zero, promotion disabled and Render production unchanged.


## October 24 continuation — bounded missing-final retries

PR #261 is merged and the live source workflow published 29 frozen native-v2 records / 14 matching retained research observations / 15 unresolved, with zero quarantines or enrolled outcomes. All 1,058 sports tests and all 15 exact-head checks passed before merge; the post-merge source and integrated replay runs also succeeded.

The next collection gap is recovery after a temporarily unsupported yesterday page. A separate read-only plan now selects only missing-native-final records from two or three Eastern days ago, after verifying their original starts and every retained source. Opt-in collection makes at most two date requests, preserves opaque originals, rejects stale midnight-crossing plans, and leaves score/identity conflicts quarantined. Yesterday's normal receipt remains the latest successful capture. Only explicitly listed and replayed directories can be staged, preventing failed catchup partials from entering publication. The real October 24 plan requested zero older-date retries; the remaining records are October 24/25 games. No future final is inferred. See `NBA_NATIVE_FINAL_CATCHUP_V1.md`.

NO_BET=true, actual wagers zero, outcome enrollment/settlement/training/forecasting/promotion disabled; no Render deployment.

## October 24 continuation — retained-date NBA source history

Post-#260 integrated, live-source and historical-receipt workflows passed. The live source status at 18:40:38 UTC (run 40121485462) correctly publishes 29 newer native-v2 features, 12 matching single-date research observations, 17 pending and zero outcomes enrolled. Read-only Render inspection confirmed automatic deployment disabled and latest live deployment still October 22; no production deploy was initiated.

The 17 single-date pending records comprise two completed October 22 games and fifteen October 24/25 features awaiting their original scheduled starts at the current audit snapshot. Independently replaying retained October 22 sources matches both older games. This branch adds a separate retained-history reader, preserving the single-date outputs: bound both inventories, replay every original v3/native-v2 dependency and provider capture, compare all accepted final claims before selection, then choose earliest consistent native/provider receipts with provider observation after reported end. Earlier source conflicts, source identity quarantine and changed frozen starts cannot be hidden by a later agreeing pair. Contradictory capture/manifest/row digest links remain in the report.

The real offline replay yields 29 frozen features / 14 distinct matching research observations / 15 pending original starts / zero quarantined features, from 30 native and 93 provider receipts. Repeated captures count once per frozen identity. Ten focused tests cover cross-date retention, conflicting earlier scores, provider quarantine, duplicate identities, source clocks, frozen-start drift, empty-league captures, inventory bounds and symlinks. Workflow status execution reproduces the separate 29/14/15 fields and rejects a false wager flag before publication. The initial 1,056-test full suite passed; final regression and CI include the added cross-date test before merge. See NBA_NATIVE_V2_RETAINED_FINALS_V1.md.

This is retained source comparison, not a prediction ledger or independently certified official-final dataset. No original features, forecasts, receipts, model weights or first-100 cohorts are rewritten. Outcome enrollment, settlement, model training, forecasting, grading and promotion remain disabled; NO_BET=true, actual wagers zero, no paid feed or Render change.

## October 24 continuation — newer NBA feature cohort source lifecycle

The existing v3 source audit correctly retains its original v1 feature cohort (16 records), but that is not the newer native-v2 feature denominator (29). A separate version-pinned reader now replays native-v2 feature originals and their own protocol against v3 final sources and independently retained ESPN. It preserves every legacy report and explicitly prohibits pooled cross-version counts. The pinned October 24 16:35:20 NBA / 16:34:45 ESPN observations yield 12 agreeing research observations for native-v2 features, with 17 records outside the requested October 23 daily page still pending; the legacy cohort retains zero for that same source pair. Outcomes enrolled, grading, official-final certification, training, promotion and wagers remain zero/disabled.

The new artifact and separate `native_v2_features_v3_*` workflow fields prevent these newer-cohort observations from being silently omitted or mixed into old `nba_v3_*` counts. Eighteen focused tests verify the actual source pair, distinct reader roots, unchanged original feature bytes, legacy behavior, missing sources and corruption rejection. The full branch suite and saved-source workflow replay pass. YAML and embedded status Python compile; executing the status step reproduces 29/12/17/0 and rejects a forged false wager field before publication. See NBA_NATIVE_V2_FINAL_V3_LIFECYCLE_V1.md for exact scope.

Separately, #259 merged at `c23dc89b7dfbcaf7e3a3d0c435275e54668f9bf8` after all fifteen applicable checks passed and one intentional skip. Both live publication paths succeeded: standalone run 40120588425 and official-final run 40120588395. The published MLB scoreboard at 18:25:06 UTC correctly references that committed input revision and reports 37 frozen player-games / 15 scored / three ineligible / 19 pending, with no market odds or proven edge. The earlier push-race failure remains historical evidence, not a settlement or prediction rewrite. NO_BET=true, actual wagers zero, model promotion disabled and Render unchanged.

## October 24 continuation — merged integrity repairs and concurrent scoreboard publication

Merged #255 (`017e2cd2868225c14096da10e593995071c60c29`), #256 (`1938d7ea75ff261e0f8738076c0467654ad91687`), #257 (`8ac5c25ba9053e841d8a81abab688d42f1cbf095`) and #258 (`5456e384e7bf5418efa7bab394ec34153ea3cf98`) after all 16/19/17/18 applicable checks respectively passed, each with one intentional review skip. These bind NBA provider keys to row IDs, enforce ASCII native-page game IDs, require integer-zero MLB wagers before settlement/batch fetch, and reject ambiguous MLB source JSON during collection and archive replay. Combined local validation passed 1,037 sports tests and the complete saved-source integration replay with unchanged tracked evidence. All 31 retained MLB original response archives replayed under strict JSON.

Post-#258 main checks passed. Post-#257 official-final run 40119588961 passed tests, the fresh source audit and strict settlement with no new final files, then failed only when its derived scoreboard push raced a newer main commit. This branch replaces both scoreboard push paths with bounded publication from isolated worktrees: fetch current committed main, rebuild its ledger snapshot, stage exactly the permitted scoreboard, and retry from fresh inputs after a normal push rejection. Real offline Git tests exercise a competing ledger commit, updated source revision/count, dirty caller preservation, exhausted retries and unexpected staged paths. All 44 focused and 1,042 integrated sports tests pass locally; live post-merge publication still requires verification.

The current committed MLB ledger has 37 frozen player-games, 15 scored, three ineligible and 19 pending across six game IDs; no scores or originals were rewritten. The post-#255 source publication at 18:09:03 UTC retains 29 NBA feature observations, 12 regulation-final source observations and zero qualified outcomes. All twelve newly published ESPN response SHA-256 digests were independently checked from Git objects. Source replay is not official-final certification or a betting edge. NHL's fixed first-100 protocol, rejected NFL calibrators and source-only NBA/NCAA gates remain unchanged. NO_BET=true, actual wagers zero, promotion disabled, no Render deployment or paid feed activation.

## October 24 continuation — canonical native NBA daily game IDs

The native pregame/final page readers accepted Unicode decimal digits in the five-digit game-ID suffix, unlike the canonical full-schedule identity policy. Require ASCII digits in the shared pregame and final parsers, which also protects the opt-in null-envelope and Final-break readers. Synthetic full-width and Arabic-Indic suffixes reproduced eight failing assertions across v1/v2 pregame and v1/v3 final tests before repair; all 32 focused tests and 1,033 integrated sports tests now pass. Complete saved-source integration replay passes without rewriting tracked original evidence.

Depends on the provider key/row-ID binding repair in #255. Valid source schemas, original archived bytes and all source-only/model/wager guards are unchanged. No new outcome qualification, historical training eligibility, forecast, wager or production deployment follows from these parser checks.

## October 24 continuation — bind NBA provider lookup identity

Direct NBA schedule matching emitted the provider row's game ID without first binding it to the mapping key used by final replay. A second fixture under another key could reuse the first provider ID, causing two research finals to consume one game's scores and provenance. Schedule matching now rejects a key/row-ID disagreement before selecting any fixture. A two-fixture regression reproduces acceptance at both schedule and final boundaries before repair; a positive control retains both distinct provider games and all closed model gates.

The 34 focused NBA schedule, receipt, final and type-boundary tests and all 1,033 integrated sports tests pass. Complete saved-source integration replay passes without changing frozen evidence. These are source consistency checks, not independent official-final qualification or proof of profitability. Keep NO_BET=true, actual wagers zero, model promotion disabled and existing NFL/NHL/MLB cohorts unchanged.

## October 24 Work continuation — direct NCAA/NBA final and receipt boundaries

Recovered actual main `ab84d92d28285c7309a2645983313a6c66b9ecfb`, verified #246–#248, open issues #98/#217 and source-only cohort gates. #249 merged at `f2efd5d1a5d00eedd446222bf2b29cda45a849fa` after 15 successful checks and one intentional skip. It rejects float ESPN season stages across all three expansion cohorts, truthy college final flags, malformed provider scores, and float NBA final status/stage values. Four adversarial methods reproduced 28 failures; 27 focused and 1,020 integrated sports tests passed. All post-merge checks passed.

Post-merge live source workflow [40097049642](https://github.com/tylerstong66/Tyler-ai/actions/runs/40097049642) succeeded on that merge. Published status at **2026-10-24 13:14:44 UTC** retains 29 native NBA feature observations, zero v3 corroborated outcomes, `independent_official_final_results_verified=false` and `forecasting_enabled=false`. Publication commit `965f78d0862ce04d1a30d1109f0290e7a388fb64` retains ESPN capture `20261024T131200952400Z`; all twelve original compressed responses were separately retrieved from Git objects, decompressed and checked against their recorded SHA-256 digests. This is source-byte replay, not independent final certification or new qualified predictions.

The separate chronology repair #250 merged at `bf0b3720a014d1ccfb601d601c93e638c9896ad7` after fourteen successful checks and one intentional skip. It binds direct college/NBA crosswalk clocks to capture identifiers and rejects linked sources observed after the derived receipt. Eight adversarial clock cases failed before repair; 57 focused and 1,022 integrated tests passed. All 79 retained college crosswalks preserve prior behavior (78 pass, one preexisting exclusion), and the retained NBA schedule receipt replays. #251 merged at `c549dc55d30fb4bed5a3112b80b2afa3a38cc63c` after fourteen successful checks and one intentional skip. It rejects ambiguous NBA/linked ESPN manifest JSON and forged research guards; ten cases failed before repair, then 31 focused and 1,024 integrated tests passed. The direct source-replay follow-up #252 merged at `8d36787c8e869154bc6fad59a3348648332c6b4e` after fourteen successful checks and one intentional skip. No failing or incomplete check authorizes merge.

This branch additionally replays the full closed ESPN source capture at the direct NBA schedule-receipt boundary. A rehashed manifest alone previously permitted forged normalized scores, parsed team identity, source URL or forecasting flag; all four adversarial cases now reject. The focused NBA receipt/source/final suite passes 32 tests, and the combined integrated suite passes 1,025 tests. The complete saved-source integration replay also passes without changing tracked frozen evidence. These checks validate software and retained source consistency only; they do not attest upstream completeness, independent publication, official outcome qualification or profitability.

The subsequent preflight repair #253 merged at `bd31baf6b5d9046589df817b77ef0452848941be` after fourteen successful checks and one intentional skip. It requires exact integer zero wagers in the generic research eligibility and pregame chronology gates. Six boolean/floating-zero forgeries reproduced acceptance before repair; all fourteen focused eligibility/chronology tests and 1,027 integrated sports tests pass. Caller-asserted official-final flags still cannot grant historical eligibility, training, forecasting or promotion.

The next NBA identity repair binds regular/playoff classification to the exact official game-ID prefix, rejects non-ASCII IDs in both the full schedule and future Cup-slot parser, and preserves a valid 2026-season playoff fixture in May 2027 as research only. Six malformed identity cases reproduced acceptance before repair; all 32 focused identity/source/final tests pass. No original fixture is rewritten and no result is promoted to a qualified label.

Next: finish applicable CI and exact-head reviews/merges, verify post-merge integration and source publication, then continue independent official-final identity, season/stage, rescheduling and completeness qualification. FBS/D1/NBA training and forecasting remain disabled until genuinely qualified source labels and chronological training splits exist. Keep NFL's rejected calibrators unadopted, NHL's frozen first-100 protocol unchanged, MLB cohorts separate, and #217 blocked on authorized prospective sportsbook entry/close evidence. NO_BET=true, actual wagers zero, model promotion disabled; no Render production change, deployment, paid feed activation or wager occurred.

## October 24 — source replay integrity, independent CI and live collector evidence

Recovered live main and verified the frozen NFL/NHL/MLB scoreboards and all three separately isolated source-only expansion cohorts. Merged #246 (NHL archive/validator error redaction, `fe6cf20418ef791b1a29ca4b894311a363e5106f`), #247 (strict duplicate-key/nonfinite NCAA-owned JSON and exact integer zero-wager receipt guards, `3a730de242555508d802175355b703a1fe0b77c2`), and #248 (strict ESPN original JSON at the direct NCAA identity-replay boundary, `569fef8773053f8eae3066bf6c549e176e94296e`). The code-and-adversarial-test PRs passed all 13, 14, and 14 applicable PR checks respectively before merge. #247 supersedes conflict-blocked #237, which was closed without merging; the replacement preserved newer UTC-anchored source dates. The strict ESPN replay rejects rehashed duplicate-key and nonfinite bodies rather than treating their last JSON value as the original. No frozen original was rewritten.

The actual post-#247 main source workflow [40094243006](https://github.com/tylerstong66/Tyler-ai/actions/runs/40094243006) completed successfully, including source collection, SHA-256 replay, NCAA-owned source and crosswalk checks, FBS/D1 audits, native NBA receipts and source-only publication. Its saved `WORKFLOW_STATUS.latest.json` at **2026-10-24 12:34:40 UTC** records 29 retained native NBA feature observations, zero newly enrolled native features, zero v3 corroborated outcomes, and `independent_official_final_results_verified=false`. Native NBA daily v2 and final-break v3 source collection succeeded; legacy NBA schedule and v1 daily sources remained unavailable. A green workflow means validated source collection/replay, **not** governing-body official-final certification, historical training eligibility or a graded forecast. The subsequent post-#248 main source workflow [40094519411](https://github.com/tylerstong66/Tyler-ai/actions/runs/40094519411) also completed successfully and published status at **2026-10-24 12:38:34 UTC** (source head `569fef8773053f8eae3066bf6c549e176e94296e`): 29 retained native NBA feature observations, zero newly enrolled features, zero v3 corroborated outcomes, `independent_official_final_results_verified=false` and `forecasting_enabled=false`. Its success remains source replay, not official result certification.

The latest retained NHL challenger snapshot (2026-10-24 07:18 UTC) has **59 enrolled, 47 scored**, still short of its frozen first-100 checkpoint; no early tuning or promotion. NFL v2 remains **28 settled** with 27 paired priced decisive games, no supported edge over market. MLB hitter paper research has **31 frozen player-games**, 15 eligible scored, three ineligible and 13 unresolved, across five game IDs; same-game player trials are dependent and sportsbook odds are absent. These are retained research snapshots, not independently verified sportsbook returns. FBS and D1 historical source agreements remain research observations; D1 current-season collection starts at its separately configured October 30 boundary. No new qualified official final cohort, sport-specific fitted coefficients, forward-only college/NBA model forecasts or official-source completeness proof was established.

Next: review the post-#248 main source run and exact original receipts; continue official-result identity, season, postseason, rescheduling, completeness and independent-publication audits for FBS/D1/NBA. Fit each sport only on independently qualified time-split historical labels, and freeze genuine future predictions before the actual kickoff/tipoff with no retrospective pregame reconstruction. Keep `NO_BET=true`, actual wagers zero, promotion disabled, and Render production unchanged. NHL future sportsbook-specific executable entry/close proof remains separately blocked by #217; do not infer it from aggregator snapshots.

## October 23 continuation — UTC source dates and bounded original-byte integrity

Recovered main at `9a63617aa84e7b88e93fd294c7f08c9d082816df`, inspected open issues/PRs, source-only college/NBA archives, NHL/MLB shadow scoreboards and the rejected NFL annual calibrator. Three code-and-adversarial-test PRs were merged after their full applicable checks passed:

- #228 at `086cf0f4846b5db75d5ac4cce130e47bc69903c1`: ESPN FBS/D1/NBA collection always anchors source dates to the UTC date in the immutable receipt, not the caller's local calendar day. Western/eastern offset boundary, lookback, forward-horizon, original replay and no-bet tests passed. All 14 PR checks passed; integrated sports suite ran 975 tests. Post-merge integrated run 39951242662 passed.
- #229 at `32c162fd88d73ae32a3e2f086339942843702dec`: frozen NHL baseline model replay parses the exact bounded SHA-256-verified original bytes instead of performing an unbounded second disk read. Corruption and forbidden second-read tests passed. All 13 PR checks passed; integrated suite ran 976 tests. Post-merge integrated run 39951640307 passed.
- #230 at `d17652b9caf6d28349e7b15b3963da9b4a7deee5`: ESPN count metadata must be a nonnegative integer; source receipts require exact three-cohort league roster and integer zero actual wagers. Forged boolean/float/negative counts, omitted/reordered leagues and false zero-wager types fail closed. All 17 PR checks passed; integrated suite ran 977 tests. Post-merge integrated run 39952338682 passed.

The live college/NBA source workflow 39952338631 succeeded on #230's merged code and published original source receipts in `71e81c4f36ed22857e56a38ef2e1834770d2a253`. Its retained status reports successful ESPN collection and byte replay, 22 previously frozen native NBA reference-feature observations, and **no independently certified official final outcomes**. Successful ESPN replay and two-source research agreements are not governing-body final certification. Historical ESPN source-day retrieval is complete for its declared windows (NBA 490, FBS 302, D1 312), but completeness of official results is unverified; all three training/forecasting gates remain closed. D1 current-season collection is scheduled to begin at its separately configured October 30 boundary, not retroactively.

The NHL challenger scoreboard as of October 23 10:04 UTC had 47 enrolled, 45 scored and two pending; its fixed 100-game checkpoint and promotion gate remain incomplete. The NFL annual calibration candidate remains rejected, and the MLB hitter source/settlement exclusions remain unchanged. Future sportsbook-specific offering and independently certified close evidence still require authorized credentials and actual prospective capture (#217); no historic source can fill that gap.

Next: continue source-verified official NCAA/NBA final identity/completeness audits, preserve frozen original starts through reschedules, build separately time-split sport-specific training only when independently qualified historical labels exist, and freeze any future paper predictions before the true game start. Keep NO_BET=true, actual wagers zero, promotion disabled, and Render production unchanged.



## October 22 continuation — direct NHL settlement original-byte boundary

NHL archive/qualification repair #225 merged at
`ee860c9a58e69f49c5771ff3c46600d62c2e58d3` after fourteen successful checks
and one intentionally skipped check. The exact merge checkout independently
passed all 81 focused profitability tests. Post-merge integrated run 39826138447
passed 962 sports tests, the saved-source replay and unchanged-evidence check.
No production deployment occurred.

Further adversarial review reproduced three direct final-reader failures:
`verify_final_sources` trusted its caller to check original SHA-256, followed a
static source symlink, and read an oversized file before bounding it. The final
reader now obtains its parsed bytes through the same bounded, regular-file,
no-static-symlink, SHA-256 verifier as the quote and pregame readers. Direct calls
therefore enforce the original-byte contract independently of parent validation.
84 focused profitability tests and 974 integrated sports tests pass. This does not certify source origin,
publication chronology, executable sportsbook availability or an edge; all
wager, model-promotion and profitability-proof gates remain disabled.

## October 22 continuation — strict frozen starts across three expansion cohorts

Adversarial cases demonstrated that NBA, FBS and D1 source-observation audits
could attach agreeing finals after both reported starts moved away from the
original frozen starts. The common NBA and separate college source readers now
quarantine that drift without changing features or source receipts. FBS and D1
also reject a retained final's changed start when the latest game is absent;
absence never repairs a rescheduled result's original identity. Matching scores
and matching later sources cannot authorize a changed original start.

The separate `sports_nba_v3_feature_cohort.py` read-only audit consumes canonical
v3 receipts and independently retained ESPN originals, with optional pinned
capture IDs. It does not reinterpret v1/v2 receipts. Existing source collection
and integrated CI retain a distinct audit artifact and expose its own success or
failure independently from successful raw collection. The source workflow's
status script was executed under both successful and failed comparison cases.

On the saved October 22 v3 capture `20261022T100814250706Z`, the new audit
compares sixteen original frozen features: eleven source-agreement observations,
five outside the requested October 21 daily scope, zero enrolled outcomes or
graded forecasts. The separately pinned October 21 v3 page still corroborates
two observations and quarantines game `0022600003` for its exact-start conflict.
These are replayed original source claims, not new games, independent origin
attestation, profitability, or permission to train or forecast. 53 focused source
lifecycle tests and 971 integrated sports tests pass, including three NBA rescheduling cases and college
current-source/result-source drift cases. Original records remain unchanged;
all forecast, historical evaluation, promotion and wager gates stay disabled.

## October 22 continuation — NHL odds adversarial validation

Recovered main `5c98bdb` and original PR workflow logs: #216 passed 907 sports
tests, #221 passed 932, and #222 passed 940, with all 13 checks successful on
each head. Fresh local baseline passed 953 sports tests. Adversarial review
then reproduced static archive redirects, boolean/float coverage counts, malformed
source rows and relabelled aggregator prices entering entry/closing validation.

The repair rejects symlinks at capture destinations and every replay ancestor,
checks bounded regular files before reading, hashes the exact bytes parsed,
requires integer coverage denominators and validates every retained event row.
The profitability gate now rejects The Odds API source observations regardless
of forged availability/publication/timestamp flags and recomputed record hashes.
Both entry ROI and closing CLV validation use this gate; no promotion is enabled.
81 focused profitability tests, 962 integrated sports tests and the full saved-source CI replay pass. Static
path checks do not protect against concurrent operating-system mutation. Hashes
and local clocks still do not independently attest publication or bookmaker
execution. No live odds request, paid-service activation, frozen-evidence rewrite,
actual wager, model promotion or Render deployment occurred.

## October 21 continuation — recovered main, native final diagnostics and negative NFL result

Recovered actual main at `c3d897a91238251cd568b2283783b2b8711ccd02`, including
chat-mode PRs #198–#203. Then merged #204, #205, #206 and #207 after their
applicable checks passed. These changes retain original feature, forecast and
receipt contracts. NO_BET=true, actual wagers zero, model promotion disabled.

The NHL challenger checkpoint advanced to **33 enrolled, 31 scored, two
pending** at 10:09:06 UTC. The first-100 cohort remains incomplete, with no
missed started forecasts among the eligible saved source forecasts. Four
game-date blocks do not meet its five-block uncertainty gate. Weights,
enrollment horizon and checkpoint rules remain unchanged; early results were
not used to tune the challenger or authorize promotion.

The native October 20 NBA final page retained on October 21 was rejected
because all three cards report `gameBreakStatus: "Final"`, while the existing
v2 reader requires an empty value. #204 adds an isolated v3 diagnostic for
that exact inspected shape. It replays the original v2 receipt and source
bytes with the original response clock; the canonical receipt remains
unsupported. Existing collectors and the scheduled v2 lifecycle are unchanged.

#205 separately compares that v3 diagnostic against pinned independent ESPN
originals and original frozen features. Two games have source-agreement
observations. Game `0022600003` remains quarantined: NBA's current saved
start is 01:30 UTC while ESPN's moved to 01:50; both original frozen starts
were 01:30. Matching scores cannot bypass the exact-start gate. These are
feature observations, not predictions or enrolled outcomes. Sixteen original
NBA features remain intact; the existing v2 lifecycle still accepts zero
finals from this page. Full-season acquisition remains unavailable, and native
daily availability does not silently enable old feature enrollment.

#206 fixes repeated official MLB requests within a settlement invocation.
Status and per-hitter validation now share one original response per game,
using isolated copies and expiring the cache before the next run. Successful
post-merge live run 39594567023 used **four official game responses for twelve
player-game checks**, with zero new settlements and all twelve unresolved
records preserved. Six have original/current start conflicts and six lack
explicit official at-bats. The ledger remains 25 frozen player-games across
four game IDs: eleven eligible scored, two ineligible and twelve unresolved.
No missing count was inferred and no forecast or legacy source gap rewritten.

#207 retains a separate annual NFL calibration development recipe and its
negative result. Each 2022–2024 year uses only prior seasons for independent
base/calibrator fitting. On 813 decisive games, calibrated Brier worsened
from 0.4487592 to 0.4516064 and log loss from 0.6398104 to 0.6430794; both
paired descriptive intervals include zero. Dedicated GitHub run 39594197538
exactly matched the actual local report, and the final head requires full
semantic replay of the retained result. This retrospective experiment excludes
2025/live 2026 and is not an untouched holdout. Neither this recipe nor the
earlier fixed-fit negative calibrator is adopted. Existing prospective NFL
records remain 27 settled, including one tie, with no supported market edge.

Current college replay has **48 frozen FBS feature records**, three later
source-agreement observations and 45 pending; D1 has zero feature records.
The existing publication auditor additionally verified the 45 still-future
FBS files against exact original bytes at GitHub head
`f68aaf3ba2183a5a3688b1008b12dfb8407f20ac`, server-observed in run 39594047657
at 11:43:19 UTC, before both sources' starts. The separate saved recipe
overlaps two of the earlier five-file recipe, covering this 48-record
checkpoint. The three already-started games rely on the earlier proof;
the later server observation never retroactively attests them. Saved recipes
require fresh API replay; offline digest checks do not certify a fresh query.

Next development must preserve those distinctions: genuine later source
observations, frozen pre-event features versus predictions, exact identities
and starts, independently evaluated parameters, and unchanged originals.
NBA/FBS/D1 training, historical evaluation, forecasting and promotion remain
disabled. No retrospective diagnostic or favorable classification accuracy
authorizes wagers or model promotion.

## October 20 continuation — native NBA evidence and automatic source lifecycle

Merged #190–#197 after their relevant PR checks passed. Code checkpoint
`e9c2c6ede0a9fd37cc77efcaeb89e4a5d5e5fcf5` passed all **830 sports tests**
again in post-merge integration run 39483552863. Native v1 receipts,
historical seals and original frozen features remain replayable; none were
rewritten to satisfy the changed public page format.

NBA now has separate native v2 pregame and recent postgame receipt schemas
and archive roots. V2 requires an explicitly present null date-override field;
v1 still requires true. Both retain bounded original HTML/JSON, exact
route/query/selected-date, complete-page, identity, time and status checks.
The unknown UI flag is never rewritten or represented as an attested active
override. Native pregame collection requires complete nonempty one-to-one
ESPN agreement with exact teams and UTC tipoffs, all still pregame at the
actual complete-response clock.

The first native pregame receipt `20261020T185058198304Z` retains all eleven
October 21 games and their original bytes. The existing scheduled source
workflow has since independently collected, replayed and published further
observations of that same eleven-game date. Latest verified source run
[39483553018](https://github.com/tylerstong66/Tyler-ai/actions/runs/39483553018),
job 118838043528, published `b18ce9dea0aa93fd7c46ccc414153f3ae0963963`.
Its native pregame receipt `20261020T192725676135Z` matches all eleven fresh
ESPN games with no withheld records. Repeated observations are not additional
independent games or forecasts.

The previous-Eastern-date native postgame page is explicitly
`EMPTY_DAY_NO_FINAL_EVIDENCE`, with **zero** supported finals. The newly
fetched April 10 reference separately demonstrated fifteen regulation-final
cards under the native format; it remains historical shape evidence collected
in October, never prospective results or historical pregame availability.
Mixed/live, overtime, postseason and incomplete pages retain opaque original
bytes and zero accepted final games. Any unsupported card withholds the
whole page. Actual bounded request/response clocks and recent-date limits
prevent backdating old pages into current postgame receipts.

The native frozen-feature lifecycle now replays original feature/source
bytes and historical seals, recent native receipts and independent latest
ESPN responses. It requires frozen identities, both teams/orientation,
regular-season scope, unique exact current tipoffs, agreeing final scores,
and source observations after original/current saved starts and freeze,
at or after the NBA-reported actual end. It identifies the single requested daily scope and
out-of-scope games explicitly; missing games never imply cancellation.
The source workflow's live native lifecycle audit succeeded. It grades no
predictions, enrolls no outcomes and backfills no features. Offline integrated
CI replays the same saved sources and view with unchanged tracked inputs.

A real post-merge publication failure in run 39478799323 was traced to a
queued run checking out its older event SHA even though publication was
already serialized. #194 starts collectors from current main and records
both actual checked-out and trigger revisions. Fresh runs 39480725231,
39481081648, 39482886349 and 39483553018 subsequently published successfully.
Unavailable v1 and full-season NBA endpoints remain explicit failures.
Native daily success does not certify full-season coverage or enable the
existing NBA feature collector. The existing schedule is unchanged.

NHL's latest retained checkpoint is still **31 enrolled, 20 scored, 11
pending**, as of 17:09:07Z. The first hundred-game cohort is collecting.
The pinned challenger, weights, enrollment horizon and checkpoint protocol
are unchanged; no early-result tuning or promotion was performed.

The NFL calibration experiment remains a retained negative result: its
higher classification accuracy did not improve proper probability losses.
No calibrator was adopted and no inspected data is relabeled as an untouched
holdout. Further improvement requires independently evaluated evidence.

MLB's latest published snapshot remains **25 frozen player-games, 11 eligible
scored, two ineligible, twelve unresolved**, across four distinct game IDs.
The last validated settlement attempt retained six source-start conflicts
and six missing atBats. No forecast, original start or legacy original-source
gap was repaired by reconstruction. Missing/conflicting records remain
ungraded while unrelated exact-match settlements can proceed.

Next work is to inspect genuinely later NBA two-source finals against the
frozen feature cohort, continue the unchanged NHL first-100 evaluation,
independently evaluate any further NFL changes, and resolve MLB gaps only
from authentic source evidence. NCAA FBS/D1 work remains source/feature
research with training, evaluation, forecasting and promotion gates closed.

**NO_BET=true; actual wagers zero; model promotion disabled.**

## October 20 continuation — completed outstanding PRs and verified live MLB repair

Recovered actual main at 69b194ebb182fd1c8b5119d138ada4df8d1d2dab, beyond the
supplied checkpoint. Merged #182 (d050a70), #183 (66206f4), #186 (b222748)
and #187 (b7e5d6d), after respectively 13, 14, 15 and 18 complete green
PR workflows. Combined integration run 39469755005 passed all 795 sports
tests with unchanged tracked inputs. Post-merge run 39470850246 independently
passed all 795 tests. No model promotion or live application changes were made.

MLB final-collection run 39470850241 succeeded after 48 focused tests. It added
four separate immutable result files in 1a41ffdd3503a3d07ad5a43b5f84ee67cbef4644:
three eligible conditional results and one zero-at-bat ineligible result.
A following commit 554304b9a93c45e93df1c084ae5682c941132e04 changed only the
read-only scoreboard. All original forecasts are unchanged. Of sixteen
attempted pending player records, twelve remain unresolved: six valid start
conflicts and six missing atBats. Nothing missing or conflicting was labeled.
The published total is 25 frozen player-games, 11 eligible scored, two
ineligible and twelve pending across four distinct official game IDs; player
counts are not independent games. No betting edge, calibrated model, market
odds or independent publication attestation is claimed.

The narrow start-conflict exception arises only after strict final status,
exact game ID and both teams pass. Direct settlement still rejects that
player-game. The batch retains both starts and original/source digests, then
allows unrelated exact-match games through existing checks. Malformed
timestamps/statistics and game/team conflicts remain fatal. No schedule,
forecast, original receipt or source availability is backfilled. Existing MLB
legacy original-source gaps and independent-cohort issue #98 remain open.

NFL experiment #186 uses 1,280 base-training games (2014–2018), 784 calibration
games (2019–2021; 781 decisive), and 815 evaluation games (2022–2024; 813
decisive across 54 season/week blocks). It excludes 2025 and live 2026.
The retained report reproduces exactly in CI. Accuracy rose 62.48% to 65.81%,
but conditional Brier worsened 0.449518 to 0.450904 and log loss worsened
0.640491 to 0.642486. Paired proper-loss intervals include zero: no adoption
is supported. This is post-hoc retrospective development with separated
parameter-fitting roles, not a fresh confirmatory test or prospective gain.
The live NFL v1/v2 models and original 27-game cohort are untouched.

The NHL challenger snapshot at 17:09 UTC has 31 enrolled, 20 scored and eleven
future games, with no missed started saved eligible primary forecasts. Its
pinned recipe, weights and first-100 enrollment rule are unchanged. No early
tuning, replacement of slow results, checkpoint creation or promotion occurred.
The existing hourly collector last verified healthy at run 39463131272 remains
the forward collection path; no new monitoring automation was created.

#183 adds separate bounded postgame-source receipts. Its actual October 19
page observed October 20 13:44 UTC is empty, supplying zero final evidence.
Latest source run 39470572052 at 17:59 UTC retains NCAA/provider evidence and
reports NBA full-season HTTP 403 plus a daily date-envelope rejection. Fresh
diagnostic #188, run 39471327873/job 118795846053, verifies exact daily body
counts/SHA256 before inspecting their embedded JSON: requested and selected
dates match and error/fallback flags are false, but isDateOverrideActive is now
explicit null rather than the retained accepted true. Original bodies are
retained in artifact 12287212268. This finding does not relax the existing
source contract, certify a schedule or enable a source. Artifact ZIP metadata
was read, not independently downloaded in the unavailable local runtime.

NBA/FBS/D1 expansion forecasting, fitting, grading and promotion remain disabled
until their actual source, identity, chronology and evidence prerequisites pass.
NO_BET=true, actual wagers zero. Next: inspect real new finals at actual clocks,
resolve the changed NBA envelope through a separately reviewed source contract,
and preserve original features. Existing early or retrospective results cannot
supply a fresh prospective evaluation.

The local execution environment is unavailable; all new validation here ran in
read-only GitHub CI, with exact main/branch integration and post-merge checks.
The integrated workflow now covers benchmark edits as well as code and replays
actual saved readiness, MLB hitter results and postgame receipts without source
collection or tracked-input changes.

## October 20 continuation — expose real MLB final-source conflicts

Verified failing workflow 39394816672, job 118534804118: all 37 safeguards
passed; strict final collection then rejected official game state/time/identity.
A separate bounded read-only audit now preflights originals and retains new
official source bytes in a CI diagnostic artifact before that strict step.
The settlement rejection rule is unchanged. Seven new adversarial tests and
all 25 focused audit/settlement tests pass locally.

Actual local observation at 13:38:20–13:38:38Z read four unique games for sixteen
pending hitter records. All four archived original bodies replayed against
their SHA256 receipts. Six game 849817 records conflict only on scheduled start:
saved October 17 00:00Z versus current October 18 21:08Z (+162,480 seconds).
Teams match those hitter records. Ten other records match game/team/start only;
no batting results, outcomes or scores were enrolled. The artifact explicitly
cannot attest original pregame availability. Existing issue #98 concerns an
earlier independent-cohort schedule difference and is not resolved by this.

Next: verify CI and preserve the unresolved source discrepancy without editing
original forecasts. Final collector remains blocked by the exact-start rule;
do not represent its valid rejection as a repaired settlement or model result.
NO_BET remains true; no deployment or monitor changes.

## October 20 continuation — target-season NBA Stats access diagnostic

PR #180 merged at 657ff356819d7499c261bee6045420c2effb6ba0 after all CI
checks passed. Its post-merge collector 39428873271 completed successfully and
saved status at 13:17:28Z: ESPN/NCAA collection, crosswalks, FBS/D1 audits and
the separate NBA daily receipt passed. NBA full-season access still failed;
new NBA features stayed skipped and independent-final certification is false.
The retained daily receipt 20261020T131558790491Z replays eleven pregame games.

The bounded diagnostic now also requests the fixed NBA Stats 2026–27 schedule
route already used for retained closed-season originals. Eight diagnostic tests
pass, including fixed target season, fixed hosts, bounds, no credentials or
redirects, and no source/feature/model enablement after HTTP 200. This only
inspects endpoint availability and archives an opaque body; no collector URL,
receipt protocol, model or forecast changes. All original evidence is preserved.

Actual diagnostic run 39429708256 at head 1605141a0a82a043323161462a937246e47d56da
started at 13:21:43Z. Artifact 12266833941's ZIP SHA256
80bf88b7f311bfb0d6678591017c91b6a08338b4fbfcbf9735bbb1249bc201d1 verified
after download. The new NBA Stats request ended in ReadTimeout with no complete
body or archive. Both CDN endpoints returned 403; the three official daily
pages returned 200 but remain diagnostic responses. No source was enabled.

Next: recheck bounded target-season access when available and inspect any
complete body before considering a separately versioned schedule receipt.
Current-season postgame verification still needs real final source bodies;
the first saved NBA/FBS starts were still future at the last cohort replay.
No historical fixture can supply prospective finals. NO_BET remains true.
The diagnostic additionally requests the fixed NBA-owned all-calendar schedule
HTML route linked in original page navigation. Run 39430650043 at head
b9322dba534d47e34deacb6525d69d2831493e4b retained its HTTP 200 body in artifact
12267712354. The ZIP digest
15168f8bd190fc40e4cb5e8d62aa3406a75ae5954469f060eef4122657525b0f and original
236,781-byte body digest
76ccb614d86294657c972331415e30dbabc54e9c0f5bf0eda4f26b2119f97d64 verified.
The embedded pageProps contain layout, teamName, region and scheduleSettings;
the complete embedded JSON has no leagueSchedule, gameDates or gameId dataset.
Its games configuration is CMS presentation settings. It is an HTML shell, not
a replayable season schedule. No source coverage or freshness gap is repaired.

## October 20 continuation — protect new source capture destinations

PRs #172–#179 are merged after all of their complete CI checks passed. The
latest scope repair #179 merged at 3f98e0a75df15542c28ba1f7d4cc20c2a4c6105f
after 13 workflows passed. The following writer-boundary repair rejects static
symlinks in ESPN, NCAA, NBA schedule and college-crosswalk destination paths
before source reads/fetches or archive creation. NBA/college entry points also
check bounded regular linked manifests before decoding.

A twelve-scenario adversarial matrix covers redirected capture roots,
ancestors and dangling links, asserting no network request and unchanged
outside-directory bytes. All 35 focused and 755 integrated sports tests pass
with current main. Existing valid capture/replay tests remain green and both
original historical seals still replay 2,920 files unchanged. These guards
remain static checks, not concurrent filesystem-race protection.

Existing NFL/NHL/MLB original forecast/result hash, identity and chronology
checks passed read-only: respectively 27/27, 68/57 and 10/7 retained records
at this checkpoint. They are integrity counts, not performance claims or new
forecasts. The historical NBA page/ESPN diagnostic still verifies 15 reference
final agreements, with zero outcome enrollment and no current-season claim.

Next: obtain actual current-season postgame NBA bodies at their real receipt
clock and inspect lifecycle shapes before connecting a separate result-source
collector. Full-season NBA acquisition, unsupported overtime/postseason/mixed
pages and MLB legacy-source gaps remain blockers. Fitting, new expansion
forecasts, historical evaluation, grading, promotion and wagering stay disabled;
NO_BET is true. No Render changes or new monitoring automation were made.

## October 20 session checkpoint — source integrity and NBA reference finals

PRs #172–#178 are merged after their complete CI checks passed. #173, #175,
#176 and #177 close reproduced static symlink, ancestor-directory and source
filename redirects across MLB, ESPN, NCAA and NBA archive readers. #174 adds
the separate regulation-final NBA daily parser; #178 replays 15 historical
NBA-page/ESPN agreements with actual October observation clocks. GitHub artifact
12265303431 at run 39425842961 matched its ZIP SHA256 and the exact local report.
These are historical reference checks, not current-season final certification.

A final provider entry-point repair validates sport, split, canonical date and
an explicitly supplied aware observation cutoff before any archive access.
Two adversarial methods reproduced nine scope failures and two invalid-clock
errors before repair. All 29 focused and 754 integrated sports tests pass on
current main plus that repair; #179 subsequently merged after all 13 GitHub
workflows passed. The original 2,292-file seal and 628-file extension seal still verify.
Frozen forecasts, features and source bytes are unchanged by these repairs.

Post-merge source run 39426321967 at #177's fbc2db7 records successful source
replay, FBS/D1 checks and separate NBA daily collection at 12:58:37Z. Independent
full-season NBA acquisition still fails, new NBA features remain skipped and
official-final certification is false. MLB issue #98 and legacy original-source
gaps remain unresolved; joint cohort comparison is disabled. Static path checks
are not descriptor-based protection against concurrent OS mutation.

Next: retain actual current-season NBA postgame bodies with their real receipt
clocks and inspect supported/unsupported lifecycle shapes before wiring a
separate result-source capture. Overtime, postseason and mixed-status daily
pages remain unsupported. Keep model fitting, new expansion forecasts, grading,
historical evaluation, promotion and wagers disabled until prerequisites pass.
NO_BET remains true. No Render deployment or monitor duplication was performed.

## October 20 continuation — historical NBA page/ESPN reference agreement

PR #174 merged at 3d19049d3e308e31c4600648a95aa758ba367fec after all 15
workflows passed and a local current-main integration passed 738 sports tests.
The separate read-only reference diagnostic now joins its pinned original
April 10 page with the already sealed ESPN April 10 response. All 15 finals
agree under the existing identity-first classifier. The ESPN raw/receipt
must replay under the original 2,292-file content seal before comparison.

The two observations were recorded October 18 and October 20, respectively;
agreement is available only at the later October clock. Five new tests cover
original cross-source replay, invalid/future observation clocks, seal changes,
score conflicts and identity mismatches. All 29 focused and 743 integrated
sports tests pass on this branch, before pending current-college and NBA
filename changes. The diagnostic enrolls zero outcomes and writes no dataset,
feature or prediction; its CI artifact is explicitly a historical fixture.
Current-season finals, prospective accuracy, fitting, grading, forecasting and
promotion remain unverified or disabled. NO_BET remains true.

Next: inspect and retain current-season postgame NBA pages using actual receipt
clocks, then design separate result-source capture without altering original
features. Overtime/postseason/mixed-status shapes still require real inspection.

## October 20 continuation — offline NBA regulation-final page parser

The original April 10 NBA-owned page from diagnostic run 39420119470 was
downloaded and verified against GitHub artifact 12263667020's ZIP digest and
the report's exact body size/SHA256 before implementation. The separate offline
parser replays 15 regulation finals. IDs, teams, starts, statuses and scores
match the separately retained NBA-owned 2025–26 season response; this is
same-origin corroboration, not independent ESPN final verification.

Eleven new tests cover original-byte replay, historical observation timing,
game/team identity, status and period totals, completeness, chronology,
unsupported lifecycle shapes and archive tampering. All 42 focused page/daily
tests and 734 integrated sports tests pass. The pregame parser keeps its
original status rules and shares only document envelope validation. The new
read-only CI replay retains its diagnostic output separately. See
NBA_DAILY_FINAL_PAGE_V1.md.

No current-season final collector or grading pipeline is connected. Overtime,
postseason and mixed-status pages remain rejected pending real shape inspection.
The fixture's observation clock is October 20, never an earlier pregame freeze.
Next: retain genuine current-season postgame source receipts and reconcile
strict identities against ESPN, while keeping fitting and forecasting disabled.
Archive path repair PR #173 merged at e205ca0842a74bb53b362029b448b5714fee9c50
after all checks passed, including the complete historical replay workflow.
Its post-merge source run 39423783405 records successful ESPN/NCAA collection,
replay and FBS/D1 checks at 2026-10-20T12:39:17Z. The separate NBA daily receipt
20261020T123822346914Z replays 11 pregame identities. Full-season NBA acquisition
still failed and new NBA features were skipped; official-final certification
remains false. This verifies collector compatibility, not new model readiness.

## October 20 continuation — archive path integrity

Adversarial fixtures reproduced static directory/ancestor symlink acceptance in
the ESPN capture auditor, direct NBA daily replay/collection and MLB original
response retention/replay. These paths now reject symlinks in every ancestor
before archive access, including dangling archive roots. ESPN manifest and blob
reads additionally require bounded regular files. Five new regression methods
exercise ten previously accepted cases; 32 focused tests and all 723 integrated
sports tests pass. Original benchmark evidence is unchanged. This is a static
working-tree check, not descriptor-based protection against concurrent filesystem
mutation; other archive readers still need a separate scope review.

PR #172 was reviewed and merged at ea8a55ee8ca8b7ce9535133d016b410435f7021e
after its 13 PR workflows passed. It only adds a fixed previous-season completed
NBA games-page diagnostic endpoint; it does not establish independent finals.
Next: inspect its archived actual response before designing any final parser,
and extend archive path safeguards to other readers where tests justify it.
Forecasting, fitting, historical evaluation, promotion and wagers remain disabled
for the expansion cohorts. NO_BET remains true; no Render changes were made.

Archive repair PR #173 merged at e205ca0842a74bb53b362029b448b5714fee9c50
after all CI checks passed. A follow-on repair applies its static path guard
to historical ESPN/FBS/D1/NBA receipts and current NBA schedule/linked ESPN
reads. Three regression methods reproduced 25 failures before the repair; a
fourth checks bounded regular receipts. All 35 focused tests and 727 integrated
sports tests pass on this branch (before the separate final-page parser).
Original content seals replay 2,292 original and 628 extension input files;
all 42 FBS weeks, 312 D1 days and two NBA seasons still verify without byte
changes. This remains a static check, not concurrent filesystem race protection.

PR #175 merged at 838cfc1c7d2ffe6d898cd87f33b12ec6ec45fcba after all 15
workflows passed. A subsequent direct NBA provider boundary check reproduced
seven cases accepting an absolute/traversing/wrong-day archive reference or
noncanonical date. The reader now requires a valid canonical calendar date
and exactly NBA_<date>.json.gz before access. All 22 focused and 729 integrated
sports tests pass on this branch, before the separate final-page and current
college changes. No original source bytes or identity rules were rewritten.

## October 20 continuation — NBA-owned daily page evidence

PRs #164, #165 and #166 merged the D1 collector, UTC freeze correction and
shared college lifecycle reader. The 2026-10-20T10:01:14.881192Z source status
reports successful ESPN/NCAA/FBS/D1 collection and lifecycle checks, while the
NBA CDN schedule request still fails and new NBA feature collection is skipped.

The separate read-only access diagnostic found an accessible NBA-owned source:
the official games pages for October 20 and 21. Diagnostic run 39415304518 at
commit 72e77afb81ea504c6ec7b49fadc1c3eca7db9425 archived both original HTML bodies.
The downloaded artifact ZIP matched GitHub's SHA256 digest, and the two original
body sizes/hashes matched the archived probe report before parser development.

The new offline parser accepts 3 games for October 20 and 11 for October 21.
All 14 game IDs, home/away tricodes, statuses and scheduled UTC starts exactly
match the earlier archived owned season schedule. A read-only reconciliation
against ESPN capture 20261020T095948145364Z matches those same 14 games; the other
14 ESPN games remain outside these two pages' corroborated coverage.

Thirteen focused tests cover original source replay, identity/season/date and
chronology rejection, duplicates, incomplete pages, corrupted archives, pinned
manifest changes and decompression limits. This is an offline source parser,
not a live collector fallback. Initial source replay uses its saved clock and
explicitly reports that it is not a fresh observation. No actual-start/final,
receipt-clock, full-season, forecast or model claims follow from HTTP 200.
See NBA_OWNED_DAILY_PAGE_V1.md. NO_BET remains true and actual wagers zero.

## October 19 continuation — D1 lifecycle and shared college result checks

PR #164 merged the prospective D1 reference collector after all 13 CI workflows
passed. Its first post-merge source receipt at 2026-10-19T23:03:04Z records
D1_FEATURE_OBSERVATIONS success, alongside valid ESPN/NCAA collection. NBA
schedule acquisition still failed; new NBA collection remained skipped.

PR #165 merged the fix for non-UTC NBA/FBS collection clocks producing records
that failed subsequent replay. The two new tests reproduced both failures before
the fix; 27 focused and 671 integrated sports tests passed afterward. Read-only
audits reverified all 16 original NBA and five FBS files without byte changes.
All 13 PR workflows passed before that merge.

The D1 lifecycle reader in this change replays original feature inputs and
attaches only source-backed, identity-consistent, chronologically valid final
observations. It shares the classification core with FBS while preserving
separate protocol scopes, schemas and actual-start disclaimers. All 682 sports
tests pass, including 21 FBS/D1 lifecycle cases. The real five-record FBS report
is unchanged under canonical JSON at a fixed clock after extracting the core.
The real D1 reader returns an empty cohort with zero result observations.

See D1_FROZEN_FEATURE_COHORT_V1.md. Source artifacts and outcomes expose D1
collection and lifecycle checks separately. Missing games do not become
cancellations, saved starts do not attest actual tipoff, and source quarantines
cannot become results. No original feature, source receipt or forecast is
rewritten; predictions, accuracy, fitting, evaluation, activation, promotion
and wagers remain disabled in this preparation work.

## October 19 continuation — prospective D1 collection readiness

PR #163 merged the existing six-record MLB declared-source publication audit
after all 15 CI workflows passed. Its independent native API replay confirmed
all 21 exact record/archive blobs. The combined sports suite passed 659 tests.

The separate D1 collector in this change pins eight corroborated prior-season
results per team for the 2026–27 source window. Its real-data preflight replayed
5,977 historical reference games and found zero current D1 crosswalk matches;
it created no live records. Both historical content seals, the reviewed D1
identity policy and original provider team names/IDs are replayed. Current
matching keeps strict live-source identities and enables no new live aliases.

Ten new D1 tests and the existing FBS tests pass 25 focused cases; the final
combined sports suite passes 669 tests. Tests cover
last-eight selection, immutable replay, late/missing history, changed identities,
calendar limits, schedule state, duplicate IDs, stale/future sources, source
corruption and UTC normalization. Collector status distinguishes an existing
college crosswalk from actual D1 source games; successful empty preflight cannot
claim a current D1 cohort. Source publication skips absent record directories.

See D1_PREGAME_REFERENCE_FEATURES_V1.md. New D1 cohorts will still need separate
publication and lifecycle checks. These records are reference features, not
predictions; fitting, historical evaluation, forecasting, promotion and actual
wagers remain disabled. Existing NBA/FBS features and original archives are
unchanged. NBA acquisition and legacy MLB source gaps remain unresolved.

## October 19 continuation — declared-source MLB cohort publication

PR #162 merged the read-only legacy source inventory after all 13 CI workflows
passed. The old 19 hitter records still lack replayable original pregame game
bodies; current canonical-JSON matches do not repair their original provenance.

Six newer records for game 849815, already created by the existing collector,
have four explicitly declared original source responses each. A separate live
audit and second replay verified their six exact sealed record blobs and 15
distinct exact source archive blobs at immutable head
d07e0a8ce2b281715bba61f0feef62032a9e8230. GitHub run 39325179589 was created at
2026-10-19T21:08:55Z, after their 20:00:51–20:00:57Z freezes and before all saved
2026-10-20T00:08:00Z starts. The new audit's 45 focused publication/transport
tests passed. This local audit does not claim its own PR has merged.

See MLB_ARCHIVED_SOURCE_PUBLICATION_V1.md for replay and evidence transport.
These checks bind declared record/archive bytes to a server-observed commit;
they do not certify response origin, receipt clocks, actual first pitch, every
model input's semantics or prediction quality. No new forecasts, training,
grading, model activation or wagers were performed. The original legacy source
gap and issue #98 remain open.

## October 19 continuation — prospective feature cohorts and overnight source coverage

PRs #154–#161 merged the NBA and FBS feature lifecycle readers, MLB cross-cohort
schedule audit and original publication chronology, five prospective FBS
reference-feature records and their separate publication chronology, shared
bounded GitHub server-evidence transport, and opt-in overnight source lookback.
The combined sports suite passed 645 tests after integrating the FBS lifecycle
change with current main. PR #161 merged after all 13 refreshed workflows passed.

The 16 original NBA and five original FBS records are feature observations,
not predictions. FBS uses four corroborated previous-season games per team;
NBA uses ten. Original sealed records remain unchanged. GitHub server-created
workflow observations separately bind the exact cohort bytes before both saved
starts; these proofs do not attest actual kickoff/tipoff or upstream truth.
The FBS read-only lifecycle replay on October 19 returned five pending records,
zero result observations, zero schedule drift and zero identity quarantines.
The first original NBA/FBS saved starts are October 20 UTC.

Source workflow run 39307568503 completed successfully after PR #160. Its
20261019T190225407561Z ESPN capture declares two prior UTC days and three
forward days and retains 52 provider-reported FBS final observations. These
are source observations, not graded predictions. A persisted workflow
receipt at 2026-10-19T19:18:47Z records successful ESPN/NCAA collection and replay,
crosswalk, result-dataset, FBS-feature and NBA-cohort checks, while independent
NBA schedule acquisition failed and new NBA feature collection was skipped.
Workflow success therefore continues to mean partial source availability.
After #161 merged, source run 39325179589 completed successfully and its
2026-10-19T21:09:30Z receipt additionally records FBS_FEATURE_COHORT_AUDIT
success. NBA schedule acquisition still failed and new NBA features stayed
skipped in that run; the successful workflow does not close that source gap.

MLB's original 19-hitter/three-winner cohort publication chronology was separately
verified. Original saved starts differ by 120 minutes for six hitter records and
eight minutes for another six; joint performance comparisons remain disabled.
The original pregame game-response bodies remain unreplayed. Later archive
canonical-JSON matches do not establish original wire bytes or availability at
freeze. The new read-only inventory verifies 18 current archives and finds
canonical-JSON matches for 12 roster and 24 hitter-history references among the
original 76 receipt references. None matches the 19 original pregame game-feed
references. Its seven new tests and the related archive/cross-cohort tests pass
24 focused cases. See MLB_LEGACY_SOURCE_CONTENT_INVENTORY_V1.md. Issue #98
remains open; original forecasts and receipts are unchanged.

Next: retain source final observations as the original feature events occur and
investigate legacy MLB source gaps without rewriting old receipts or upgrading
their provenance claims. Training,
new forecasting, historical evaluation, model promotion and wagers remain
disabled in this feature-preparation work. NO_BET remains true.

## October 19 continuation — GitHub server chronology for the first NBA feature cohort

PR #151 merged the 16 original feature observations with all 12 GitHub CI
workflows passing. A live GitHub API audit now verifies the exact bytes of all
16 records at immutable head f160b9ba98148b67dd8ecb077e27b291a39a9361.
GitHub created workflow run 39262563627 at 2026-10-19T13:43:22Z, after the
original feature freeze and before both saved starts for every record.

The separate report and auditor in this change retain that narrow claim:
GitHub's server observed a commit containing those exact feature bytes before
saved start times. They do not certify public visibility, actual tipoff,
source-origin truth, forecasts, model quality or profitability. Original feature
records remain byte-for-byte unchanged and still decline publication attestation.
Saved reports require fresh API replay; they are not standalone server proof.
Replay explicitly preserves the original cohort even after future records arrive.
See NBA_FEATURE_PUBLICATION_CHRONOLOGY_V1.md. NO_BET remains enforced;
training, historical evaluation, forecasting, promotion and wagers stay disabled.

## October 19 continuation — original pregame NBA feature observations

PRs #146–#150 merged source-backed NBA/FBS/D1 feature diagnostics, reviewed D1
source identities and current NBA schedule acquisition. Local all-sports tests
now pass 546 cases. The historical diagnostics retain the explicit distinction
between post-hoc reconstruction and genuinely observed pregame availability.

The current NBA source fix preserves 1,200 concrete supported games and six
future Cup TBD slots in a separately replayed quarantine. Its first original
capture matched 16 future ESPN/NBA schedule identities, with zero final results.
Strict v1 receipt/parser behavior and all original archives remain unchanged.

The new digest-pinned NBA reference-feature collector in this change froze 16
feature observations at 2026-10-19T13:33:36.525177Z before their October 20–22
Eastern-date saved starts. Each team has ten corroborated prior-season results
whose original receipts were available by the freeze. A second collection and
read-only audit verified all sixteen without replacements. These are feature
observations, not predictions or a trained-model activation; original records
explicitly decline independent publication-time attestation.

The scheduled source workflow stages feature records only after successful
full preflight and source replay. Invalid existing records stop new feature
writes; started, stale, ambiguous or incomplete targets stay unenrolled. Later
source snapshots and postgame audits cannot rewrite original feature records.
No odds, probabilities, fitting, outcome grading, model promotion, deployment
or actual wagers are enabled. Next: independently inspect original publication
chronology and preserve the first prospective feature cohort as future data arrive.


## October 19 continuation — source-backed feature preparation and D1 identities

PR #146 merged the NBA-only source-backed team-form diagnostic reader. Both
original source-content seals verify before feature extraction. Actual receipt
timing and an explicit kickoff-plus-24-hour reconstruction use separate state;
current/future outcomes and other-season data cannot enter a target's history.
Both-team reconstructed history exists for 1,294/1,299 of 1,310/1,315 targets,
while observed-receipt history is unavailable for those past seasons. No fit,
probability, historical paper forecast, evaluation or model activation is enabled.

PR #147 merged the source-backed D1 identity review packet: 127 candidate
institution-name pairs, 112 excluded pairs, repeated exact-time/opponent anchors
in both source seasons, stable source slugs/team IDs and no score-based identity
selection. The packet adds no runtime aliases or Division I membership claims.

The separate digest-pinned opt-in D1 spelling policy and source-dispute reader
in this change preserve default exact replay and the FBS policy. Replay yields
6,047 training / 5,977 validation source-final agreements; changed starts,
nonfinals, ambiguous identities and all source quarantines remain excluded.
Newly recognized Idaho State–Montana (NCAA 6349336 / ESPN 401720925) reports
86–61 in NCAA and 86–62 in ESPN and stays excluded, alongside Belmont–Drake's
validation disagreement. See D1_HISTORICAL_REVIEWED_SPELLINGS_V1.md.

Next: prepare separately scoped FBS and D1 chronological feature diagnostics,
retaining observed availability versus reconstruction assumptions and the same
no-training/no-evaluation/no-forecast/no-promotion/no-wager restrictions.
Completing a PR or these steps is not a request to pause autonomous work.


## October 19 — completed independent archives and stricter research diagnostics

PR #142 merged a separate opt-in historical NBA exact-tipoff identity policy.
It recovers repeat fixtures only with one exact UTC start and no competing
fixture within 30 minutes; original v1 policy and receipt bytes remain unchanged.
The separate replay yields 1,310 training / 1,315 validation final agreements,
versus 1,185 / 1,203 under v1. No outcome selects an identity.

PR #143 merged the full NCAA-owned D1 validation request window. Both D1
splits now retain 156/156 dates; scheduled main-branch training receipts won
an overlap resolution without rewriting their original observations. There are
6,346 unique NCAA training contest IDs and 6,332 validation IDs. Exact school
matching yields 2,965 training / 2,954 validation final agreements. The original
0–0 NCAA final for contest 6442390 remains quarantined. Belmont–Drake on
March 6, 2026 (NCAA 6592612 / ESPN 401851488) remains excluded: NCAA reports
81–100, ESPN 79–100. All other unmatched identities and changed starts stay
excluded. Request-date completeness is not official schedule completeness.

PR #144 merged diagnostics that retain both original claims, all source observations and
receipt hashes for exact-identity score disputes. The separate completed
628-file D1/NBA content index pins its manifest digest; the older 2,292-file
seal remains unchanged. The new index and its checks accompany this handoff
update; see the historical archive README for exact scope and limitations.

Next research gate: derive sport-specific pregame feature availability and
chronological split integrity from trusted source receipts. These historical
responses were observed after their events and are not saved historical
pregame predictions. Do not convert source agreements or caller-asserted flags
into training/evaluation eligibility. D1 school identities remain exact-only;
no fuzzy matching, score-based identity selection, automatic model activation,
forecast generation, promotion, runtime deployment or actual wagers.


## October 18 — linear linked-source replay and end-to-end D1 regressions

Extracted the unchanged single-capture ESPN integrity audit so receipt readers
validate only linked sources; full coverage audits still replay all captures.
Local aggregate timing: 3.300s before / 0.482s after, byte-identical 23-game
output; full source audit equals the retained coverage report. Added original
NCAA MBB/ESPN D1 fixtures including nonfinal and unknown-alias exclusions.
112 combined source-pipeline tests passed. NBA archived-final reader PR #127
merged with all 13 checks; all post-merge workflows succeeded, with unavailable
independent NBA source still explicit. No wagers, promotion or runtime deploy.

## October 18 — cross-capture college result dataset and identity uniqueness

Added strict one-NCAA/one-ESPN identity use, original school/team IDs in separate
v2 receipts (v1 bytes preserved), and all-capture result deduplication. Changed
scores, source state regression and reassigned IDs quarantine observations.
Retained 18 crosswalks: 17 replayed / 1 explicitly excluded as nonreproducible
under current identity policy; 23 unique FBS agreements / 0 accepted-game
quarantines. No model eligibility, wagers or accuracy claim. 103 local source
pipeline tests passed. Dedicated CI and source collection retain aggregate JSON
as a 30-day artifact. See `SPORTS_RESEARCH_MATURITY_2026_10_18.md` for the six
separate sports and their actual remaining evidence gaps.

## October 18 — archived NCAA/ESPN final research receipt reader

Implemented `sports_college_final_receipts.py` and dedicated PR CI. Every
research-only final agreement now can be replayed from an explicit crosswalk,
linked manifest hashes and original NCAA/ESPN raw responses. Both source
observations must follow both saved starts; invalid chronology is quarantined.
No historical model eligibility or independent final certification is granted.
Local 85-test source suite passed; latest real crosswalk
`20261018T171012515514Z` produced 0 qualifying finals / 4 pending or quarantined.
See `COLLEGE_ARCHIVED_FINAL_RESEARCH_V1.md`. GitHub research code only; no
production deployment, model promotion or actual wagers.

## October 17, 2026 — New leagues: FBS college football, Division I men's basketball, NBA

**Explicit user-requested three-league expansion.** Each is separately scoped and source-only in version 1, not a copied NFL/NHL/MLB model. No current new-league betting picks, historical-fitted model, scored probability, official verified result or production deployment.

- **PR #102** (11/11 checks passed, merged) adds `sports_expansion_observer.py`, `test_sports_expansion_observer.py`, `benchmarks/college_nba_source_v1/README.md`, and independent GitHub Actions `.github/workflows/college_nba_source_observation.yml`. The workflow is scheduled approximately 05:10, 13:10, and 21:10 UTC and was verified successful on the post-merge run. This does **not** change the existing NFL/NHL/MLB scheduled workflows.
- Provider source scope: `NCAAF_FBS` = ESPN FBS-associated (group 80) schedule, `NCAAM_D1` = ESPN Division I-associated men's basketball (group 50), `NBA` = ESPN NBA scoreboard; all specify `limit=500` to avoid default top-25 truncation. ESPN snapshots are **not** independently official governing-body NCAA/NBA finals. Preseason/unknown competition stages remain excluded, not silently misclassified. NCAA men's basketball observation starts October 30 ahead of the NCAA's November 2 regular-season opening; NBA observations began October 17 ahead of its October 20 regular-season opening.
- Raw ESPN responses are timestamped and gzip-archived with SHA-256, original source URL, provider game/time/season/team IDs and observed state; conflicting representations of the same game across dates are quarantined rather than preferentially chosen. No retroactive paper forecasts, odds collection or unsourced game results are produced. `forecasting_enabled=false`, `official_final_scoring_enabled=false`, `model_training_enabled=false`, `promotion_allowed=false`, `NO_BET=true`, `actual_wagers=0`.
- **PR #103** (11/11 checks passed, merged) adds `sports_expansion_audit.py`, `test_sports_expansion_audit.py`, and an explicit GitHub Actions audit step/commit gate. An independent source replay verifies each saved gzip response against the original SHA-256 and the normalized games, replays cross-date quarantine, checks league/date request grouping, rejects source/identity/time tampering and validates no-model/no-bet flags. This is **independent validation of archived provider bytes**, *not independent verification of official final scores*. The post-merge collector/audit completed successfully.
- Verified `benchmarks/college_nba_source_v1/COVERAGE.latest.json` at **2026-10-17T12:49:04Z**: **2 archived collections**, **16 raw source responses SHA-verified** and **0 quarantined games**. Across those two collections, FBS has **110 provider game observations** (the same 55 schedule games seen twice), NBA **6 provider game observations** (the same 3 opening-day games seen twice), and NCAAM **0 yet** because the start-of-season observation window has not opened. **Do not** represent 110/6 as unique fixtures, actual results or trained forecasts. The report independently replays both observations with no scored new-league outcomes.
- Remaining **critical prerequisites before prospective new-league predictions**: separate league/team membership identity verification, independently verified NCAA/NBA official results (including time changes, overtime and postponed games), previous-season historical training with strict chronological feature cutoff/holdout, frozen separate baselines, exact pregame prediction timestamp/hash enrollment and paired later performance benchmarks. No borrowing other sports' coefficients, no backfilling and no automatic promotion.
- Existing daily **Tyler AI Development** automation was updated to include all three new leagues in future justified work, while the existing hourly Tyler Health & Results monitor remains scoped to separately recorded NFL/NHL/MLB outcomes and was not duplicated. Do not mistake new research source captures for model results. Render production auto-deploy remains OFF.

**Next engineering milestone:** Build and test independent official final cross-check adapters for NBA and NCAA before adding training/forecast production. Keep sports-specific baseline recipes segregated. Preserve all existing saved source archives on schema changes or replay incompatibility; do not silently reinterpret historical observations.

---


## Latest verified continuation — 2026-10-16 22:04 UTC

- **NHL shadow:** now **3 genuinely post-activation immutable forecasts**, **0 scored / 3 pending**, and **0 missed saved-source enrollments** as of the 21:09:32 UTC scheduled audit. The three future games are **NJD at WSH (2026020121)**, **CAR at WPG (2026020122)** and **VAN at TBL (2026020123)**. Original NHL cohort **40 recorded / 35 settled / 5 pending**. No Brier or calibration inference from the still-unscored challenger.
- **MLB hitter shadow:** **13 sealed player-game forecasts**, **4 scored**, **1 confirmed zero-AB ineligible**, **8 pending** as of the 20:10 UTC public feed; six new pending forecasts relate to game **849817** whose first pitch was saved as 2026-10-17 00:00 UTC, while two older unresolved forecasts still await sealed official final batting evidence for **Gary Sánchez** and **Andrew Vaughn** (game **849810**). No missing field treated as zero or a loss.
- **PR #96** merged with **12/12 CI checks**. The read-only MLB scoreboard reader now classifies *displayed original saved first-pitch chronology* as future versus elapsed, including explicit hidden pending counts. This is **not official evidence of game start, completion, an at-bat or a wager outcome**. Legacy scoreboard feeds remain supported. It does not deploy an updated Render application.
- **PR #97** merged with **12/12 CI checks**. The official-final MLB hitter collector no longer crashes when the historical prediction directory exceeds 100 files; it first preflights every sealed original forecast and existing settlement, then checks up to 100 unsettled past-scheduled-start player-games per execution, rotating windows on its existing three-hour schedule. Full future/pending/deferred counts and window selection remain explicit. Its triggered post-merge collector's unit test, official final, scoreboard and commit stages completed successfully; full GitHub run concluded **success**. Forecast and result immutability and NO BET remain intact.
- **Open diagnostic issue #98** documents the confirmed **MLB game 849817 independent-cohort schedule drift**: team-winner original saved 2026-10-16 22:00 UTC versus six later hitter forecasts saved 2026-10-17 00:00 UTC (**+120 minutes**). This may reflect a legitimate schedule update between their independent original freeze times; do not merge the cohorts' score records, silently rewrite timestamps, infer current market pricing or treat the earlier game-winner readiness as verified. A proposed new cross-cohort audit code write was blocked by the available tool safety check; **no audit code was published**. Issue is tracking, not a shipped feature.
- All latest reviewed evidence remains **RESEARCH ONLY / zero actual wagers / no automatic promotions**. Render remains intentionally auto-deploy OFF; the research code and new read-only classifications have not been represented as an updated runtime deployment. GitHub scheduled collection and settlement workflows may operate independently of this chat according to their configured cadence.

**Next justified engineering/evidence steps:** Verify actual official NHL results for the first three challenger games on or after their scheduled completion; score only frozen forecasts once independent result evidence exists. Verify the NHL model/Elo/market paired comparison and casebook after those results (not before). Check the MLB hitter publisher and settlement logs as newly eligible official finals become available; retain explicit pending reasons for the two incomplete players. Treat the 849817 cross-cohort scheduling issue as a research integrity question, not a reason to rewrite old forecasts. Do not tune the NHL challenger on its prospective outcomes or claim a betting edge from small early cohorts.

---


## Verified after NHL activation: source comparison, postgame audit and MLB freshness (18:04 UTC)

Research/paper only; **NO BET / zero actual wagers / zero model promotions**. The following changes are GitHub research workflows, **not** new Render production deployments.

- **NHL shadow:** first real post-activation forecast is `2026020121`, **New Jersey at Washington**, starting **2026-10-17 17:00 UTC**. Its frozen Washington home-win probability is **0.5911197964** from the independent 2024-fitted challenger, versus original model **0.5410579328**, fixed Elo **0.6224179446** and saved market **0.5324675325** (archived DraftKings quote at 2026-10-16 17:24:56 UTC, **not current odds**). This is a forecast, not an event result. As of the post-merge 2026-10-16 17:51 UTC audit, **1 shadow enrolled / 0 scored**, **0 missed enrollments** and first-100 checkpoint collecting. Original NHL cohort **38 enrolled / 35 scored / 3 pending** at the matching research audit.
- PR **#90** adds a source-hash-linked read-only pregame probability comparison for the earliest 25 future shadow NHL games by scheduled start/ID, never cherry-picked by expected win. **15/15** checks passed; post-merge automated collector published exactly the first frozen matchup.
- PR **#91** adds a verifiable postgame casebook for up to 25 latest verified outcomes; it uses immutable original and shadow digests, authenticated result linkage, proper scoring and same-game candidate-minus-baseline differences. **15/15** checks passed; as expected the casebook initially remains empty until the first official final result is verified.
- PR **#92** preserved the first real NHL challenger forecast and immutable publication state in this handoff. **10/10** checks passed.
- **MLB hitter feed freshness:** PR **#93** now recomputes unchanged saved research and refreshes a feed heartbeat at most every 2 hours while keeping the date of the **last actual benchmark content change** separate. Successful refresh must not be mistaken for fresh official at-bats, a model improvement or independently attested publication. The GitHub PR passed **12/12** checks. Verified public feed heartbeat **2026-10-16 18:00 UTC** reported unchanged 13:15 UTC benchmark content. The new optional reader metadata is backward-compatible; Render auto-deploy is **OFF** and should not be represented as updated app code.
- **MLB unresolved hitters:** PR **#94** added source-sealed player-game identities for up to 25 pending forecasts, with count/truncation checks and explicit non-grading. **14/14** checks passed; the publisher's post-merge workflow updated `scoreboard.latest.json` at **2026-10-16T18:04:26Z**. The benchmark still has **7 frozen hitter forecasts / 4 scored / 1 verified zero-AB ineligible / 2 pending**, all from MLB game **849810**. The two still-pending players are **Gary Sánchez (596142)** and **Andrew Vaughn (683734)**. Status is `NO_SEALED_OFFICIAL_SETTLEMENT_YET`, **not proof of zero official at-bats, a loss, or failure to play**.
- MLB team-winner readiness remains unresolved for game **849808** (current ESPN event/recorded pregame odds missing) and **849817** (saved first pitch 22:00 UTC, latest official 00:00 UTC next day, +120min). Do not backfill prices, rewrite freeze/start, or grade conflicting events. NFL retained prospect cohort **14/14** settled with insufficient independent week blocks for confidence claims.

**Next developer priority:** Let scheduled pregame enrollment and source-final verification run without interruption. On the first NHL challenger game final, validate the hash-linked shadow casebook and same-game scores against the original official result before interpreting aggregates. Continue the existing retry-only settlement logic for the two unresolved MLB hitters; grade only complete verified official lines. Do not change frozen NHL model weights, retrospective samples or no-wager gates. GitHub collector operations occur on their scheduled cadence; additional code work starts only in an active ChatGPT/Work session or a separately configured automation.

---



**Research/paper only. No real wagers. No model promotion without genuinely sufficient independent prospective evidence.** This is a current operational entry; older historical notes remain below unchanged.

### First independently enrolled NHL challenger forecast — verified 2026-10-16T17:51:45Z

- **Cohort is active.** Post-cutoff NHL game `2026020121`, **New Jersey Devils at Washington Capitals**, scheduled **2026-10-17T17:00Z**, was recorded before start. The immutable original NHL forecast was generated at **2026-10-16T17:24:56Z** and shadow record written at **17:24:58Z**. Original `sha256=2ac1b09bf7d217c039df2fac8e11b067fbd3156ad4d71e44a4411afb0f6fc8b9`, shadow `sha256=8538cf4b864bc5448a877bf7ab806f580babf7fa661b699aab26d51af39f396a`. No retrospective addition.
- Frozen Washington home-win probabilities: **NHL challenger 0.5911197964; original model 0.5410579328; fixed Elo 0.6224179446; market 0.5324675325.** The DraftKings market number was archived **2026-10-16T17:24:56Z** and **must not** be described as current or closing odds. These numbers are research inputs, not a bet recommendation or evidence of profitability.
- The independent NHL original prospective cohort was **38 enrolled / 35 scored / 3 pending**, versus the shadow **1 enrolled / 0 scored / 1 pending**, at the verified 17:24–17:51 UTC audits. Shadow source coverage was 1 eligible new original / 1 shadow / 0 misses. No first-100 checkpoint report exists yet; its status is `collecting_forecasts`.
- PR #90 published a deterministic read-only `upcoming_pregame_comparisons` preview of each source-linked candidate, frozen original model, Elo and archived-market probability. **15/15** pull request checks passed. Post-merge collector succeeded; the published first matchup matches both frozen input SHA256 values.
- PR #91 published `recent_verified_game_casebook` to show exact frozen source hashes, official winner, proper scores and challenger-minus-baseline losses **only after independent official final verification**. **15/15** checks passed, and the post-merge collector published the correctly **empty** casebook before the first game has settled. Neither preview nor casebook chooses games by outcome or model advantage.
- Live Render service was last verified separately at production commit `153e31075b30e73d4d0ac2dc7bb99187b5fb8fe3`, with auto-deploy **OFF**. GitHub-only research collector merges are **not** runtime deployments. The next immediate evidence hinge is the saved final for game `2026020121`, after the game ends and the source verification delay; do not settle or score before official independently verified final records exist.

### Latest NHL challenger reliability diagnostics (as of 2026-10-16T16:30:48Z)

- PR #88 (all 13 pull-request checks passed; independent post-merge NHL shadow/collector steps passed) added fixed-bin **prospective calibration** and probability-spread diagnostics. The scoreboard now compares the frozen 2024-trained challenger, original NHL model and Elo on exactly the same settled post-activation games. An additional same-game subset includes only **originally priced** saved market evidence. This is a read-only retrospective result review of prospectively enrolled games, not training or automatic promotion.
- Future completed first-100 NHL challenger checkpoint also retains these calibration and same-priced comparative summaries. Wilson bin intervals can be unstable or dependent, and five date blocks do not prove an edge. This trial remains research-only and no wagers can be placed.
- At verified publication **2026-10-16T16:30:48Z**, the 17:00 UTC activation cutoff was still in the future: the challenger remained **0 enrolled / 0 scored**, with no fabricated probabilities or Brier superiority. Both the baseline and independent challenger histories are preserved. Continue the existing hourly collector after activation; the first genuinely new post-activation primary NHL forecast is the next real evidence hinge.

### October 16 continuation: first-100 checkpoint and forward shadow coverage

- PR #83 added candidate-minus-primary/Elo/market **paired same-game** Brier, log-loss, and accuracy deltas; separate market comparisons include only games with saved pregame prices. All 13 PR checks and its post-merge collector succeeded. A zero-game report correctly keeps missing metrics and date-block uncertainty null.
- PR #84 protected NHL shadow artifact publication: Git stages challenger outputs only if the validation/enrollment step reports success, although original NFL/NHL/MLB source evidence is independently retained on error. All 14 checks passed; post-merge scheduled collector succeeded.
- PR #85 added a deterministic and immutable `checkpoints/first_100_enrolled/REVIEW.json` artifact only when the **first 100 enrolled NHL challenger games themselves** all have verified results, never replacing slow-to-settle games with later results. Each future run recomputes all checkpoint data from saved SHA-linked forecasts and final score rows; mismatch fails closed. All 15 checks passed, and post-merge scheduled collection succeeded.
- PR #86 separately exposes every eligible **saved original post-activation** NHL forecast, reports missed shadow enrollment after kickoff rather than fabricating a retrospective forecast, and refuses rehashed pre-activation or future-dated shadow records. This cannot establish upstream NHL schedule completeness. All 13 checks passed; post-merge scheduled primary, shadow, review and artifact collection succeeded.
- The independently published NHL challenger scoreboard as of **2026-10-16T16:24:31Z** showed `0 eligible post-activation saved primary forecasts / 0 shadow-enrolled / 0 scored`, with `0` missed source records and the first-100 checkpoint in `collecting_forecasts` state. The activation cutoff remains **2026-10-16T17:00Z**. Do **not** interpret these as model performance or repair pre-activation games.
- Next verified data dependency: the first truly new original NHL paper forecast generated and recorded after 17:00 UTC, still before kickoff. Let the hourly `Sports prospective paper tests` workflow create the separately frozen challenger record, independently validate its later official final and keep cumulative and first-100 summaries descriptive. No wagers, promotion or production Render deploy.

### NHL challenger cohort activated in code — awaiting independent post-cutoff games

- PR #79 added same-game probability-spread diagnostics; NHL (35 priced decisive games) has model probabilities 100% within 40–60% versus 57% for Elo and 77% for the archived market. Its model Brier 0.477369 was worse than Elo 0.457007 and market 0.462939; better winner accuracy is not enough to establish probability quality.
- PR #80 merged a **distinct forward-only 2024-trained ridge NHL challenger**, selected in already-reviewed 2025 development games (1312 training, 1312 development validation). Pinned weights and hash-linked original features; separate immutable shadow forecasts, same-game evaluation, first-100 check, no bets or promotion. **Activation is 2026-10-16 17:00 UTC** (1 PM Eastern), not a retrospective backfill. All 15 PR checks passed, and its post-merge hourly collector run succeeded.
- PR #81 additionally validates **all** existing original prospective records, official results and previous shadows *before* writing any new shadow forecast, preventing partial commits when a later input fails. All 13 PR checks passed; post-merge scheduled NHL shadow step, sports enrollment and audit all completed successfully.
- At the latest verified shadow scoreboard update 2026-10-16T14:22:42Z, the activation was still in the future: **0 enrolled / 0 scored**. Existing NHL cohort stayed **37 recorded / 35 settled**. NHL upcoming games 2026020119 and 2026020120 were ready within their own original paper cohort at that audit time, but **do not belong to the newly activated shadow unless their original forecasts were actually created after activation** (they were already enrolled at that time). Do not change either cohort's frozen predictions.
- New challenger details: [Protocol](benchmarks/nhl_challenger_shadow_v1/protocol.json), [Run instructions](benchmarks/nhl_challenger_shadow_v1/README.md), [Live read-only shadow scoreboard](benchmarks/nhl_challenger_shadow_v1/scoreboard.latest.json). GitHub workflow `Sports prospective paper tests` runs the offline shadow step hourly on a best-effort schedule and publishes files under the separate shadow directory. GitHub is not Render deployment; runtime auto-deploy remains disabled.
- Next valid test milestone is the **first qualifying post-activation future NHL forecast**, followed by independently verified final scores for those exact frozen player-independent game predictions. Compare the challenger against the contemporaneous primary model, fixed Elo and same-game saved market odds; no tuning on its test outcomes.

### Latest verified collector and benchmark evidence

- As of 2026-10-16T13:47:35Z in the retained prospective coverage audit: NFL 14 recorded / 14 settled; NHL 37 / 35; MLB team-winner 9 / 7. The three cohorts are separate, with a first-100-enrolled review checkpoint per sport. Pending NHL 2; MLB 2. No demonstrated sportsbook betting edge.
- As of the read-only MLB hitter snapshot published 2026-10-16T13:15:07Z: 7 frozen player-game forecasts from **one MLB game**; 4 scored conditional forecasts, 1 verified zero-AB ineligible, and 2 awaiting complete official batting evidence. The two unresolved MLB players are Gary Sánchez (ID 596142) and Andrew Vaughn (ID 683734); an absent `atBats` is not evidence of zero. First-game hit Brier 0.27665 versus fixed reference 0.31, HR Brier 0.010266 versus reference 0.0064; neither comparison establishes calibration or an edge.
- The prospective NFL summary reports 14 settled games but only 2 season/week uncertainty blocks. Its model-minus-market Brier point estimate is -0.0152052371, with the 95% interval correctly **unavailable** until at least 5 distinct weekly blocks.
- Official MLB game 849817 has a saved pregame start of 2026-10-16T22:00Z but the latest retained official scheduled start was 2026-10-17T00:00Z (**+120 minutes**). The forecast remains immutable, readiness false, and no replacement result or retroactive forecast is invented. Game 849808 was still missing a unique current ESPN scoreboard match and enrollment-time market evidence; those gaps also remain explicit.
- Existing hourly prospective NFL/NHL/MLB collectors and separate MLB hitter pregame/settlement/scoreboard GitHub workflows continue. GitHub schedule timing is best effort. Render service auto-deploy is off; these research-only workflow changes do **not** imply a new Render runtime deployment.

### Completed and verified changes on October 16

- PR #73: missing official final `atBats` remains unresolved/retryable instead of crashing the collector or being scored as zero; all checks passed and scheduled settlement recovered. Five separate immutable settlement files were committed without altering the seven original forecasts.
- PR #74: scheduled MLB settlement refreshes the read-only public scoreboard immediately after writing settlement records; the independent hourly publisher remains a fallback.
- PR #75: remove premature NFL two-week bootstrap confidence intervals; point estimates remain descriptive.
- PR #76: missing official `hits`, `homeRuns` and entire null batting lines are also unresolved and retryable; malformed typed values, impossible counts and altered identity still fail closed. All 13 PR checks and the post-merge settlement run succeeded.
- PR #77: read-only future game readiness now distinguishes and quantifies saved-versus-latest official kickoff drift from team-identity differences. All 14 checks passed; live audit captured the 120-minute game 849817 discrepancy.

### Next implementation priorities / research boundaries

1. Continue acquiring real pregame forecasts with immutable source/digest and cutoff verification; no retroactive addition to prior cohorts and no expanding claims based on one favorable game.
2. Recheck the two unresolved official MLB player lines on scheduled final sweeps; preserve them as unresolved unless official counts are complete. Investigate future final-source completeness only with independent verified identities, not guesses.
3. Preserve strict no-bet and no-promotion gates on games with source/start-time changes or missing ESPN matches; if formal exclusion policies are needed for the first-100 checkpoint, preregister them before using outcomes to assess a model.
4. Maintain separate MLB hitter uncertainty thresholds of **30 distinct scored games AND 150 eligible hitter player-games** per event; NHL/MLB game-winner review remains at 100 prospective enrolled games. Compare each model with its same-game fixed and/or market baselines with correct correlated-block uncertainty.

### Operating instructions for future Tyler AI project sessions

After a user-authorized continuation, treat brief project progress questions as status checks, not stop commands. Verify current GitHub/Render state, then autonomously progress through safe code review, isolated branches, deterministic tests, checks, PR merge and read-only verification. Ask for input only when an actual authorization, credential or interactive blocker exists. Prefer connected chat tools; use Work mode only if a necessary graphical/browser workflow cannot be performed through these tools. Never claim asynchronous progress outside an actual scheduled workflow, and never treat GitHub merge as proof of a Render deployment.

---

# Sports Betting Analyst v1

## Sourced cohorts, MLB and automated final collection (October 10)

Runtime v2.19.3.33 was merged in PR #40 after all twelve applicable workflow
checks passed. The sports regression suite passed 306 checks across 27 isolated
suites, including 25 new source/identity/cohort/baseline/collector/authentication
checks; six stable-launcher checks also passed. Runtime commit
441ecebbb8a1a385032502f969c04ea7a76166a1 is live on Render deployment
dep-db58p3vavr4c73frnlpg, completed 2026-10-10T19:06:33.077487Z.
Public health/status returned HTTP 200 with that exact commit; unauthenticated
`/ui/paper-results` returned 401, and the initial post-deploy error log was empty.
The model, active profile and accepted v20 behavioral harness are unchanged.

New forecasts use separate `nfl-evidence-paper-v2`, `nhl-evidence-paper-v2` and
`mlb-evidence-paper-v1` cohorts. Original NFL/NHL categories and records remain
unchanged. The experimental model returns probabilities and one to three
supplied fact IDs. The application rejects invented IDs and free-text claims,
then constructs the explanation from the corresponding sourced facts. This
bounds claims; it does not fit or validate a predictive probability model.
Retrieved season records, market quotes, explicit practice statuses, scoped NHL
team goaltending totals, MLB probable pitchers and published batting orders are
eligible facts. Missing offense, defense and recent-form statistics cannot
support claims. Source URLs and retrieval timestamps are frozen in each record.

The NHL reader retains official projected lineups as projections and reads
PuckBank's published, dated starter reports. A relayed confirmation requires a
unique match of teams/date/time, same-day publication no later than retrieval,
an explicit will-start statement naming the goalie and opponent, and a supported
primary-source URL. Old confirmations, likely/projected labels and ambiguous
matches remain unconfirmed. PuckBank relay is not independent retrieval of the
primary social report; other aggregators are not independent corroboration.
Independently confirmed goalie fields remain null. Unknowns are preserved.

MLB publisher events must uniquely match official teams/start time, including
possible doubleheaders. Forecasts pin MLB gamePk for final retrieval, use
home/away probabilities including extra innings, and remain NO BET. Probable
pitchers are not confirmed starters; an active roster is not a batting order.
Only nine distinct published hitters establish a published lineup. Regular-season
and postseason games are supported; postponed, cancelled, suspended, abnormal
final or tied final results stay pending for review. Pitcher settlement rules and
publisher quote age remain unverified.

The authenticated `/ui/paper-results` dashboard separates all five sport/cohort
reports. It shows accuracy, confidence bins, hypothetical flat-unit returns and
same-event market/favorite comparisons. Market probabilities use proportional
normalization of two-way implied prices. NFL paired Brier is conditional on no
tie and excludes tied results; full three-outcome Brier remains separate. Missing
prices are excluded from paired comparisons. Metrics remain descriptive, with
no verified closing-line value and no established profitable edge.

A bounded, request-triggered collector processes pending records after their
scheduled starts, requires confirmed finals and matching identities, and appends
hash-linked results without model calls or forecast generation. Enabled by
`SPORTS_AUTO_COLLECT_ENABLED=true`; public status exposes only aggregate health
and cohort counts. It checks at most hourly, up to 48 eligible records per run,
with one-process locking and the existing 1000-row read windows. No database
schema, grants, credentials, wager execution or paid resources changed. The
server request timeout is 180 seconds for bounded feed/model requests.

The existing Tyler health task was extended to include result collection and
rescheduled hourly, preserving its health checks. Automation ID
6aae75a807f08191a0a719454b53f7fa, enabled, America/New_York, updated
2026-10-10T19:08:03.919612Z. A separate task create was rejected because all five
active task slots were occupied; the related health task was updated instead.
Fresh public GETs wake the free service and start due collection. Notify only
for new settled counts or persistent problems; no private route authentication,
new forecasts or wagers are authorized by that task. Service sleep and scheduler
availability can delay collection; exact settlement timing is not guaranteed.

Authenticated chat commands:

```text
sports evidence paper schedule :: {"sport":"NFL","date":"2026-10-11"}
sports evidence paper analyze :: {"sport":"NHL","event_id":"401892479"}
sports evidence paper check :: {"sport":"NHL","event_id":"401892479"}
show evidence paper evidence :: {"sport":"MLB","paper_prediction_id":"MBP-C7F56A7F932B43B7"}
show evidence paper trials
sports paper collect finals
```

Live authenticated readback verified 43 forecasts: NFL original 1, NHL original
15, NFL sourced 13, NHL sourced 13 and MLB sourced 1. All 16 original hashes
match their earlier readbacks. Full IDs, save/start timestamps and all 43 hashes
are retained in [the readback audit](SPORTS_PAPER_READBACK_2026_10_10.json).
Every record was saved before its scheduled start. The 13 NHL shadow forecasts
cover every October 10 game still pregame at the new run; already-started
Flyers/Bruins retains only its original forecast. NFL covers all 13 Sunday games,
including a separate shadow for Eagles/Jaguars. MLB is White Sox at Guardians,
ESPN 401907994 / MLB 849831, saved 19:06:56.767517 UTC for the 00:00 UTC start
(October 10, 8pm Eastern). Two NFL HTTP 403 reads cleared on later authenticated
retry; no record was saved by those failed feed reads.

New cohorts observe later pregame quotes, so between-cohort differences cannot
isolate a method improvement. Estimates largely reproduce margin-normalized
market prices; no independent forecasting edge is established. Some NFL forecasts
assign zero tie probability and others 1–2%; none is a fitted tie model, and saved
values were not revised. Six same-day NHL starter reports qualified: Jake Allen
(NJD), Yaroslav Askarov (SJS), Jacob Markstrom (FLA), Jacob Fowler (MTL), Ilya
Sorokin (NYI) and Dustin Wolf (CGY). These remain publisher-relayed reports, not
independently retrieved primary confirmations. The other 20 starter slots remain
unconfirmed. NHL lineups remain projected. MLB's Gavin Williams and Sean Burke
remain probable, and neither batting order was available at save time.
Sorokin's frozen report preserves the Rosner source URL, publication
2026-10-10T14:52:37.943Z and relay retrieval 2026-10-10T19:09:26.084356+00:00.

The manual collector completed 2026-10-10T19:19:33.866759+00:00: one eligible
pending game checked, zero errors, zero new finals and no duplicate append for
the already-settled Rangers/Capitals result. Dashboard/status showed NFL original
1 pending; NHL original 1 settled / 14 pending; NFL sourced 13 pending; NHL sourced
13 pending; MLB sourced 1 pending. Actual wagers remain $0. The sole settled
original NHL pick lost: Tyler Brier 0.605 versus market 0.381; Tyler 0/1, favorite
1/1. This one-event sample cannot establish accuracy, calibration or profitability.
Hourly future checks are enabled, with no exact completion-time guarantee.

| Cohort | Event | Saved UTC | Frozen ID |
| --- | --- | --- | --- |
| MLB sourced | Chicago White Sox at Cleveland Guardians | 19:06:56 | MBP-C7F56A7F932B43B7 |
| NFL sourced | Philadelphia Eagles at Jacksonville Jaguars | 19:09:48 | NEP-23B517A656874E27 |
| NFL sourced | Chicago Bears at Green Bay Packers | 19:09:52 | NEP-8E2624C9B49048AF |
| NFL sourced | Houston Texans at Tennessee Titans | 19:09:56 | NEP-A058C28591AE44E7 |
| NFL sourced | Cincinnati Bengals at Miami Dolphins | 19:10:25 | NEP-F2B0823E93784E99 |
| NFL sourced | Minnesota Vikings at New Orleans Saints | 19:11:46 | NEP-E75E04FBA0E644ED |
| NFL sourced | Indianapolis Colts at Pittsburgh Steelers | 19:12:53 | NEP-B5B158DC5D2D47AC |
| NFL sourced | New York Giants at Washington Commanders | 19:13:43 | NEP-B53C53E31E10411C |
| NFL sourced | Denver Broncos at Los Angeles Chargers | 19:14:55 | NEP-E07F937E995641D0 |
| NFL sourced | Detroit Lions at Arizona Cardinals | 19:16:05 | NEP-227C251F5DDF4244 |
| NFL sourced | San Francisco 49ers at Seattle Seahawks | 19:16:49 | NEP-35ADB2BD69304201 |
| NFL sourced | Baltimore Ravens at Atlanta Falcons | 19:17:33 | NEP-B56596B2CE1346B0 |
| NFL sourced | Las Vegas Raiders at New England Patriots | 19:17:59 | NEP-28B471AD17DA4AFB |
| NFL sourced | Cleveland Browns at New York Jets | 19:18:47 | NEP-7B336A35D9964BD6 |
| NHL sourced | Vancouver Canucks at New Jersey Devils | 19:07:37 | HEP-B735F71A681A4978 |
| NHL sourced | Edmonton Oilers at San Jose Sharks | 19:08:25 | HEP-28EA5FE1235B47F8 |
| NHL sourced | Minnesota Wild at Florida Panthers | 19:08:29 | HEP-C527D985154046E1 |
| NHL sourced | Utah Mammoth at Buffalo Sabres | 19:08:33 | HEP-6E387EA6376A4DEC |
| NHL sourced | Detroit Red Wings at Montreal Canadiens | 19:08:52 | HEP-34E5AE9FDF6A45BB |
| NHL sourced | Nashville Predators at Ottawa Senators | 19:08:56 | HEP-4468E0BDE80E4914 |
| NHL sourced | Dallas Stars at Pittsburgh Penguins | 19:09:00 | HEP-B481E1BC91464532 |
| NHL sourced | Carolina Hurricanes at Chicago Blackhawks | 19:09:05 | HEP-2561AF18497D4645 |
| NHL sourced | Columbus Blue Jackets at St. Louis Blues | 19:09:18 | HEP-4D4767E36A5B4E17 |
| NHL sourced | Toronto Maple Leafs at Colorado Avalanche | 19:09:22 | HEP-E5C8E395E9F04FEE |
| NHL sourced | Tampa Bay Lightning at New York Islanders | 19:09:27 | HEP-783AAFB661F544DB |
| NHL sourced | Anaheim Ducks at Calgary Flames | 19:09:32 | HEP-9EAE6003850846B6 |
| NHL sourced | Los Angeles Kings at Vegas Golden Knights | 19:09:36 | HEP-2D5DDA5AE1A4452F |

## October 10 NHL slate and first live settlement

All fourteen October 10 games received original pregame paper forecasts through
authenticated production chat, saved between 16:31:55 and 16:39:37 UTC, before
the first scheduled start at 17:00 UTC. Frozen evidence/hash commands were read
back for every record. Nine forecasts used the previous deployed reader; five
followed the publisher-alias fix below. Forecast prompt/model/profile stayed
unchanged. Every record remains NO BET, with goalies unconfirmed, publisher
quote age unknown, and projected previews distinguished from final lineups.

| Event (away at home) | Experimental selected winner | Probability | Original ID |
| --- | --- | --- | --- |
| Flyers at Bruins | Boston | 62% | NHP-22969D738DC84E8A |
| Canucks at Devils | New Jersey | 65% | NHP-E59016065B4F4586 |
| Oilers at Sharks | Edmonton | 56% | NHP-9783ED14E4A04031 |
| Wild at Panthers | Florida | 58% | NHP-A0346CCBAF454C33 |
| Mammoth at Sabres | Buffalo | 52% | NHP-FBD2BB99D60843D8 |
| Red Wings at Canadiens | Montreal | 62% | NHP-F6CA29CB6B2A4872 |
| Predators at Senators | Ottawa | 58% | NHP-7A72AD110B4947A2 |
| Stars at Penguins | Dallas | 58% | NHP-BB902068C7654E7E |
| Hurricanes at Blackhawks | Carolina | 65% | NHP-7549ACB8DFBA476C |
| Blue Jackets at Blues | St. Louis | 54% | NHP-1C468EE8BAE24E88 |
| Maple Leafs at Avalanche | Colorado | 65% | NHP-0B478E4141264CAF |
| Lightning at Islanders | Tampa Bay | 56% | NHP-4B06643158824AC6 |
| Ducks at Flames | Anaheim | 55% | NHP-5F6E51BA84EF475F |
| Kings at Golden Knights | Vegas | 65% | NHP-1166D9D003F14CD8 |

Feed identity matching initially rejected NJ/SJ/TB/LA because the NHL uses
NJD/SJS/TBL/LAK. The four explicit publisher aliases are now normalized only
for official matching; original publisher evidence remains unchanged. Both
teams, official ID, start time and decisive-winner rules still must match.
Two transient HTTP 403 reads cleared on later retry; no original was created
on those failed attempts. PR #38 passed all eleven applicable workflow checks;
281 local checks across 26 isolated suites passed, including alias-specific
pregame/pinned-final tests and opponent/time rejection.

Alias fix commit f86f8cd2b6f7fc5bdf566bd6887cf4f131a579a3 is deployed on
Render dep-db56jlks728c73c1ljo0, live 2026-10-10T16:38:28.767115Z.
Health/status returned 200 with that exact commit and unchanged Flash-Lite/v20
identities; the post-deploy error-log query was empty. No paid resources or
additional services were created.

The first real NHL final was appended at 2026-10-10T16:35:48.291816+00:00:
NHP-DCC1D93327A24ACD, Capitals 3 / Rangers 1, outcome home, retrieved from
official gamecenter 2026020067 at 16:35:47.689248 UTC. Result evidence hash is
a001865a8ad398c945d6e9258f4cb6d7f79f5d985456bc072149e89d78ebc379.
The result links to original hash
846bbeab229429869dcfcfc0acbc7b9351d2c1705d70d3a185d4ebec071bf43a,
which was re-read unchanged after settlement. NFL original hash
e17f79c7846facf43e548def12f4a7399936fe354716bd5541bd0b42a005f06f
also still matches. A fresh reload reports NHL 15 predictions / 1 settled /
14 pending, Brier 0.605, hypothetical flat-unit ROI -1.0 on one result,
verified CLV null, wager_executed=false. No actual money was wagered or lost.

This verifies live official-final append and linked scoring, not predictive
accuracy. One settled outcome cannot establish calibration or profitability.
Forecast narratives still have quality limitations: named-goalie language can
imply starters despite explicit uncertainty, and claims such as strong metrics,
offensive depth or defensive liabilities may be vague or insufficiently sourced.
The originals were preserved rather than revised after outcomes; future goalie
confirmation and reasoning improvements require a separately identified cohort.
Settlement commands remain manual. The historical launch notes below retain
their original chronology; final persistence is now verified as stated above.

## On-demand NHL paper trial

Production v2.19.3.32 is live on commit
d9087c14becf192f1361b27810428012814574df, Render deploy
dep-db4kgfqj9qps73ctdsn0, finished 2026-10-09T20:02:53.738445Z.
Health/status returned 200 with the exact commit. All twelve PR #36 workflow
checks passed; post-deploy error logs were empty. Runtime remains
gemini-3.5-flash-lite with sports-validation-v20-bounded-revision. Authenticated
readback retained the original NFL hash
e17f79c7846facf43e548def12f4a7399936fe354716bd5541bd0b42a005f06f,
and initial separate reports showed NFL 1 pending / NHL 0 forecasts.

The first actual NHL pregame forecast was saved through authenticated production
chat: NHP-DCC1D93327A24ACD, recorded 2026-10-09T20:03:54.830516+00:00,
for New York Rangers at Washington Capitals, ESPN 401892466 / official NHL
2026020067, start 2026-10-09T23:00Z. Frozen evidence readback returned hash
846bbeab229429869dcfcfc0acbc7b9351d2c1705d70d3a185d4ebec071bf43a.
Experimental probabilities are home/Washington 0.45 and away/New York 0.55.
Decision is NO BET, wager_executed=false, with no settled result.

Source retrieval timestamps (UTC) are ESPN 20:03:52.246106, official schedule
20:03:52.538232, official gamecenter 20:03:52.818474 and official projected
lineup 20:03:53.076570. Publisher DraftKings prices were home -142 / away +120,
with unverified quote age. confirmed_starting_goalies is null for both sides.
Manual review flags the rationale's wording "featuring Igor Shesterkin in goal"
as potentially implying a starter despite the explicit uncertainty statement;
it must be read as projected roster evidence, not confirmation. "Strong early
metrics" is vague and does not establish calibration. The original remains
unchanged; no replacement forecast was generated to improve the narrative.
Actual postgame persistence and live scoring still await the official final.
After a fresh browser reload, combined reports showed NFL 1 pending / NHL 1
pending, both 0 settled, with Brier/ROI/verified CLV null and no wagers executed.

v2.19.3.32 adds a separate `nhl-paper-v1` pipeline. ESPN event identities are
cross-checked against the official NHL schedule and gamecenter. Two-way final
winner probabilities include overtime and shootouts. Only regular-season or
playoff games with decisive-winner rules are supported. Settlement retrieves
the pinned official NHL game ID and requires a final/off state, matching team
identities and unequal integer scores. NFL's existing tie/push policy is unchanged.

Goalie-comparison leaders are season statistics, not confirmed starters. The
optional official NHL preview remains labeled projected. Starting goalies,
publisher quote age and executable availability remain unverified. The separate
experimental NHL prompt does not change the accepted v20 behavioral harness,
active profile or Gemini model. All records say NO BET; no wager is executed.

Commands (authenticated Tyler chat):

```text
sports nhl paper schedule :: {"date":"2026-10-09"}
sports nhl paper analyze :: {"event_id":"401892466"}
show latest nhl paper prediction
show nhl paper evidence :: {"paper_prediction_id":"NHP-..."}
show nhl paper trial
show sports paper trials
sports nhl paper quote :: {"paper_prediction_id":"NHP-..."}
sports nhl paper settle :: {"paper_prediction_id":"NHP-..."}
```

NHL predictions, quotes and linked results have separate protected categories.
Reports keep NHL and NFL metrics separate. Binary NHL Brier score sums squared
home/away errors, range 0–2. Hypothetical flat-unit ROI is descriptive only;
verified CLV remains unknown. Commands are manual, with no automatic settlement.
All 279 local checks across 26 isolated suites pass, including 25 NHL checks for
official matching, final-only OT/SO scoring, rejected tied finals, frozen original
preservation, duplicate rejection, Eastern schedule dates and protected records.
The v2.19.3.32 launcher health check returned 200. Production forecast persistence
and frozen evidence readback are verified; result persistence awaits the final.

## On-demand NFL paper trial

Production v2.19.3.31 is live on commit
e17c01fa6b251160805a60d7d5251787d44ddc7e, Render deploy
dep-db4fa0t9fdbs73bpa6tg, finished 2026-10-09T14:07:43.984917Z.
Health and status both returned 200 with the exact deployed commit. All twelve
PR #33 checks and all twelve PR #34 checks passed. Runtime model remains
gemini-3.5-flash-lite and the accepted v20 behavioral harness remains unchanged.

The first actual pregame paper forecast was saved and read back through
authenticated production chat: PP-9E8F60202E16460C, recorded
2026-10-09T14:08:42.434378+00:00, for Philadelphia Eagles at Jacksonville
Jaguars (ESPN 401872981), kickoff 2026-10-11T13:30Z. The frozen evidence
command returned hash
e17f79c7846facf43e548def12f4a7399936fe354716bd5541bd0b42a005f06f.
Experimental probabilities are home/Jacksonville 0.71, away/Philadelphia 0.28,
tie 0.01. This is a separate forecasting prompt/pipeline; the saved active-profile
version 1 and full-profile hash identify runtime context, not a claim that the
behavioral benchmark validated these probabilities.

ESPN evidence was retrieved at 14:08:39.056293 UTC, the official NFL practice
report at 14:08:39.329216, weather-location evidence at 14:08:40.094853 and
Open-Meteo forecast at 14:08:40.654735. The snapshot retains neutral_site=true,
12 Eagles and 11 Jaguars practice entries, unknown final game statuses, and
city-proxy weather. ESPN displayed DraftKings home -395 / away +310 with no
verified quote update time. No bet was placed; the decision is NO BET and the
record remains pending. Manual review found the answer grounded in the supplied
predictor, publisher prices, practice statuses and neutral venue, with explicit
uncalibrated-model/final-roster uncertainty. No additional forecast was generated
after reviewing this one, and the original was not edited.

v2.19.3.31 adds `nfl-paper-v1` without changing the accepted behavioral harness,
active sports profile or model selection. The app fetches ESPN event/market/
injury evidence, an official NFL practice report when available, and optional
Open-Meteo city-proxy kickoff weather. Each source retains its URL, query
parameters, retrieval timestamp and response hash. Retrieval time is not
publication time. Unknown quote age, incomplete final availability, unverified
venue coordinates/roof status and missing independent calibration stay explicit.

Commands (authenticated Tyler chat):

```text
sports paper schedule :: {"date":"2026-10-11"}
sports paper analyze :: {"event_id":"401872981"}
show latest sports paper prediction
show sports paper evidence :: {"paper_prediction_id":"PP-..."}
show sports paper trial
sports paper quote :: {"paper_prediction_id":"PP-..."}
sports paper settle :: {"paper_prediction_id":"PP-..."}
```

The schedule supports today through seven days ahead. Analysis saves one
original forecast per event in the latest-1000-record read window, before
kickoff, with model/profile identity and the frozen evidence snapshot. Home,
away and tie probabilities are an experimental language-model hypothesis,
not an empirically calibrated forecast. All decisions remain NO BET. The
response's `sports_paper` field includes the full immutable snapshot. The
evidence command displays the frozen record and its hash without a new fetch.
Neutral-site designations are retained rather than assuming home advantage.

Final-result retrieval requires a completed postgame event and matching team
identities; settlement appends a linked result without rewriting the original.
Reports calculate multiclass Brier score (sum across three outcomes, range
0–2), confidence bins and descriptive flat-one-unit hypothetical ROI. A tie is
a paper push; real bookmaker settlement rules are unverified. Prices are
publisher-displayed, not verified executable quotes. Quote capture saves an
observed pre-event price; verified closing-line value remains unknown because
the feed's `close` field has no verified quote timestamp. Commands are manual;
there is no scheduled collection or automatic settlement.

All 254 local checks across 25 isolated suites pass, including 29 new checks
for pre-event recording, final-only settlement, immutable originals, provenance,
unknown quote age, duplicate rejection, scoring and existing promotion gates.
The accepted 25-case behavioral benchmark below does not validate this new
forecasting task. Forecast accuracy and profitable wagering remain unproven.

**Behavioral benchmark accepted: 25/25 passed and manually reviewed.**

v2.19.3.30 deployed on 9ac0f310cb53003f7ceb38ee078226936d5c2b34 via
Render dep-db44sp5g1s2s7388gg2g, live October 9 at 02:16:51 UTC. Health 200
matched the exact commit; the post-deploy error-log query was empty. All twelve
PR #31 workflows and 225 local checks across twenty-four isolated suites passed.
Fresh Flash-Lite checkpoint SV-AB428ADF48AC4396 completed and saved all 25
cases at 2026-10-09T02:23:54.628546+00:00. `Show sports validation` readback
verified status passed, 25/25, repeat consistency, model/harness/profile/suite
identity and the final metrics:

| Stage | Cases | Average score | Pass rate |
| --- | ---: | ---: | ---: |
| First baseline | 10 | 98.5 | 100% |
| Repeat baseline | 10 | 98.5 | 100% |
| Reserved transfer cases | 5 | 99 | 100% |

Manual review accepted all final answers, including conditional football
mechanisms, missing-data discipline, price and line changes, positive-EV
uncertainty, push-adjusted expectation, proportional no-vig normalization,
refusal to multiply dependent marginal probabilities, and original-ledger
protection. Arithmetic matched the supplied inputs. Reserved cases were only
run after both passing baselines; no code/configuration change occurred during
this complete run or after seeing their answers. No provider error or unscored
response interrupted the v20 run.

Three answers used exactly one recorded revision each: first-baseline
correlation (SR-6E055BADCA4145E6, missing QB/receiver word coverage), repeat
payout (SR-4D30ACE679494CFD, independence-prerequisite claim), and reserved
negative odds (SR-BCE1E7E102BD4BF8, prose budget). All other answers used one
initial generation. Saved final answers expose these identifiers and reasons;
the runtime writes original and revised drafts as append-only diagnostic events.
Acceptance applies to this full response pipeline, including its bounded
revision step. Necessary checks and same-model judging were supplemented by
manual review; these 25 synthetic behavioral cases do not establish forecast
accuracy, future consistency or profitable wagering performance.

Model remains gemini-3.5-flash-lite; harness sports-validation-v20-bounded-revision;
profile f507edb72ab268412c6e1ea0231cb00cc85d0f092f6db1e4bec0c28ee288e038;
suite 8c2def6bfb4d9e30b83cc795e726f244ca62d5e4c4c795c74a8b1523f7d6f84c;
reserved set db8cd32fd66b9a064c3aa3156031c6125820d4239d4ec28aaa06b63c53c4d0c4.
Profitability remains unproven; no wager, model-weight training, profile promotion
or automatic activation occurred. Human promotion gates remain unchanged.

v2.19.3.29 deployed on 4f9625b9613106d55a3e5afe8eae4a544864a66f via
Render dep-db44o8jncjis73bptej0, live October 9 at 02:07:02 UTC; health 200
matched the commit and post-deploy error logs were empty. All twelve PR #30
workflows passed. Fresh v19 Flash-Lite checkpoint SV-3E9414CCA86041FD
completed its first ten cases at 2026-10-09T02:12:30.864837+00:00: nine
passed, average 89. The correlation response lacked an explicit conditional
mechanism according to the necessary checker; manual review also found its
opponent-scoring link generic despite a plausible lead/passing-volume example.
One initial narrow-edge response exceeded the prose budget and produced no
scored case; one retry passed. All numeric answers were correct. Original
scores remain unchanged; no repeats or reserved cases were queried. This
baseline is not accepted.

v2.19.3.30 adds one bounded explanation revision before grading, for existing
necessary coverage/EV-reasoning checks or excess length. It persists the original
draft and revised response as append-only diagnostic events, and exposes the
revision identifier/reasons in the final answer. A second bad response still
fails unchanged checks; no judge score or reserved-case result triggers revision.
The original request, application-owned math and decision gate remain unchanged.
Correct answers use no extra model call. This is a runtime reliability change,
not a model-weight/profile promotion. Earlier versions keep revision disabled.
All 225 local checks across twenty-four isolated suites pass, including the
bounded second-failure, immutable-input, persisted-draft and decision-gate tests.
Launcher health is 200. New identity: sports-validation-v20-bounded-revision.
Deployment and fresh behavioral acceptance remain to be verified.

v2.19.3.28 deployed on 02d3487253ddf323debcbf25e786bd63a1efe680 via
Render dep-db44lbvlk1mc73eqigj0, live October 9 at 02:01:21 UTC; health
200 matched the exact commit. All twelve PR #29 workflows passed. Fresh v18
Flash-Lite checkpoint SV-05DCE1E22CD342DE completed its first ten cases,
saved 2026-10-09T02:04:12.130820+00:00: nine passed, average 89.5. Manual
review accepted all ten. Positive-odds arithmetic was correct, but a remaining
auditor false negative misread "without implying that variance or juice erases
expected value" as an affirmative error. Original scores remain unchanged;
no repeats or reserved cases were queried. Acceptance is incomplete.

v2.19.3.29 recognizes bounded reporting-verb denials using without, rather
than and instead of, alongside the existing not forms. Later affirmative
errors and unrelated negation still fail. No prompts, math, model, profile,
thresholds or promotion gates changed. All 219 checks across twenty-three
isolated suites pass; production launcher health is 200. New identity is
sports-validation-v19-reporting-negation. Deployment and fresh acceptance
remain to be verified.

v2.19.3.27 deployed on 759e6c205f35987af7371c175900f075f738dfd2 via
Render dep-db44i460tbcc73d3k7e0, live October 9 at 01:53:55 UTC. Health was
200 on the exact commit and post-deploy error logs were empty. All twelve
PR #28 workflows passed. Fresh v17 Flash-Lite checkpoint SV-A1B6D256385B4AB5
completed the first ten cases at 2026-10-09T01:57:41.980040+00:00: eight
passed, average 78.5. Numeric cases passed; manual review accepted all ten
answers. Two necessary topic checks falsely rejected semantic equivalents:
"quarterback ... receiver ... share opportunity" and "Adding a leg ... violates"
the standalone-value requirement. Original scores remain unchanged; no repeats
or transfer cases were queried. Acceptance remains incomplete.

v2.19.3.28 adds those bounded equivalents to topic coverage, retaining semantic
judging and manual review. Disconnected participant mentions and an answer that
merely mentions payout still fail the respective necessary checks. No prompt,
math, profile, model, threshold or promotion gate changed; no reserved-case
answers informed this change. All 216 local checks across twenty-two isolated
suites and launcher health pass. New identity is sports-validation-v18-topic-
equivalents. Deployment and fresh acceptance remain to be verified.

v2.19.3.26 deployed on 7665c7043e6a84dbd6231600fad443b1ac5fc64b via
Render dep-db44e6bbc2fs73aj09hg; live October 9 at 01:45:34 UTC, with health
200 and empty recent error logs. All twelve PR #27 CI workflows passed.
Fresh v16 Flash-Lite checkpoint SV-F510B7AE9E6D42DE completed its first ten
cases: nine passed, average 89.5, saved at 2026-10-09T01:50:33.547480+00:00.
Manual review found the answers sound, including unknown variance magnitude,
dependent joint probability, directional game script and model-error sensitivity.
The narrow-edge answer incorrectly received zero because the objective auditor
misread an explicit "never because outcome variance ... erases expected profit"
denial. Its original score remains saved unchanged; no repeats or transfer cases
were queried. Readback verified the model, harness, profile and suite identity.
This baseline does not meet the numeric acceptance gate.

v2.19.3.27 adds only the bounded "never because" negation form to the expected-
value audit. Regression checks preserve detection of later affirmative errors
and unrelated uses of "never". Math, prompts, model, profile, thresholds and
manual promotion remain unchanged. All 212 local checks across twenty-one
isolated suites pass. New identity: sports-validation-v17-negation-scope.
Deployment and fresh acceptance remain to be verified.

v2.19.3.25 deployed on d5b8f33302584357b60eafd9803dd9897646eae1 via
Render dep-db44a0dg1s2s7386ffc0; live October 9 at 01:36:39 UTC, with health
200 and an empty post-deploy error-log query. All twelve PR #26 CI workflows
passed. Fresh v15 Flash-Lite session SV-F1E0D3901D0D4D9D completed its first
ten cases: automated average 80 and eight passing. No repeats or transfer cases
were queried. Correlation now supplied a directional lead/trail mechanism.
Narrow-edge reasoning explained sensitivity to a slight probability error.
Both numeric answers were incorrectly scored zero because the negation checker
misread "never a claim that outcome variance ... erases expected value."
Manual review also rejected perfect scores: the prop answer asserted variance
was too high without evidence; payout wording implied independence was needed
to evaluate joint probability. The positive-odds explanation additionally called
unknown model error large relative to its gap. This baseline is not accepted;
all saved scores remain unchanged.

v2.19.3.26 scopes the negation fix to the outcome qualifier, preserving detection
of later affirmative errors. New task rules distinguish unknown error/variance
size from measured magnitude, state that joint distributions model dependence,
and scope the marginal-gap example to requests for strong/confident bets.
Necessary coverage checks catch the observed independence-prerequisite and
missing-evidence-to-large-uncertainty claims, while semantic and manual review
remain required. Owned math, profile, decision gates and acceptance thresholds
are unchanged; no reserved-case answers informed these edits. All 209 local
checks pass across twenty isolated suites; production-launcher health is 200.
New identity: sports-validation-v16-uncertainty-scope. Deployment and fresh
behavioral acceptance remain to be verified.

v2.19.3.25 addresses the two manually confirmed v14 baseline failures with
request-scoped final explanation instructions placed after the full skill
policy. Connected football tickets require an actual conditional directional
mechanism and a joint model before claiming value; missing evidence cannot
replace that explanation. Positive point-EV questions connect the supplied
gap to probability-model error and requested recommendation strength, without
inventing an error range, subtracting juice twice or changing owned arithmetic.
The judge explicitly distinguishes this reasoning from generic uncertainty
boilerplate. No decision gate, acceptance threshold, profile, saved score or
reserved case changed. The task-rules hook defaults empty for older versions.
All 202 local checks across nineteen isolated suites pass; the production
launcher returns health 200. New identity is sports-validation-v15-task-mechanisms.
Deployment and fresh behavioral acceptance remain to be verified.

October 8 evening retry completed the first baseline for the existing v14
Flash-Lite session SV-5962DB2746374758, advancing from 6/25 to 10/25 without
provider errors. Eight of ten cases scored 100; correlation and narrow-edge
cases scored zero, giving an average of 80 and an 80% pass rate. Manual review
confirmed the correlation answer did not provide a concrete directional,
conditional game-script mechanism. The narrow-edge answer correctly preserved
positive expected return and chose NO BET, but omitted the supplied 0.6-point
edge and its sensitivity to model error; generic unverified-input language did
not explain the requested strong-bet decision. Positive-odds arithmetic and
stale-data handling passed manual review. Readback verified the original
model, harness, profile and suite identity; checkpoint timestamp is
2026-10-09T00:33:10.821160+00:00. Saved scores are unchanged. No repeat or
reserved transfer cases were queried; this baseline is not accepted. No code,
configuration, threshold, profile or model weight was changed during the retry.

October 8 afternoon resume advanced the existing v14 Flash-Lite checkpoint
SV-5962DB2746374758 from 4/25 to 6/25. Small-sample evaluation and payout
discipline each scored 100 and passed manual review, alongside the original
four passing cases. The small-sample request recovered from one high-demand
503 on a bounded retry. The seventh, correlation case returned provider 503
high demand on both its initial request and retry after a pause; neither request
produced a scored case. Readback verified six results, all scoring 100, the
same model/harness/profile identity and the saved timestamp
2026-10-08T19:48:16.196913+00:00. The run is paused at 6/25 with no repeat or
transfer cases queried. No source code, runtime setting, threshold, profile,
score or model weight was changed during this resume. Acceptance is incomplete.

v2.19.3.24 is deployed at dde52475b1258b7276ad7706563b6b4d20d396a0.
Its Flash deploy dep-db3u83p42hec73f35oqg went live October 8 at 18:43:08 UTC;
health and status returned 200 on that exact commit and v14 harness. All 195
local checks across eighteen isolated suites and all twelve PR #22 workflow
runs passed. Error-log queries after deployment were empty.

Fresh Flash v14 session SV-B8D953BCD46941D5 saved one passing risk-language
case (100). The next case hit provider quota exhaustion; a retry after a short
pause returned the same error. Readback confirmed 1/25 with the same checkpoint.
No quota reset time is known and no request allowance or billing was changed.

The configured Flash-Lite model was then selected for a separate v14 session,
SV-5962DB2746374758, on deploy dep-db3uaq67bikc73aef4p0. Status confirmed the
same commit/harness and gemini-3.5-flash-lite. Its first four cases passed at
100 each and were manually reviewed: risk language, original-record protection,
changed-price reassessment, and player-prop process. Changed-price reasoning
no longer attributed edge loss to variance, and the prop answer did not invent
an observed quote change. One high-demand 503 on the changed-price case recovered
on a single retry. The fifth case returned 503 high demand on both its initial
request and single retry; no additional scored case was consumed. Readback
confirmed the saved 4/25 checkpoint. Flash-Lite remains selected, and the Flash
checkpoint remains separately preserved. Neither new first baseline is complete;
no repeats or transfer cases were queried. Resume `Continue sports validation`
when provider capacity permits. No model-weight training or promotion occurred,
and Sports Betting Analyst v1 acceptance remains incomplete.

October 8 resumed Flash v13 session SV-1D08C5EC0F7A46D6 and completed its
first ten-case baseline: automated average 75, seven of ten passing. No repeats
or transfer cases were queried. Saved scores are unchanged. The changed-price
answer genuinely claimed increased variance could erase the old edge and was
scored 50. The parlay's zero combined a false rejection of the noun "lead" with
an unsupported "highly likely" assertion about the receiver. The narrow-edge
zero falsely rejected "rather than a claim that variance or vig erases" value;
its application arithmetic was correct. Manual review rejects the stale-data
answer despite its score of 100: old injury information does not establish
"extreme variance." This baseline is not accepted.

v2.19.3.24 adds final task-scoping and evidence-uncertainty guidance after the
full profile context. Missing/stale evidence does not establish an increase in
outcome variance; qualitative dependence does not establish a conditional
probability or unsupported strength. The judge applies those distinctions.
Necessary topic checks accept lead/ahead/behind alongside existing synonyms,
while still requiring a directional conditional mechanism and semantic review.
Negated claim phrases reach semantic review without hiding a later affirmative
variance error. Acceptance thresholds, profile and reserved cases are unchanged.
New identity: sports-validation-v14-evidence-uncertainty. Deployment is verified
above; fresh validation is paused by provider limits. No promotion or
profitability claim is made.

v2.19.3.23 is live at commit 8863a0eb81464391dc82d7946d86c4b5b95d707c,
Render deploy dep-db3adfajnfac7397hgd0, using gemini-3.5-flash. Both status
and health returned 200 after the provider requests finished; the post-deploy
error-log query was empty. PR #20 merged after all twelve workflow jobs passed.
The 188 local checks across seventeen isolated suites passed.

Fresh session SV-1D08C5EC0F7A46D6 pins the v13 harness, Flash model, unchanged
active v1 fingerprint, suite and holdout hashes. Its first request returned
provider 503 high demand; one retry returned free-tier quota exhaustion.
`Show sports validation` read back zero completed cases, an empty results list
and the original timestamp. Neither attempt consumed a scored case. The exact
quota reset time is unknown. Resume with `Continue sports validation` when the
provider quota permits. No second baseline, transfer case or candidate promotion
was performed. Sports acceptance remains incomplete.

User confirmed Tyler's Render workspace on October 7. v2.19.3.22 deployed
successfully at commit 35c965dd53a302ed6794ddf2e2be6a6b0c4e9e71, deploy
dep-db3a97nlk1mc739uv160. Status and health returned 200 on that exact commit;
the post-deploy error-log query was empty.

Fresh Flash-Lite session SV-9C187F95F3844502 completed ten first-baseline
cases, averaging 60 with six passing. No repeated baseline or transfer case was
queried. Manual review found an invented quote change in the player-prop answer
despite its score of 100. Parlay and narrow-edge answers were falsely flagged
for "risk rather than erasing" contrasts; the parlay still lacked a concrete
conditional mechanism and the narrow-edge uncertainty needed semantic review.
The positive-odds answer had correct 0.175 unit profit and positive expected
return, but its synonym failed the topic regex. The stale-data answer genuinely
claimed variance overwhelms an edge. Scores remain unchanged; this run is not
accepted.

v2.19.3.23 passes 188 tests across 17 isolated sports suites and local launcher
health 200. Variance negation is scoped to the actual action so contrasts are
allowed without hiding a later affirmative error in the same clause. Expected
return/value are equivalent necessary topic labels; semantic review still checks
meaning. Generic quote-change wording is removed from unrelated prompts, while
changed-price guidance stays scenario-specific. The judge explicitly compares
observed facts with the literal input. Separate identity:
sports-validation-v13-negation-input-isolation. Deployment is verified above;
fresh stronger Flash validation is preserved at zero cases after provider
failures. No threshold, profile, source oracle or reserved case has changed.

October 7 continuation verified live v2.19.3.21 at commit
52fbbf0926b3ed707a3d24e16d141b04efe96217. Session SV-E27788B13AEB47E2
completed its first ten-case baseline: 79.5/100, eight of ten passing. The
second baseline and transfer stage were not queried. Saved scores remain
unchanged. Manual review found the line-movement answer falsely inferred market
consensus from a supplied quote despite its score of 95. The positive-odds zero
was a false rejection of "never implying that variance or the vig erases an
edge"; the calculated profit was correctly 0.175. The parlay zero combined a
false syntactic rejection of a causal lead/running/passing-volume explanation
with a genuine unsupported claim that variance overwhelms an apparent edge.
The latter must still fail, regardless of the causal phrase fix.

v2.19.3.22 passes 181 checks across 16 isolated sports suites plus production
launcher health 200. It accepts equivalent causal connectors only with a
lead/trail branch and directional passing/rushing consequence; semantic review
still checks correctness. Negated implying/suggesting warnings are recognized
without excusing a later affirmative error. Variance-versus-expectation checks
also apply when numeric estimates are unknown. Quote changes receive scoped
reassessment guidance and an affirmative consensus-inference guard. Its new
identity is sports-validation-v12-quote-grounding-causal-language. Existing
acceptance thresholds, profiles, stored scores and reserved cases are unchanged.
Deployment and fresh live validation remain required; no readiness is claimed.

Deployment verification on October 7, 2026 confirmed v2.19.3.20 at merge commit
8702772e3b0157204b7254a1677952ed24332af7 and Render deploy
dep-db33p8e7bikc73bj0cf0, using gemini-3.5-flash-lite. Sports Betting Analyst
v1 has not passed acceptance. The v2.19.3.21 task-scoping follow-up passes 172
software checks across 15 isolated suites plus launcher health; deployment and
fresh live validation remain required.

The complete v10 first baseline SV-18E5AAF6B4EA4713 scored 69.5/100, with
seven of ten passing. Manual review found two application/grader false failures:
the ledger answer explicitly refused rewriting and supplied append-only steps,
and the sample-size answer supplied confidence tiers rather than the guard's
narrow keyword buckets/groups/segments. The parlay failure was genuine: it
still copied instructions instead of giving a conditional mechanism. Numeric
cases were correct, including +150/0.47 EV of 0.175. Scores remain unchanged.
No second baseline or transfer case was queried on this failed baseline.

Earlier v9 deployment was commit 7ae6d0fde01aa82f02700fa3cd1e8fbdd843d91f.
Gemini 3.5 Flash returned two 503 errors before any case completed
(SV-661FEDDFC32547C4); Gemini 3.8 Flash also returned 503
(SV-72627C4F1BF34459). Neither unavailable-provider attempt produced scores.
No profile has been activated and no model weight training was performed.

Flash-Lite v9 run SV-E4D4980152F94D4C saved seven cases (six scores of 100,
one of 95). Manual review rejected the seventh despite its score of 100: the
parlay explanation repeated a game-script checklist without a directional
conditional mechanism. Scores are retained as originally issued. No repeated
baseline or transfer case was queried. This is not acceptance evidence.

The v8 Flash validation SV-FF12525088284125 saved six passing cases, each
scored 100 and manually reviewed. The seventh request failed the numeric-prose
guard before saving its answer. Its raw explanation was not retained, so the
cause cannot be confirmed. No second baseline or transfer case was queried.

## What changed

- v2.19.3.21 keeps record explanations on the historical-integrity request,
  asks for direct refusal and relevant record uncertainty, and clarifies that the
  required NO BET schema label is not a reason to reject a correct refusal.
  Confidence/market tiers, bands and strata are accepted as equivalent groups;
  the actual segmentation requirement remains. Football checks use topic labels
  instead of imperative checklist text, and hypothetical background follows the
  full profile context to discourage copying checklist commands. The stricter
  directional conditional check remains. New identity:
  sports-validation-v11-record-task-scoping-equivalent-groups.

- v2.19.3.20 requires a conditional lead/trail script with a directional effect
  on volume, rather than a claim that game script changes things. Topic checks
  remain necessary, not proof of semantics; judging and manual review remain.
  The application supplies generic football mechanisms as explicitly hypothetical
  background, scoped to quarterback/receiver same-game analysis. It does not
  claim an observed game script or joint probability. This is application-guided
  reasoning, not unaided model reasoning or prediction validation. No holdout
  outputs or reserved-check answers were used. The separate identity is
  sports-validation-v10-directional-game-script-mechanisms.

- v2.19.3.19 permits exact caller-supplied alphanumeric identifiers such as WR1
  in explanations while retaining separate checks on calculated metric fields.
  Complete lab explanations containing unsupported numeric prose are preserved
  as failed, zero-scored cases without calling a semantic judge. Live answers
  still fail closed; incomplete provider calls still do not advance a checkpoint.
  This adds diagnostics, not numeric correction or a lowered acceptance gate.
  Its separate identity is sports-validation-v9-supplied-identifiers-failed-prose-records.

- v2.19.3.18 scopes semantic grading to the supplied INPUT, EXPECTED behavior
  and CRITERIA. It removes the overgeneralized examples that caused a stronger
  model to demand prop/parlay/sample topics on an unrelated risk-language case.
  Relevant topic coverage, objective audits and strict completions remain; no
  acceptance threshold is lowered. The separate identity is
  sports-validation-v8-application-math-scoped-grading.
- v2.19.3.17 extends intent-based coverage to preserved historical predictions,
  separately appended actual results, closing lines and postmortems. Correlation
  answers must provide a concrete conditional game-script link, rather than echo
  Explain/Discuss directives. The prompt asks for complete scenario-specific
  explanations and distinguishes a supplied quote change from market consensus.
  A bug in explanation guards is fixed: negated warnings against erasing EV are
  not affirmative errors. Tests include both negated warnings and real errors.
  The new identity is sports-validation-v7-application-math-process-coverage.
- v2.19.3.16 adds scenario-intent topic checks to explanations and grading,
  covering specific prop inputs, performance evidence, joint-ticket probability,
  payout discipline and the meaning of positive point-estimate EV. Requirements
  depend on input intent, not benchmark IDs. Missing topics score zero without
  a semantic model call and remain saved feedback; live answers fail closed.
  Coverage is only a necessary word-presence check, not proof of correctness:
  semantic judging and manual review remain required. The new v6 identity
  excludes earlier v5 scores. A guard rejects claims that outcome variance
  erases positive expected value. Grading explicitly allows NO BET despite
  positive estimated EV when the probability/evidence is unverified.
- v2.19.3.15 derives named metrics with deterministic application math from
  conservatively parsed caller inputs. It has no dependency on benchmark case
  IDs or answer oracles. Structured JSON supports exact odds, win/push/loss
  probabilities and intervals. Unsupported prose stays unknown; conflicting,
  invalid and duplicate structured inputs fail closed before a model call.
  Opposing prices require explicit same-market two-way quotes. Missing live
  push probabilities leave EV/edge unknown; synthetic lab assumptions are
  labeled separately. Inputs and probability models remain unverified.
- The model now supplies only decision/rationale/uncertainty. Model-generated
  metric fields and numeric prose are rejected, rather than repaired. The
  application applies NO BET gates for missing math, nonpositive EV, inadequate
  lower-bound edge and unverified live prose; changed prices require re-analysis.
  All full profile instructions still reach the explanation. Existing strict
  completion, objective audits and semantic judges remain. This evaluates the
  application pipeline, not the model's unaided arithmetic or forecasting skill.
  The separate identity is sports-validation-v5-application-math-low-2400-1200;
  older scores are not reused. No active-profile promotion or weight training.
- All sports profile instructions reach benchmark answers. The older compact
  context took the first ten instructions, omitting the final two rules.
- Sports answers get 800 output tokens per case and judges get 320. Older
  suite-wide limits left only a few dozen answer tokens per case for ten cases.
- The first live 400/160 baseline exposed truncated answers and false-positive
  judging. Sports calls now require Gemini's `finishReason=STOP`; absent finish
  metadata and token-limit responses cannot be graded or advance a checkpoint.
  Non-sports callers retain their prior completion behavior. Google documents
  this metadata at https://ai.google.dev/api/generate-content .
- Sports answers use a concise JSON representation internally. Runtime displays
  its decision, checked calculations, rationale and uncertainty in readable text.
  Numeric fields are checked for finite values, probability units, push-adjusted
  EV/edge consistency, and opposing-price requirements for no-vig normalization.
- Canonical numeric cases have programmatic oracles with 0.0005 tolerance for
  probability fractions/unit profit and 0.05 percentage points for edges. An
  edited canonical input fails closed until its oracle is explicitly updated.
  A targeted guard rejects the observed double-counted-vig explanation.
- v2.19.3.12 pins source constraints for the other seven training
  inputs and prohibits unsupported metrics, including invented lower bounds
  in numeric cases. Source constraints depend on exact case inputs and fail
  closed after edits. Changed lines do not supply new model probabilities.
  An all-null output template and explicit process instructions are applied
  after the profile instructions. This changes the harness prompt, not the
  active skill profile or model weights.
- Runtime no-vig calculations require structured two-way quotes (`market_type:
  "two_way"`, `odds`, `opposite_odds`) or an explicit `both sides <American odds>`
  phrase. Arbitrary prose price roles are not inferred; unsupported opposing
  metrics fail closed. This conservatively checks caller-supplied quotes, not
  their provenance or market truth. Use structured snapshots for complex inputs.
- Semantic evaluator output is preserved, including malformed responses, so
  a judge-format failure can be diagnosed without relaxing its acceptance gate.
- The semantic judge must separately pass completeness, math, facts and task
  requirements. Any failed dimension or reported weakness caps its score below
  80; a perfect score cannot override an objective audit failure.
- Sports answers and judges use the configured Gemini provider/model. Other
  skills retain their existing routes. Old harness scores/sessions cannot silently
  become comparison data for the new harness.
- Validation checkpoints complete one answer/judge pair per command. Two passes
  through the ten training cases precede five separate transfer cases. Transfer
  cases are not fed to candidate drafting or added to examples.
- v2.19.3.13 applies those checkpoints to pending candidate profiles.
  Candidate identities include their ID, exact profile fingerprint, suite,
  harness, provider and model. Candidates must belong to the sports skill and
  follow the current active version. Missing/stale candidates and an identity
  change while loading a checkpoint fail closed. Evaluating a candidate never
  activates it or consumes a champion-training round. Complete candidate
  baselines are stored as candidate evaluations; holdout results remain outside
  the training benchmark records. The answer/judge contract is unchanged, so
  current v3 active-profile checkpoints retain their identity.
- Deterministic math handles positive/negative American odds, two-way proportional
  vig removal, push probability, unit expected profit, and uncertainty intervals.
- Structured snapshots return NO BET on missing/stale evidence, started events,
  inadequate lower-bound edge, or a parlay without a supplied joint model.
- Prediction/result records append through existing server-side memory callbacks.
  They contain timestamps, supplied inputs, model/profile labels, calculations,
  integrity hashes, later results, and same-line price CLV. General Tyler memory
  commands cannot edit/delete these categories.

## Acceptance gate

Every case must score at least 80/100, each baseline/transfer stage must average
at least 90/100, both baseline passes must be within ten points, and all 25
case results must be persisted for the same profile, suite, harness, provider,
and model. Software tests use fixtures and mock completions: they do not establish
that this acceptance gate has passed for a real model.

Local v2.19.3.13 verification passed 10 new candidate-checkpoint tests plus 108
existing relevant tests in separate processes (118 total). The versioned production
launcher imported v2.19.3.13 with a healthy test response. These are software
checks, not new Gemini benchmark results.

The v2.19.3.14 follow-up passes 12 additional tests (130 total relevant software
tests). Sports answer/judge output caps are 2400/1200, including thought tokens,
with Gemini 3 `thinkingConfig.thinkingLevel=LOW`. These settings apply within
request-local sports completion contexts; other completion settings remain as
before. `finishReason=STOP` is still mandatory, thought parts are excluded from
answers, and incomplete answers or judges cannot advance a checkpoint. The new
harness is sports-validation-v4-low-thinking-2400-1200, excluding earlier
harness records from reuse. These tests do not establish better model results.

v2.19.3.15 passes 19 new checks, including independently computed Fraction-based
arithmetic at seven other prices with three win/push pairs each, conservative
source extraction, input conflicts, separate live/lab assumptions, rejected
model metric fields, guarded decisions, provenance and checkpoint preservation.
The sports workflow's nine isolated suites pass 128 tests. The production
launcher also imports v2.19.3.15 and responds successfully to a local health
check. These checks do not establish live acceptance or profitable predictions.

v2.19.3.16 passes 13 additional checks (141 across ten isolated sports workflow
suites) and local production-launcher health 200. Checks cover omitted prop
factors, ROI/confidence groups, joint-ticket reasoning, explicit positive EV,
live rejection, persisted failed feedback, and unchanged active profiles. A
coverage pass still requires the semantic judge, which can reject wrong meaning.

v2.19.3.17 passes seven additional record/negation/echo checks (148 across eleven
isolated sports workflow suites) and local production-launcher health 200.

v2.19.3.18 passes four additional scope/identity/integration checks (152 across
twelve isolated sports workflow suites) and local launcher health 200. These
tests check retained relevant requirements, not a model's semantic reliability.
Google's API documents ThinkingConfig at
https://ai.google.dev/api/generate-content#ThinkingConfig .

Champion training remains a separate prompt-profile improvement process using
the existing human approval gate. This work does not fine-tune model weights,
activate a challenger, place wagers, or certify profitable performance. If a
profile is changed/promoted, validate that exact new active profile again.

## Commands after deployment and private sign-in

1. `Start sports validation`
2. `Continue sports validation` (one case per request, 25 successful advances)
3. `Show sports validation`
4. Inspect every failed case. Use the existing `Start champion training Sports
   Betting Analyst` / `Continue iterative training Sports Betting Analyst`
   commands for training; use the displayed restart instruction if an older
   harness session exists. Improvements remain subject to the existing promotion
   gate. Keep transfer-case answers out of training examples and candidate edits.
5. Validate the resulting exact active profile again before calling it ready.

With v2.19.3.13 or later, inspect `Show skill lab` for a pending sports
candidate. If none exists, `Train skill Sports Betting Analyst` drafts one
without activation. Then use `Start sports candidate validation`,
`Continue sports candidate validation` (one case per request), and
`Show sports candidate validation`. A provider failure preserves the last saved
case; inspect the checkpoint before continuing. These commands evaluate the
candidate independently and do not complete the champion trainer's round.
Keep the existing human promotion gate and revalidate any promoted profile.

`Sports analyze :: <scenario>` generates a Gemini sports answer and executes
no research or recording tools. Without supplied verifiable current facts, it
must not claim a live recommendation. `Sports evaluate :: <JSON>` runs math and
evidence checks with no model calls. `Sports log :: <JSON>` persists a pre-event
paper prediction. `Sports settle :: <JSON>` appends its result. `Show sports
ledger` shows descriptive paper metrics.

Snapshot fields: `event`, `market`, `selection`, `line` when applicable,
`event_start` (ISO with timezone), `indoor` (boolean), `odds` (American), `p_win`,
`p_low`, `p_high`, optional `p_push` and `opposite_odds`, `probability_method`,
`rationale`, and `evidence`. Probabilities are fractions, not percentages.
Evidence entries for `odds`, `availability`, `usage`, and outdoor `weather` need
`summary`, `source_url` (HTTPS without credentials/query/fragment), and
`captured_at`. Policy freshness windows are 30 minutes, 6 hours, 24 hours,
and 3 hours respectively. These are operating defaults, not empirical guarantees.
Parlays also need `is_parlay: true`, `joint_probability_method: "joint_model"`,
and `correlation_rationale`; that label is a caller assertion, not model validation.

Settlement JSON uses `prediction_id`, `outcome` (`win`, `loss`, `push`, `void`),
`source_url`, optionally `closing_odds` and `closing_line`. Only identical lines
produce price CLV; changed numbers are retained separately.

## Limits and current blocker

Private sign-in works. A corrected hypothetical push-math training example was
saved before deployment; this is prompt/example storage, not weight training.
Gemini's quota blocked the earlier champion-training start, but Gemini responded
after v2.19.3.10 deployed. No champion training round or promotion completed.

Validation SV-A1FF52C4DA104E24 persisted all ten first-baseline cases on active
profile v1 using gemini-3.5-flash-lite. The same-model judge awarded every case
100, but manual review rejected readiness: the line-movement answer was cut off
and mislabeled raw implied probabilities as no-vig; the small-edge answer
double-counted vig. Other answers also ended mid-sentence. Treat those scores as
unreliable, not as a successful acceptance test. No second baseline or holdout
stage was run; the stored checkpoint is 10/25 and remains historical evidence.

After PR #8 merged and v2.19.3.11 deployed, Gemini completed and production
persisted the ten first-baseline cases in SV-96F0182E6E9448AA. Its automated
average was 60/100 with a 60% pass rate. Four cases scored zero: changed-line
arithmetic/opposing price, invented parlay probability, double-counted vig, and
an unparseable semantic judge response. All answers were complete JSON.

Manual inspection also rejected supposedly passing risk-language and player-prop
answers: they invented opposing -110-like prices and no-vig references. The
small-edge and positive-odds answers invented lower probability bounds; the
line-change answer invented a fresh estimate/range. Some semantic answers omitted
parts of the expected process (append-only postmortem, prop inputs, ROI/buckets).
Thus even 60/100 is not an independently accepted score. The persisted checkpoint
is 10/25, and a complete baseline record was saved. No second baseline or
holdout stage was run with this harness; the remaining stages were paused after
these defects surfaced. No candidate was activated or champion promoted.

After the approved PR #9 merge/deployment, v2.19.3.12 completed validation
SV-9F908832BFD94AE9 on active profile v1, Gemini gemini-3.5-flash-lite, using
the sports-validation-v3-input-grounding-800-320 harness. All 25 case results
were saved. Automated baseline averages/pass rates were 70/70% and 80/80%;
the five transfer cases averaged 40 with a 40% pass rate. The session status
is failed. Baselines differ by ten points, but neither stage meets acceptance.

Objective checks rejected invented opposing prices/no-vig references on both
risk-language passes; the first small-edge pass omitted required push and
conditional probabilities. Both +150 answers produced incorrect expected
profit (1.775 and 1.75 instead of 0.175). The transfer stage rejected an
unsupported opposite price and missing NO BET at a negative lower-bound edge,
incorrect push-adjusted profit (-0.065 instead of +0.01545), and incorrect
-110 unit profit (-0.0476 instead of approximately -0.04545). These are saved
validation observations, not new candidate instructions or training examples.

Manual review also rejects some semantic-judge perfect scores. Prop answers
omit required inputs; payout answers omit explicit correlation treatment; the
second parlay answer mistakes an opposing team's under for a game-total under
and asserts the wrong correlation. The first small-edge answer claims juice
erodes already price-adjusted positive EV. The record-proof transfer answer
refuses certification/rewriting but omits the explicit append-correction process.
Thus the automated averages are not independently accepted readiness scores.

Champion session TRN-EB9AC23D07 started successfully using the saved first
baseline (70/100). Its subsequent continuation hit Gemini quota; it remains
READY_FOR_ROUND at 0/6, with no round consumed or candidate activation. Later
one-case validation requests succeeded. No exact quota reset time is known.
`Show skill lab` confirms pending sports candidate v2 CND-847D5380EF while the
active sports profile remains v1. Its candidate benchmark has not been completed.
v2.19.3.13 added the one-case candidate evaluation route without changing the
active profile, answer/judge harness, or model weights.

Candidate CND-847D5380EF completed its first ten-case Flash-Lite baseline in
SV-D2BFF5260C4443EA at 70/100 with 70% passing. It still invented opposing prices,
omitted small-edge calculations, and returned +150 expected profit of 1.175
instead of 0.175. Its checkpoint was paused at 10/25; no holdouts were run and it
was not activated. A newly drafted candidate CND-F5F24ABD95 saved two cases in
SV-5275BCE07B524F0F; the first repeated the opposing-price error and the second
passed ledger preservation. That run was paused at 2/25, not a complete baseline.

After selecting Gemini 3.5 Flash, active-v1 session SV-41626A62F4AF4CB5 started
with a separately pinned model identity. Its first completion did not return
confirmed STOP under the 800/320 limits; no case was graded or advanced (0/25).
The v2.19.3.14 follow-up supplies larger bounded budgets and explicit low thinking
for Gemini 3 sports calls. Start fresh v4 validation after deploying
TYLER_APP_MODULE=app_v2_19_3_14; the incomplete v3 Flash session is historical
evidence, not comparison data. No profile promotion or weight fine-tuning occurred.

There is no automatic sportsbook odds feed or fitted probability model. Snapshots
and probabilities are caller supplied and explicitly labeled unverified; a value
candidate is not a verified live bet. Same-model rubric scoring tests behavior,
not prediction accuracy. Repeated holdout inspection reduces its independence;
use new reserved cases if holdout failures guide later instruction changes.

The v5 application pipeline persisted the first ten cases of active-v1 session
SV-494DBEA3227D4DFD: automated average 94/100 and 90% passing. All supplied-price
and net-EV calculations were correct, including +150 net profit of 0.175 units
and no invented opposing price on the risk-language case. Manual review rejects
several perfect scores: the prop answer omitted carries, snap/route role and
line movement; sample-size reasoning omitted ROI/confidence groups; payout
reasoning omitted a whole-ticket estimate; correlation reasoning omitted the
quarterback/receiver connection and joint estimate. The positive-odds answer
also claimed variance overwhelms the apparent edge, while its judge incorrectly
treated positive EV as requiring a bet despite unverified inputs. That case
scored 45. The checkpoint is paused at 10/25; no v5 repeats or transfer cases
were queried and no candidate was activated. Training-baseline omissions and
the distinction between risk and expectation motivated v6's generic checks.

Active-v1 v6 session SV-FD780CF6CB554B06 saved ten first-baseline cases, averaging
79 with 80% passing. Prop factors, ROI/confidence groups and whole-ticket value
omissions were fixed, and arithmetic stayed correct. Two zero scores were false
failures caused by the application's variance regex matching the negated warning
"never a claim that variance or vig erases EV." That bug is corrected in v7,
without changing saved v6 results. Manual review still rejected the ledger answer
for omitting a postmortem and the correlation answer for echoing instructions
instead of giving a concrete game-script link. The changed-line answer also
inferred market consensus from a supplied quote, which is unsupported. This
checkpoint is paused at 10/25; no repeats or transfer cases were queried and no
profile was promoted. These training-baseline observations informed v7 checks.

Active-v1 v7 Flash-Lite session SV-9A91B59A880B4C20 completed ten first-baseline
cases: 89 average, 90% passing. Arithmetic and the negation checks passed;
correlation scored zero because the answer copied Explain/Discuss directives
instead of explaining the scenario. The coverage guard correctly caught that
failure. The checkpoint is paused at 10/25 with no repeats or transfer cases.

After switching to gemini-3.5-flash, separately identified v7 pilot
SV-C9A1F2539BA140FD completed one case (1/25). Its risk-language answer correctly
rejected locks and doubling stakes and left unsupplied metrics unknown. The
semantic judge falsely scored 70 for missing carries, snap/route role, ROI,
confidence buckets and joint-ticket probability, which that scenario did not
request. The run is paused. This observed grader-scope defect motivated v8;
saved v7 evidence is unchanged, no holds informed the revision, and active v1
remains protected.

The v4 budget/thinking deployment did not resolve the defect. Active-v1 Flash
session SV-AC897E1E3C4A4E00 received provider 503 errors on its first case, and
the Gemini 3.8 Flash configuration pilot SV-61F61ED4543D4A83 also received a
503 without advancing; each remains at 0/25. Restored Flash-Lite session
SV-D3AD3510E252400D saved two cases: risk-language failed for invented opposing
price/no-vig values, while ledger preservation scored 100. Its 2/25 checkpoint
is paused historical evidence, not a complete benchmark. Those training-baseline
source/arithmetic failures motivated the generic application-math design.

Application-level append-only records are not a database-enforced immutable
ledger: DB administrators can alter rows, and hashes detect changes only when
hashes are not also rewritten. Reads cover the latest 1000 rows per category.
Locks serialize writes within one process only; there are no cross-worker
uniqueness guarantees. Empty/unknown save receipts fail closed; inspect storage
before retrying an uncertain write. No schema or database permission changes
were made. Validation checkpoint writes/readbacks have now been verified in
production. The new paper-prediction category has now been saved and read back
in production; result persistence awaits a completed event. Final-only result
append and original-byte preservation have been checked with software fixtures.

Long-run performance requires genuinely pre-event out-of-sample paper records,
calibration by market/confidence group, CLV, ROI, and uncertainty estimates.
This software does not claim the model has a profitable betting edge.

## October 20 continuation — current college source archive boundaries

Current NCAA source receipt/crosswalk readers now reject static symlinks in
all path ancestors and bound regular manifests before decoding. Direct NCAA
and ESPN college identity replay also requires the expected local archive
filename; absolute or redirected source references cannot be read first.
Four regression methods reproduced 13 failures before repair; a fifth checks
bounded regular manifests. All 48 focused source/final-classifier tests and
730 integrated sports tests pass on this branch before other pending PRs.

Read-only replay of NCAA capture 20261020T123823802954Z verifies 295 retained
contests, and crosswalk 20261020T123825411389Z verifies ten strict identity
matches. Neither grants independent final certification, completeness or model
eligibility. No original source, feature, prediction or outcome is rewritten.
Static path checks do not prevent concurrent operating-system mutation. The
next boundary review is other direct NBA/provider archive filename consumers;
fitting, forecasting, evaluation, promotion and wagers remain disabled here.
