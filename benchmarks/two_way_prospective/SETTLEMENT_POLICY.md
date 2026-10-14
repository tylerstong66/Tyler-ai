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

**NO BET — actual wagers $0.**
