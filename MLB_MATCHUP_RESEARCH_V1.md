# MLB hitter-vs-pitcher and bullpen research v1

**Status: research-only library; not connected to live Tyler chat or production forecasts.** This is the first independently testable building block for the requested MLB prop workflow. No live odds, data provider, calibrated probability, placed wager, or demonstrated edge is implied. All supplied data is treated as unverified until a future feed adapter independently obtains and validates it.

## What it does

- Accepts a *single hitter* plus a listed probable/announced/unknown starter and up to 15 possible relievers.
- Uses **MLB player IDs**, not name-only joins; rejects mismatched/duplicated IDs and impossible counting-stat totals.
- Requires an HTTPS source URL, retrieval timestamp, and explicit data-through timestamp for each historical matchup row.
- Rejects analysis whose cutoff is at/after first pitch, as well as evidence dated after the cutoff.
- Preserves unknown historical HR statistics, missing pitcher rows, and reliever availability rather than replacing them with zeros or guesses.
- Reports descriptive historical hits/at-bats, home runs/plate appearances, data coverage, and small-sample flags.
- Does **not** infer a hit probability, HR probability, parlay joint probability, EV, bullpen encounter likelihood, or wagering decision.

## Offline invocation

```bash
python -m unittest -v test_sports_mlb_matchups
python sports_mlb_matchups.py --input /path/to/pregame_snapshot.json
```

Illustrative input (synthetic participants/statistics and an example source; **not verified baseball evidence**):

```json
{
  "game_id": "849831",
  "as_of": "2026-10-15T17:00:00Z",
  "event_start": "2026-10-15T23:00:00Z",
  "hitter": {"id": 10001, "name": "Synthetic Hitter"},
  "starter": {"id": 20001, "name": "Synthetic Starter", "status": "probable"},
  "bullpen_candidates": [
    {"id": 30001, "name": "Synthetic Reliever", "availability": "unknown"}
  ],
  "matchups": [
    {
      "hitter_id": 10001,
      "pitcher_id": 20001,
      "pa": 20, "ab": 18, "hits": 6, "home_runs": 1,
      "source_url": "https://example.org/synthetic-fixture",
      "retrieved_at": "2026-10-15T17:00:00Z",
      "data_through": "2026-10-14T23:00:00Z"
    }
  ]
}
```

Output fields `historical_batting_average` and `historical_hr_per_pa` describe recorded inputs, **not** the chance of a hit or home run tonight. Missing stats return `null`; a reported zero HR rate is only produced when HR=0 was explicitly supplied and PA>0.

The game ID is format-checked only. Identity against the official schedule and independent verification of every source remain work for the feed adapter. Probable/announced starter labels and bullpen statuses are input claims, not confirmations that pitchers will actually enter the game.

## Next milestones

1. Independently fetch pregame MLB schedule, roster/lineup, pitcher identities and historical batter-vs-pitcher records from documented sources. Pin content and times and defend against suspended/doubleheader identity confusion. Missing rows remain unknown.
2. Add validated bullpen usage/availability features and identify *plausible* relievers without pretending a lineup or appearance is certain.
3. Join a separately trained, out-of-sample player-prop probability model; compare it with no-vig sportsbook prices and preserve forecast uncertainty.
4. Integrate research results into an authenticated Tyler conversational command and regression suite without changing frozen team-level experiments.

There is **no deployment/promotion** in this module's introduction.
