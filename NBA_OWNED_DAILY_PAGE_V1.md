# NBA-owned daily pregame page replay

The public NBA games pages for October 20 and 21 returned HTTP 200 from the
read-only diagnostic runner, while both CDN schedule endpoints returned 403.
The original HTML bodies are retained under `benchmarks/nba_games_page_v1/initial_probe/`.
Their manifest binds each original body hash and size to diagnostic run
39415304518, commit 72e77afb81ea504c6ec7b49fadc1c3eca7db9425 and artifact
12262075268. The downloaded ZIP hash was checked against GitHub's artifact
digest before extracting the two bounded original bodies. The manifest itself
is hash-pinned by the replay module. These bindings retain acquisition evidence;
they do not independently attest the source origin or receipt clock.

```
python -m unittest -v test_sports_nba_games_page
python sports_nba_games_page.py
```

Both commands are offline. The replay uses the original observation clock,
2026-10-20T11:29:34.339098+00:00, and explicitly reports that it is not a fresh
observation. The original diagnostic's false validation flags remain untouched.
The separate parser validates the embedded NBA page payload under a narrow new
policy: one explicit Eastern date, English `/games` route, no page errors or
pagination, an explicit calendar count, regular-season NBA game IDs, stated
season, franchise IDs/tricodes, unique games and franchises, zero pregame scores,
and future UTC starts on that Eastern date. Only scheduled pregame cards are
accepted. Live/final/postponed/unknown shapes reject the whole page. Duplicate
embedded data scripts or JSON keys also reject the page.

The originals contain 3 and 11 games. All 14 game IDs, home/away tricodes and
scheduled starts exactly match the earlier archived NBA-owned season schedule.
The tests verify those comparisons directly from both sets of original bytes.
The page calendar's other dates are counts, not game identities; this module
never treats them as a full-season schedule. One empty day requires an explicit
zero in that date's calendar entry.

This is an offline parser and archive replay. It is not connected to the live
collector, feature enrollment, final-result tracking, forecasting, training or
promotion. A separate prospective collection/replay integration with freshness,
ESPN identity reconciliation and chronology checks is still required. Existing
NBA and FBS frozen records are untouched. NO_BET remains true and wagers zero.
