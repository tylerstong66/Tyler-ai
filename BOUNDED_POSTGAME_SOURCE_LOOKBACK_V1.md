# Bounded source lookback for overnight games

The source collector previously requested only today's UTC calendar date and
future dates. Evening games can finish after UTC midnight while remaining on
the prior day's scoreboard. The next scheduled run could therefore omit a
finished game before any final observation was retained.

The source workflow now explicitly requests two previous dates and three future
dates for ESPN and NCAA daily scoreboards. NCAA FBS queries still use estimated
adjacent official week candidates; their completeness remains uncertified.
The NCAA daily lookback is important for men's hoops once that source window
opens. Dates are clipped to each source league's declared season, including the
last football dates when the lookback overlaps the season end.

Both collectors retain their legacy default of zero lookback. Explicit zero
produces identical legacy manifest bytes for the same clock and inputs.
Positive lookback is bounded to at most three previous dates; forward range
remains at most seven. New opt-in captures add an explicit UTC-anchored
`collection_window` receipt with `pregame_feature_backfill_allowed: false`.
Original v1 capture files and frozen feature records are never edited.

Provider replay verifies the exact declared date/league request set as well as
original filenames, endpoint URLs, hashes and parsed observations. NCAA replay
verifies the declared window and exact official request tuples. New provider
lookback captures also pin a stricter reconciliation policy: repeated game IDs
that disagree on season stage, venue or provider team names are quarantined,
in addition to existing schedule/team/status/score conflicts. Legacy receipts
retain their original reconciliation policy; no old cohort is reinterpreted.

Offline integration tests reproduce a prior-evening FBS final on the next UTC
morning: zero agreement without lookback and one agreeing postgame observation
with lookback. Conflict, missing-day, malformed-policy, non-UTC clock and season
boundary regressions remain fail-closed. Source result observations cannot
backdate a forecast, recreate pregame features or enable performance grading.

```sh
python sports_expansion_observer.py --days-back 2 --days-ahead 3
python sports_ncaa_official_source.py --days-back 2 --days-ahead 3
```

The lookback is a bounded retrieval window, not proof of schedule completeness
or a guarantee of upstream availability. NBA's separate CDN access limitation
still appears in source-status receipts. Model fitting, evaluation, forecasting,
promotion, activation and wagers remain disabled; NO_BET stays true.
