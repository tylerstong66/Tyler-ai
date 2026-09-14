# Tyler AI v2.8.3 rollout

## Prepared changes
- Memory/task lookup filters directly by ID, with no newest-250 cutoff.
- Email requires HTTPS and a configured N8N_WEBHOOK_KEY. N8N_AUTH_HEADER defaults to X-Tyler-Key.
- Email success requires JSON with success=true, sent=true and a nonempty Gmail message_id. Text, redirects and failure responses are rejected.
- Side-effect steps are never automatically retried or replanned after errors. Resuming an interrupted write stops for manual reconciliation.
- Task saves compare the previously loaded serialized state before updating; stale concurrent requests fail without dispatching another action.

## n8n draft
Workflow: My workflow 2 (N0P1CpcaUpBCiVcT).
Draft version: 12c7750d-86ce-402d-b287-4b5eb4506af8.
Webhook uses headerAuth with the existing Header Auth account credential.
Respond to Webhook returns an explicit receipt derived from Gmail's message ID.
Gmail retries are disabled and Gmail errors stop the workflow.
The published version was left unchanged.

## Before rollout
1. In n8n, inspect Header Auth account. Verify the header name and value privately.
2. In Render, set N8N_WEBHOOK_KEY to that same value. Set N8N_AUTH_HEADER to its exact header name (default X-Tyler-Key). Do not put secrets in this repository or chat.
3. Keep N8N_WEBHOOK_URL pointing to the existing tyler-action production webhook.
4. Coordinate publishing the n8n draft with deploying this branch. Publishing authentication before deployment will reject the old app; deploying first will reject the old text receipt. Avoid email tasks during this short transition.
5. Verify the Supabase lookup and conditional task update on a disposable task in the real environment, then use one explicitly authorized email to verify the complete integration. No live emails or database writes were performed during development.

## Verification
12 local unittest regression tests passed using Flask 3.1.2 and requests 2.32.5.
Run: python -m unittest -v test_reliability
Both edited n8n node configurations validated successfully.
Published and draft workflow versions were confirmed distinct after saving.

## Limits
A Gmail receipt confirms API acceptance, not inbox delivery.
This prevents automatic repeated dispatch for the same persisted task; separately submitted requests or manual n8n reruns are not deduplicated.
An uncertain outcome requires checking n8n/Gmail before creating a replacement task.
Compare-and-swap uses the serialized task text in a PostgREST equality filter, requiring no schema change. Very large tasks can exceed the service/proxy URL limit; the operation then fails closed. A dedicated revision column or database RPC is a future improvement.
The task persistence behavior and credential match still require live verification before activation.
