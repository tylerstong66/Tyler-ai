# Tyler AI autonomy policy v1 — opt-in, limited, and auditable

**Status: design implementation / not deployed / no new permissions active.**

This policy is the first step toward a personal, self-improving Tyler AI. It is deliberately separate from existing human-gated maintenance operations and does not bypass them. Adding the policy module does not make current runtime maintenance methods automatically execute.

## Owner intent and boundaries

- Tyler AI should autonomously discover problems and opportunities, propose patches, run tests, open pull requests, and improve skills without seeking fresh permission for every ordinary step.
- Small isolated, non-production changes can eventually be merged without individual approval when all independent evidence is verified: passing exact-head CI, available rollback, and disabled production auto-deploy.
- Production application code, sportsbook/wagering controls, billing, secrets, credentials, security policy, infrastructure, and deployment remain separately approved. No actual wagers; NO_BET=true remains in force.
- The owner can suspend autonomy. The evaluator's enable switch must come from a trusted operator configuration, not from a chatbot prompt, user-supplied tool result, mutable memory, or proposed code.

## Current implementation

autonomy_policy.py implements a pure, fail-closed authorization evaluator. Its defaults do not grant permission. It denies unsafe path encodings, changes to protected files, high-impact actions, external side effects, and production merges. Automatic merges are limited to docs/autonomy/ and experiments/autonomy/ and require independent evidence inputs. It never executes a tool or changes a permission itself.

test_autonomy_policy.py exercises the default-deny and approval boundaries. **Neither file is wired into Tyler AI's existing runtime maintenance endpoints in this PR.** All existing operator approvals remain required.

## Required integration before turning on autonomous mode

1. Install an independent authorization gate at every mutating tool boundary (GitHub writes, PR merge, Render changes, n8n actions), not just in an LLM prompt. Apply branch restrictions, least-privilege credentials, and a write scope that cannot modify its own policy or workflow protections.
2. Use short-lived, narrowly scoped GitHub credentials. Prevent experimental candidate code from reading production secrets. CI must use isolated jobs and no privileged secrets on untrusted branches.
3. Evaluate live exact-commit checks and any author/PR review requirements server-side before a merge; never let the model self-report that CI passed or auto-deploy is disabled.
4. Keep append-only audit records of proposed changes, authorization decisions, tool calls, receipts, CI results, and rollback identifiers. Reconcile uncertain external outcomes instead of blind retries.
5. Turn on a limited operator-controlled feature flag only after integration tests, adversarial authorization tests, and a manual rollback rehearsal. Begin in dry-run mode, then branch/PR mode, then restricted non-production auto-merge.
6. Expand the allowlist only through separate explicit review. Preserve the sports research's frozen pre-event evidence, no-bet guarantees, and production isolation throughout.

## Validation scope

Run python -m unittest -v test_autonomy_policy from the repository root. Production behavior and deployed configuration are unchanged by this proposal.
