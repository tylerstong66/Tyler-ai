# Sports Betting Analyst v1

The v2.19.3.11 deployment is confirmed live at merge commit
1cb1321db61f0a2cb121ac811322da2aabb674cf (Render deploy
dep-db2k9naj9qps73cu4uhg). Health returned HTTP 200 with that exact version and
commit. Sports Betting Analyst v1 has not passed acceptance. This document
includes a proposed v2.19.3.12 follow-up, not yet deployed.

## What changed

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
- The proposed v2.19.3.12 pins source constraints for the other seven training
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

Local v2.19.3.12 verification passed 13 new grounding tests plus 95 existing
relevant tests in separate processes (108 total). The versioned production
launcher imported v2.19.3.12 with a healthy test response. These are software
checks, not new Gemini benchmark results.

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

v2.19.3.12 uses harness sports-validation-v3-input-grounding-800-320, excluding
both earlier harnesses from comparisons. After approved merge/deployment, set
TYLER_APP_MODULE=app_v2_19_3_12 and start fresh validation. Inspect actual answers
and evaluator output alongside objective checks. Two complete baseline passes
and all five separate holdouts remain required. New real model scores and the
effectiveness of the revised prompt remain unverified until then.

There is no automatic sportsbook odds feed or fitted probability model. Snapshots
and probabilities are caller supplied and explicitly labeled unverified; a value
candidate is not a verified live bet. Same-model rubric scoring tests behavior,
not prediction accuracy. Repeated holdout inspection reduces its independence;
use new reserved cases if holdout failures guide later instruction changes.

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
