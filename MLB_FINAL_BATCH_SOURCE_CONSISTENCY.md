# One official final snapshot per game and settlement batch

The settlement job previously fetched a game's feed for the status check and
again inside each hitter's strict settlement validator. Two hitters could cause
four HTTP requests and observe different source revisions within one batch.

The job now retains one response and its original evidence receipt per selected
official game for that invocation. Status checks and every selected hitter use
independent copies of that same response. The underlying official reader still
enforces its fixed origin, response bounds and original-body archive behavior;
the direct settlement validator still checks the exact game, both teams, original
start, final state, hitter identity and explicit batting counts.

The cache expires at the end of the call. Nonfinal games, missing counts and
start conflicts are re-fetched on the next scheduled attempt; settled records
remain untouched. The rotating player-game budget is unchanged. The report's
`attempted_official_checks` remains a player-game count; the added
`official_game_source_fetches` counts unique game responses in that invocation.
No source clock is advanced when a cached response is read.

Regression tests reproduce the old four-fetch behavior with a source revision
between requests, verify consistent original statistics, isolate returned payload
and evidence mutations, and demonstrate cache expiration and no fetches for
already settled records. The existing strict conflict, missing-field, cross-game
progress and untouched-forecast tests remain in force. This change does not
resolve genuine missing counts, schedule conflicts or legacy source gaps.
NO_BET=true; zero actual wagers; model promotion remains disabled.
