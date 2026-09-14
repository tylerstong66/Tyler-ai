# Tyler AI 2.9 reliability upgrade

## What changes
- Explicit task references load the original request, answer and saved sources into ordinary follow-ups and new tasks. Missing tasks fail explicitly.
- Recent conversation context is isolated by browser session or API conversation_id. It is bounded to four exchanges, 30 minutes and 128 conversations per worker. Only an opaque ID is stored in the browser cookie.
- Research queries use subject terms rather than instruction phrases. Audits of named tasks use the original research subject. Both reasoning paths receive titles, URLs and excerpts.
- Research responses include retrieved source links. Answers with URLs outside the retrieved set are withheld. This validates URL provenance, NOT semantic support for every claim. Relevant retrieval and real-world answer quality need live evaluation.
- Memory reads no longer perform implicit core-profile writes. Personal memory retrieval ranks recent saved facts by matching terms. Record lookup uses its ID directly, including older records.
- Save/update/delete operations require database record receipts. Existing replacement preview/confirmation commands remain available.
- Negative save instructions override save intent. They disable app memory/journal/task-state writes for the request, use the nonpersistent agent path, and discard that conversation's in-process history. They do not control provider retention or hosting access logs.
- Email requires an explicit n8n sent=true receipt. False, empty, malformed and generic HTTP-success responses are not reported as sent.
- Side-effect steps recheck authorization at execution and do not automatically retry uncertain failures or interrupted running steps.
- Partial failures retain confirmed memory-save/email receipts.
- Login template is restored to module scope.
- Offline regression checks run in GitHub Actions on this branch, PRs and main.

## n8n contract
The webhook must respond AFTER the email node succeeds with a JSON body:
```json
{"success": true, "sent": true}
```
For a failed email, return a non-2xx status or success=false. A workflow-started/queued acknowledgement is not proof of a sent email. This upgrade intentionally reports such responses as unconfirmed. Check n8n execution history before retrying an unconfirmed email. Confirmation means the email step succeeded; it does not prove inbox delivery.

## Deployment and validation
No schema migration or new runtime package is required. Merge the PR to deploy through the existing Render integration if auto-deploy is enabled. Keep app.py and reliability.py in the same deployment. Run:
```sh
python -m py_compile app.py reliability.py test_reliability.py
python -m unittest -v test_reliability
```
Tests block all unmocked network traffic and use no secrets or live data.

After deployment, check login, version v2.9.0, normal chat, explicit task lookup and a source-backed research question. Ask a follow-up in the same browser chat. Check a disposable memory's save, replacement and retrieval, and inspect the database to confirm a no-save request caused no app writes. Only test email with explicit authorization and a destination you control.

## Current limits
- In-process conversation history is temporary and is not shared across gunicorn workers or Render restarts. Explicit numbered task retrieval uses persistent storage and remains available. Multiworker shared conversation storage is future work.
- API clients must send a distinct, unpredictable conversation_id (16–100 letters, digits, underscores or hyphens) to opt into scoped recent context. This app still uses its existing single-owner API-key model.
- Memory ranking considers up to 800 recent rows before selecting 200 normal memories; it is not a vector index or an exhaustive semantic search.
- No-save requests deliberately do not create resumable tasks. A no-save instruction is per-request; use it again for subsequent turns.
- Suppressing automatic retries reduces duplicate actions but does not provide transactional exactly-once delivery or protect against simultaneous runs of the same task. A database execution lease/idempotency design is a follow-up before unattended concurrent workloads.
- Model-generated statements can still be unsupported even with valid source URLs. This is a foundation upgrade, not a guarantee of research accuracy or model fine-tuning.
