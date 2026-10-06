# Sports Betting Analyst v1

The v2.19.3.9 deployment is confirmed live at commit
609108c4139668eb4c9b99ee876235e6fec13123 (Render deploy
dep-db2dt0e7bikc73de4mh0). This document describes the proposed v2.19.3.10
software changes, which have not been deployed or tested with live credentials.

## What changed

- All sports profile instructions reach benchmark answers. The older compact
  context took the first ten instructions, omitting the final two rules.
- Sports answers get 400 output tokens per case and judges get 160. Older
  suite-wide limits left only a few dozen answer tokens per case for ten cases.
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

Live sign-in rejected the provided access key. No live baseline, training round,
validation checkpoint, or sports database write was run in this continuation.
The accepted benchmark scores reported by unit tests are fixtures, not Tyler's
scores. Restore private UI access to run the real benchmark/training sequence.

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
were made; production persistence remains unverified until authenticated tests.

Long-run performance requires genuinely pre-event out-of-sample paper records,
calibration by market/confidence group, CLV, ROI, and uncertainty estimates.
This software does not claim the model has a profitable betting edge.
