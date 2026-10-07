# Sports Betting Analyst v1

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
production; sports prediction/result persistence still requires its own check.

Long-run performance requires genuinely pre-event out-of-sample paper records,
calibration by market/confidence group, CLV, ROI, and uncertainty estimates.
This software does not claim the model has a profitable betting edge.
