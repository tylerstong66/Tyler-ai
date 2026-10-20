# NBA-owned daily final page parser

This separate offline parser accepts complete regular-season daily pages of
regulation finals. It shares bounded embedded-JSON, route, requested-date,
season, locale, pagination and calendar-count checks with the existing pregame
parser. Game IDs, franchise IDs/tricodes, sides, final status, period totals and
source-reported actual start/end chronology must all agree. Duplicate games or
teams, ties and inconsistent totals fail closed. Pregame acceptance is unchanged.

The original April 10, 2026 page was requested by diagnostic run 39420119470 at
head `1d95e264b217e220202e565fa75f25b3b0814db7` on October 20, 2026. Artifact
12263667020's ZIP SHA256 is
`25d800e1c8c8a1d8d03f5316cbe57e1cefd5216ac9e7d3d36e50ac164acb4a25`.
Its original HTML body SHA256 is
`2d50e1ed52824252deb3109552f2f497e10f93999d67540b3efb9021f129a3bc`;
all 716,767 bytes and the retained gzip member were checked before development.
The pinned fixture manifest preserves that provenance. Its observation is the
diagnostic's October probe clock, never an April pregame timestamp.

```bash
python -m unittest test_sports_nba_games_page test_sports_nba_final_games_page
python sports_nba_final_games_page.py
```

The original body yields 15 regulation finals. Their IDs, teams, starts, statuses
and scores match the separately archived NBA-owned 2025–26 season response.
This is same-origin corroboration, not independent ESPN agreement or current
season final verification. The fixture was not available at an earlier feature
freeze. It is not new historical outcome enrollment or historical evaluation.

Overtime, postseason, mixed pregame/live/final, postponed, canceled and unknown
shapes remain unsupported and reject the page. Reported actual timestamps are
source claims, not independently attested actual start times. A completed daily
page cannot establish full-season completeness or upstream truth. No collector,
result dataset, lifecycle, settlement or model is connected to this parser.
All existing evidence and original feature observations remain unchanged;
forecasting, fitting, grading, promotion and wagering remain disabled here.

Next: design separate current-season postgame capture and exact identity
reconciliation only after relevant live payloads and source clocks are retained.
Unsupported lifecycle shapes need real source inspection before acceptance.

## Separate historical cross-source fixture diagnostic

`python sports_nba_final_page_reference.py` compares the parsed NBA page with
the existing sealed April 10 ESPN raw archive. The original 2,292-file content
seal and historical receipt replay must pass first. ESPN opponent tricodes and
IDs are read from the original response, then the existing strict final
classifier selects identities before comparing scores. All 15 historical
fixtures agree. Score or team disagreement remains pending/quarantined.

The original ESPN observation is October 18, 2026; the NBA page diagnostic is
October 20. Agreement is available only at the later clock. This is a read-only
reference-fixture diagnostic, not new outcome enrollment, current-season final
verification, evidence available at historical pregame freeze, prediction
grading or model evaluation. It writes no benchmark dataset or feature record.
