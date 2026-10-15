# October 15 pregame readiness audit

**Verified October 15, 2026 at 9:22 a.m. Eastern. NO BET / actual wagers $0.**

The October 15 Eastern slate matches saved prospective forecasts: all 14 observed games are enrolled, priced at enrollment, still unstarted, and have usable current moneylines. Saved event IDs, home/away identity and exact start times match the fresh sources. Forecast and result hashes passed the existing benchmark integrity loader.

| Cohort | Schedule games | Enrolled | Saved market prices | Usable current prices | Identity/start-time conflicts |
|---|---:|---:|---:|---:|---:|
| NFL | 1 | 1 | 1 | 1 | 0 |
| NHL | 11 | 11 | 11 | 11 | 0 |
| MLB | 2 | 2 | 2 | 2 | 0 |

## Game checks

All times Eastern. Each row passed enrollment, market and identity checks.

| Sport | Game | Start | Saved forecast ID |
|---|---|---|---|
| NFL | SEA at DEN | 8:15 PM | 2026_06_SEA_DEN |
| NHL | BUF at TOR | 7:00 PM | 2026020108 |
| NHL | NYI at OTT | 7:00 PM | 2026020109 |
| NHL | SEA at TBL | 7:00 PM | 2026020111 |
| NHL | VAN at FLA | 7:00 PM | 2026020112 |
| NHL | NYR at NJD | 7:00 PM | 2026020113 |
| NHL | PHI at DET | 7:30 PM | 2026020110 |
| NHL | WPG at CHI | 8:00 PM | 2026020114 |
| NHL | SJS at NSH | 8:00 PM | 2026020115 |
| NHL | STL at MIN | 8:00 PM | 2026020116 |
| NHL | UTA at EDM | 9:00 PM | 2026020117 |
| NHL | CGY at VGK | 10:00 PM | 2026020118 |
| MLB | TB at CLE | 1:00 PM | 849818 |
| MLB | MIL at LAD | 8:00 PM | 849810 |

## Two historical MLB market gaps

These are enrollment-price gaps, not missing game forecasts. The retained enrollment snapshots contain no usable paired moneyline, but they omit the original raw provider schema. They cannot establish whether the provider had no odds or the earlier parser could not read them.

| Game | Forecast recorded (Eastern) | Later archived pregame odds (Eastern) | Later home / away odds |
|---|---|---|---|
| LAD at MIL (849812) | Oct 11, 08:32 PM | Oct 12, 03:21 AM | +113 / -136 |
| CLE at TB (849813) | Oct 12, 08:41 PM | Oct 13, 03:43 AM | -143 / +119 |

Both gaps predate the separate follow-up quote mechanism added in PR #48. That mechanism already records the first usable later quote before start in its own append-only artifact with source, timestamp and forecast-hash verification. The two historical games stay outside enrollment-time market comparisons; archived later quotes are evidence only. All current pending MLB games have enrollment prices, so no odds-parser or capture-policy change was justified by this audit.

## Verification repair

The newest saved NFL forecast has unknown injury coverage because publication season could not be verified. Three early returns in the injury parser omitted the explicit disabled-effects flag, causing the real-artifact test to fail. The repair adds the flag on future unknown-coverage returns. The immutable existing artifact is accepted only by its exact saved hash and expected unknown metadata; new artifacts still require the explicit false flag. Model weights, probabilities and scored forecasts are unchanged.

Validation: **94 tests passed**, covering market parsing, separate follow-up timing/linkage/immutability, archived coverage, reviews and prospective benchmarks. Regression cases cover missing publication metadata, wrong week, wrong season, future publication time and missing publication time. No collector or workflow was dispatched for this audit.

## Sources and limits

Fresh GETs:
- NFL schedule source: [https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv](https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv), retrieved 2026-10-15T13:22:34.833179+00:00.
- NFL espn source: [https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261015](https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261015), retrieved 2026-10-15T13:21:48.957233+00:00.
- NHL schedule source: [https://api-web.nhle.com/v1/schedule/2026-10-15](https://api-web.nhle.com/v1/schedule/2026-10-15), retrieved 2026-10-15T13:21:49.943359+00:00.
- NHL espn source: [https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates=20261015](https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates=20261015), retrieved 2026-10-15T13:21:48.969205+00:00.
- MLB schedule source: [https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-15&hydrate=probablePitcher,linescore,team](https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-15&hydrate=probablePitcher,linescore,team), retrieved 2026-10-15T13:21:48.322188+00:00.
- MLB espn source: [https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates=20261015](https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates=20261015), retrieved 2026-10-15T13:21:48.905867+00:00.

NFL schedule corroboration uses the benchmark's nflverse schedule source plus ESPN; NHL and MLB schedules use league APIs plus ESPN. This checks the observed October 15 slate, not a guarantee that upstream sources list every future game. Source response hashes, per-game checks and immutable forecast hashes are in [evidence.json](evidence.json). Reduced audit evidence is retained; raw provider responses were inspected transiently and are not archived here. Current prices are observations, not verified closing lines. Source state and scheduling may change after this check. These results establish readiness, not prediction accuracy or a betting edge.
