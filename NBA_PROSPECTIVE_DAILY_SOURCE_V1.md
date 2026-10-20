# Separate prospective NBA-owned daily source receipts

`sports_nba_owned_daily_observation.py` collects one explicit Eastern date under
the strict scheduled-pregame page policy. It uses its own archive root,
`benchmarks/nba_owned_daily_v1/captures/`. The default command makes no request
and writes nothing. Explicit collection accepts an integer offset of 0–3 days;
the default offset is one, so the collector requests tomorrow's Eastern date.

```
python sports_nba_owned_daily_observation.py
python sports_nba_owned_daily_observation.py --collect --days-ahead 1
python sports_nba_owned_daily_observation.py --replay CAPTURE_STAMP
python sports_nba_owned_daily_observation.py --audit
```

Public requests use fixed NBA URLs, existing NBA request headers, explicit
timeouts, bounded streaming and no redirects. Only HTTP 200 is accepted. No
repository token or account credential is forwarded. Both the request-start
clock and the clock read after complete response retrieval are saved. The
request must finish within five minutes, and every accepted NBA start must
follow the receipt clock. A midnight rollover preserves the date requested at
request start. The saved clock is a collector claim, not an independent clock
attestation.

The latest retained ESPN capture is selected before HTTP collection and fully
replayed. It must already exist at request start and remain at most 12 hours
old at response completion. Team and start identities are reconciled only for
the requested Eastern date; other dates are explicitly outside scope. Ambiguous
or non-unique joins, ESPN non-regular stages, live/completed states and elapsed
ESPN starts are withheld. The parser separately rejects unsupported NBA live,
final or postponed shapes for the whole page.

Only fully validated source receipts are written to a new, exclusively created
timestamp directory. Original HTML is retained in deterministic gzip form,
bound by hash and size. Replay verifies the exact canonical manifest against
both original source archives. It retains an old receipt's original clock and
reports current staleness separately. Changed inputs, extra files, clock/folder
disagreements and rewritten research guards reject replay.
Every retained receipt is replayed before making a new network request. An
orphaned/incomplete capture also blocks new collection until investigated;
it is never silently reused or overwritten.

The read-only PR/manual workflow captures and replays a new next-day source
receipt as an artifact. Its first live run 39417176214 captured October 21 at
2026-10-20T11:45:14.510380Z and reconciled 11 pregame games. Both original files
from artifact 12261683691 are retained exactly. The downloaded ZIP digest was
verified before bounded extraction, followed by successful local source replay.

The main college/NBA source workflow now runs this separate observer after its
ESPN audit and publishes daily archives only after collection and replay both
succeed. It exposes a distinct NBA_DAILY_PREGAME_SOURCE outcome. The existing
CDN schedule outcome and NBA feature gate retain their own meaning; a successful
daily page neither repairs the full-season feed nor enables feature enrollment.
Other source failures do not become successful through the daily-page result.
No old records, grades, forecasts, training or model promotions are changed.
NO_BET remains true; wagers are zero.
