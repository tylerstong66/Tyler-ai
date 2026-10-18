# Sports research maturity — retained repository evidence, October 18, 2026

This read-only assessment uses the repository snapshots at base `beec53c`.
Counts are cohort-specific, not independently re-certified performance claims.
All work remains NO_BET / actual_wagers 0 / no model promotion or runtime deploy.

| Sport | Retained development evidence | Immediate evidence gap |
|---|---|---|
| NFL | Prospective v2: 26 recorded, 14 settled, 12 pending; 13 paired priced decisive games | Only two season/week uncertainty blocks; retain null confidence intervals and await independent weeks |
| NHL | Original: 53 recorded / 51 settled; frozen challenger: 16 enrolled / 14 scored / 2 pending | Continue unchanged prospective challenger; evaluate the preregistered first 100 rather than tune on early outcomes |
| MLB | Team winner: 10 recorded / 7 settled / 3 pending; hitter: 19 player-games / 8 scored / 1 ineligible / 10 pending | Pending official batting completeness and cross-cohort start-time drift; only two scored hitter-game clusters |
| NBA | NBA schedule/ESPN receipt code is tested; 0 real NBA-owned archived captures; historical provider collection 110/490 declared dates | NBA CDN returned HTTP 403 in run 39148942458; independent source acquisition and final replay remain blocked before model evaluation |
| NCAA FBS | New all-capture reader: 23 unique raw-replayed NCAA/ESPN agreeing postgame results across 17 compatible captures | One older crosswalk excluded under current identity policy; source scope and historical pregame evidence remain uncertified |
| NCAA D1 men | Separate source/identity parsers; historical provider collection 110/312 declared dates | No qualifying college-final dataset rows yet; require independent matched final sources and chronology |

NBA/FBS/D1 historical dates retrieved are provider observation coverage, not proof
of complete official schedules. FBS retained 110/302 declared historical dates.
The new college result observations are a separate 2026 research cohort, not the
2024-fit/2025-validation history and not prospective paper forecasts.

Sources: `benchmarks/nfl_prospective_v2/summary.json`,
`benchmarks/two_way_prospective/{nhl,mlb}/summary.json`,
`benchmarks/nhl_challenger_shadow_v1/scoreboard.latest.json`,
`benchmarks/mlb_hitter_props_shadow_v1/scoreboard.latest.json`,
`benchmarks/college_nba_history_v1/COVERAGE.latest.json`, and deterministic
`sports_college_result_dataset.py` replay of all 18 retained crosswalk captures.
