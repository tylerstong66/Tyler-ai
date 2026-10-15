# MLB hitter season context — v2.19.3.38

This research-only upgrade adds verified batting-side and pitching-hand metadata, plus the hitter's previous and current regular-season totals, beside Tyler's earlier pitcher matchup and automatically collected bullpen shortlist. No game hit/HR probabilities, sportsbook prices, joint parlay forecasts, or wagers are generated.

The October 15, 2026 live MLB StatsAPI schema audit found that a traded hitter's season response can return an aggregate total *and* several per-team totals. The parser uses the aggregate once, cross-checks the sum of each distinct team's totals, and refuses contradictions; if only distinct team rows are available, it sums those once. It explicitly filters by MLB player ID, season and regular-season game type, and rejects missing/inconsistent counts.

Official hitter batting side and probable starter throwing hand come from separately checked MLB people endpoints. Missing data stays unknown, rather than inventing platoon effects. Historic rates are explicitly labelled descriptive per at-bat / plate appearance; they are **not** probabilities of a hit or home run in tonight's game.

When deployed, the same authenticated command applies:

```text
sports mlb full research by name :: {"date":"2026-10-15","hitter_name":"Andrew Vaughn","team_name":"Milwaukee Brewers","starter_name":"Tyler Glasnow"}
```

The above is a time-sensitive pregame example only, not a wager recommendation. Exact names and game status are reverified. The old version v2.19.3.37 remains available for rollback.

Run the regression suite including:

```bash
python -m unittest -v test_sports_mlb_hitter_context test_sports_mlb_contextual test_v2_19_3_38_mlb_context_http
```

Before activation: independently check the new season/hand data flow using the live MLB public API, run all repository checks, then update the Render `TYLER_APP_MODULE` selector only after reviewing those results.
