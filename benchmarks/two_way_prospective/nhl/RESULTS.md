# Tyler NHL prospective paper test

Recorded: **22** · Settled: **6** · Pending: **16**

**NO BET — actual wagers $0.**

Frozen team-Elo logistic model versus fixed Elo and timestamped market odds. No NFL coefficients, goalie or pitcher model effects. Historical fitting is training only; this is the fresh independent test.

| Model | Paired games | Brier | Log loss | Accuracy |
|---|---:|---:|---:|---:|
| model | 6 | 0.4666 | 0.6596 | 83.3% |
| fixed_elo | 6 | 0.4330 | 0.6263 | 66.7% |
| market | 6 | 0.4769 | 0.6683 | 50.0% |

| Game | Start (Eastern) | Model pick | Win probability |
|---|---|---|---:|
| SEA at WSH | Oct 11 05:00 PM | WSH | 57.0% |
| VAN at NYR | Oct 11 06:00 PM | NYR | 56.8% |
| CAR at PHI | Oct 11 07:00 PM | CAR | 55.9% |
| FLA at BUF | Oct 12 01:00 PM | BUF | 54.7% |
| OTT at NJD | Oct 12 07:00 PM | OTT | 50.2% |
| VGK at MIN | Oct 12 08:00 PM | MIN | 50.9% |
| NJD at DET | Oct 13 06:00 PM | NJD | 50.3% |
| FLA at CBJ | Oct 13 06:15 PM | CBJ | 52.3% |
| BUF at MTL | Oct 13 06:30 PM | MTL | 52.1% |
| WSH at CAR | Oct 13 06:45 PM | CAR | 57.3% |
| SEA at PHI | Oct 13 07:00 PM | PHI | 51.9% |
| TBL at NYR | Oct 13 07:15 PM | TBL | 51.4% |
| STL at OTT | Oct 13 07:30 PM | OTT | 54.2% |
| VAN at NYI | Oct 13 07:45 PM | NYI | 56.8% |
| PIT at CHI | Oct 13 08:00 PM | PIT | 52.8% |
| MIN at WPG | Oct 13 08:15 PM | MIN | 50.6% |
| COL at DAL | Oct 13 08:30 PM | DAL | 50.6% |
| VGK at NSH | Oct 13 08:45 PM | VGK | 52.2% |
| TOR at UTA | Oct 13 09:00 PM | UTA | 55.7% |
| CGY at ANA | Oct 13 09:45 PM | ANA | 57.2% |
| EDM at LAK | Oct 13 10:30 PM | EDM | 52.4% |
| BOS at SJS | Oct 13 11:00 PM | SJS | 50.0% |

All eligible regular-season and playoff games are enrolled before start, including games without odds (unpriced games are excluded only from paired market metrics). First review after 100 settled games; enrollment continues. Unknown starters/lineups stay unknown. Delays or source conflicts can leave coverage gaps. These are experimental forecasts, not betting recommendations.
