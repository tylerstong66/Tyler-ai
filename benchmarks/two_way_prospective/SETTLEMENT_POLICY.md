# Prospective result verification

Enrollment requires exact agreement between official and ESPN team identities,
venue status when available, and scheduled start time. Saved forecasts, model
weights, training data, probabilities, and pregame timestamps remain immutable.

## NHL final timestamp revisions

The October 14, 2026 completed capture `20261014T115856760081Z` shows two
otherwise corroborated finals that the original exact-time matcher rejected:

| NHL game | Saved ESPN event | Official start (UTC) | ESPN start (UTC) | Agreed final |
|---|---|---|---|---|
| 2026020100 | 401892498 | Oct 14 00:30 | Oct 14 00:45 | COL 3, DAL 2 |
| 2026020105 | 401892503 | Oct 14 03:00 | Oct 14 03:15 | BOS 6, SJS 3 |

Settlement permits an ESPN start-time difference of at most 15 minutes only for
an NHL final with a unique ESPN event ID already saved in the pregame forecast.
Both providers must mark the game final, identify the same home and away teams,
agree on final scores and available venue status, and the official game ID,
team IDs, and start time must still match the original forecast. Forecast hash
and pregame timestamp checks also remain required. Larger changes, ambiguity,
rescheduling of the official start, or disagreements leave the game pending.

New result records retain both provider times, the ESPN event ID, the time
difference, and the matching method under `match_verification`. This is a
collector verification correction, applied to both outcomes; it does not change
forecast selection, frozen models, or scoring formulas. Historical captures and
saved error records remain intact. MLB still requires exact-time matches,
including doubleheaders and resumptions.

The existing scheduled collector will verify pending results using this policy.
The first review milestone remains 100 settled games per sport, with enrollment
continuing thereafter. Settlements and paired market comparisons have separate
sample counts. No betting edge is established by reaching a count.

## MLB conflicting daily source snapshots (October 17)

The Oct 17 scheduled collector encountered the same official MLB game ID
in overlapping requested-day feeds with materially different originally
observed official rows. Previously this aborted the entire MLB collection
with `Daily official snapshots conflict`, even though unrelated games and
NHL evidence remained valid.

The collector now groups official MLB rows by game ID across requested dates.
Identical duplicated rows are safely deduplicated. If kickoff, team IDs,
score fields, or state disagree, **the full conflicting game is quarantined
from all new team-winner forecasts and final grades for that run**. Every
original daily observation, request date and conflict reason is preserved
under `captures/<run>/official_daily_conflicts.json` and recorded again
in `manifest.json` with `official_schedule_complete=false`,
`quarantined_game_ids`, and `official_daily_conflicts`. Other unique,
internally consistent MLB games can still be collected independently. A
quarantine also withholds new optional MLB market follow-up quotes during
that run rather than risk associating a quote with a disputed event; already
saved historical quote evidence is never modified. This is **partial source
coverage**, not a blanket successful verification of all scheduled games.

No source row is selected merely because its timestamp is later or more
favorable, and no frozen game/winner forecast, model input, team identity,
price, or official settlement is rewritten. In particular the already
identified two-hour frozen-start discrepancy for game 849817 remains
separate from its independently frozen hitter forecasts. Resolve that
discrepancy through an auditable future provider-identity investigation,
never retrospective re-enrollment or backfilled market odds.

**NO BET — actual wagers $0.**
