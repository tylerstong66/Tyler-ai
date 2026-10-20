# Native NBA null-envelope source receipts v2

Native probes on October 20 parsed all eleven October 21 pregame cards and
matched all eleven against the audited prior ESPN capture, with exact home,
away and UTC tipoff identity. Today's page remained unsupported under the
pregame status policy.

This opt-in collector stores a distinct v2 schema under
`benchmarks/nba_owned_daily_v2/captures`. V1 roots, schemas, envelope rules and
canonical replay remain unchanged. A frozen protocol passes the parser and
destination through the existing shared collector; no global mutation or
source-body rewriting selects the new protocol.

V2 requires complete, nonempty, unique agreement across the entire requested
date. Every official card and every same-date ESPN game must match, with exact
UTC tipoff, regular-season stage, pregame state and a future saved start.
Any unsupported card, missing/extra game, duplicate, status or time conflict
prevents receipt creation. Linked ESPN bodies are audited and must precede
the request by no more than twelve hours. Actual request and complete-response
clocks bound collection to five minutes; tipoffs must still be future at
receipt. All retained receipts replay before another fetch.

Raw native bytes and a canonical manifest are written exclusively, replayed
immediately, and retained as CI artifacts for reviewed repository archival.
The CLI defaults to no collection. No schedule is added. Public source bytes
are exportable from the source workflow for exact archival, not reconstructed
from parsed cards.

These are source observations, not forecasts. Full-season scope, independently
attested origin and clocks, final outcomes, feature enrollment, model fitting,
forecasting and promotion remain false. NO_BET=true; actual wagers zero.
