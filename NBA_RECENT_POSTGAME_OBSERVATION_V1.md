# Separate recent NBA postgame source observations

`sports_nba_postgame_observation.py` retains one NBA-owned daily page for the
actual request clock's Eastern date or a bounded zero-to-three-day lookback.
This is a distinct append-only source archive, separate from pregame receipts,
frozen features, ESPN identity crosswalks, result datasets and predictions.
It reuses the fixed public NBA games route, existing request headers, byte
bounds, timeout and no-redirect policy. No credentials are forwarded.

```bash
python -m unittest test_sports_nba_postgame_observation test_sports_nba_final_games_page test_sports_nba_games_page
python sports_nba_postgame_observation.py --collect --days-back 1
python sports_nba_postgame_observation.py --audit
```

The default command is inert. Collection validates all retained source receipts
and directory ancestors before any fetch. It records the start clock and the
actual complete-body receipt clock, refusing backwards or over-five-minute
requests. Every receipt binds the exact original HTML byte count and SHA256 to
a deterministic gzip member, fixed route, Eastern date, inferred season and
separately versioned parser output. Replay recomputes the canonical manifest at
its original receipt clock and rejects future-dated, altered, redirected,
incomplete or extra-file archives. A replay is not a fresh observation.

The existing regulation-final parser remains unchanged. A complete supported
page is source-only data, never independently certified results. An empty day
is labeled `EMPTY_DAY_NO_FINAL_EVIDENCE`, with zero final evidence. Mixed,
overtime, pregame, live, postponed, malformed or otherwise unsupported pages
remain opaque diagnostic bodies; no partial game list or scores escape them.
Empty and unsupported pages cannot certify event coverage or season completeness.

The first real capture requested October 19, 2026 at October 20 13:44 UTC.
Receipt `20261020T134407369928Z` preserves 282,545 bytes with SHA256
`83b808161f9b6104df89aa7edb653f99033d90e094afcc26b98cd28bdcaedcc3`.
It replays as an empty day and provides **zero current-season finals**. This
does not fill the still-blocked full-season schedule or independent-final gaps.

Twelve new tests exercise raw-body replay, old pages under current clocks,
supported reference shapes under explicitly simulated unit clocks, empty days,
whole-page withholding, receipt chronology, Eastern season boundaries, request
scope, exclusive creation, tampering, directory redirects and inert CLI behavior.
Temporary simulated receipts are test fixtures, never research observations.
All 36 focused tests pass. The dedicated read-only CI workflow captures the
previous Eastern date and retains its actual source/replay artifact for 30 days;
it adds no schedule or monitor and cannot commit results.

Independent ESPN reconciliation, outcomes, scoring, model training, promotion,
forecasts, feature backfill and wagers are disabled. Source timestamps and origin
are not independently attested. Next: inspect real supported current-season
final bodies, then design a separately versioned exact-identity comparison at
the later actual source clock. Preserve all original feature freezes.
