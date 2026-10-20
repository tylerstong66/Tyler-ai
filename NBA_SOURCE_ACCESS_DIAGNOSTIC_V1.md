# NBA endpoint access diagnostic

The existing independent NBA season schedule fetch returns HTTP 403 from the
collector runner. This separate diagnostic checks that exact endpoint, NBA's
public daily-scoreboard endpoint and the official NBA games pages for the current
and next America/New_York dates. A fifth fixed endpoint requests April 10, 2026,
to inspect the actual completed-game card shape from the previous regular season.
The sixth fixed endpoint requests the pinned 2026–27 NBA Stats season schedule
using the same public route as the retained closed-season NBA-owned archives.
It is explicitly labeled with its target season, does not change existing
collector URLs or receipt protocols, and cannot enable source validation merely
by returning HTTP 200. Returned bodies remain opaque diagnostic material.
That older response is diagnostic source material, not a current-season result
or evidence available at any earlier feature freeze. No historical evaluation
is performed. It uses the same existing NBA request headers, fixed
timeouts, bounded streaming and no redirects. No credentials are sent.

```
python sports_nba_source_access_probe.py
python sports_nba_source_access_probe.py --probe --output-dir nba-source-access-probe
```

The default command makes no network request. Explicit probing requires a fresh
output directory. Complete HTTP 200 bodies are retained as opaque compressed
diagnostics with SHA256s. Non-200 responses and oversized/incomplete bodies are
not archived. Exception types are retained without potentially sensitive messages.

HTTP 200 is not source validation: JSON shape alone does not attest NBA game
identity, season, schedules or finals. Even a successful diagnostic keeps every
source-verification and feature-enrollment flag false. No collector fallback is
enabled. A green diagnostic workflow means only that access observations were
recorded, including possible HTTP 403s; inspect each endpoint's HTTP status.
Any useful alternative still needs its own strict parser, archive replay,
identity matching and chronology checks before entering the research pipeline.
The workflow's token has read-only repository permission and is never attached
to NBA requests. No model, forecast, training, promotion or wagers are enabled.
