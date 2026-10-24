# Bounded retries for missing native NBA finals

The scheduled native-v3 collector normally requests yesterday's Eastern date.
A temporary unsupported page on that date could leave a frozen game unresolved
even after the source becomes readable. `sports_nba_final_catchup.py` adds a
separate retry plan for missing native finals from two or three Eastern days
ago. Yesterday's collection stays in place.

Planning first replays the frozen native-v2 features and all retained native and
provider sources. It selects only records whose two original saved starts have
passed and share the same Eastern date, with no accepted native final and no
identity/score quarantine. Matching outcomes and missing-provider-only cases
do not cause a native retry. Requests are deduplicated by date: at most two
additional requests per scheduled run. Older unresolved game IDs are reported
outside the retry window rather than silently backfilled.

The default CLI only prints a plan. `--collect` retains original v3 bytes through
the existing append-only collector, including opaque unsupported responses.
Crossing Eastern midnight rejects the stale plan before requesting another date.
Retries run before the normal yesterday capture so single-date readers continue
to select the newest yesterday observation when that collection succeeds.

Publication replays every explicitly listed capture and verifies its requested
date and original collection day. The workflow stages those exact directories,
plus the normal collector's exact receipt, instead of sweeping the native-v3
root. A failed retry cannot publish an unrelated partial receipt. Artifacts and
status distinguish a successful empty plan from actual additional captures.
The cumulative report is recomputed after collection; a new receipt cannot hide
an earlier conflicting claim.

At the October 24 development check, all older missing-native dates were already
covered, so the real plan requested zero retries. The 15 unresolved records are
October 24/25 games; the first saved start was October 24 at 6:00 p.m. Eastern.
No result is inferred from a scheduled start or a successful network request.

This creates source receipts only. Outcome enrollment, settlement, forecasting,
training and promotion remain disabled; `NO_BET=true`, actual wagers zero.
