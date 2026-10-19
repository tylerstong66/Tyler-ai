# Tyler NHL prospective paper test

Recorded: **57** · Settled: **52** · Pending: **5**

**NO BET — actual wagers $0.**

Frozen team-Elo logistic model versus fixed Elo and timestamped market odds. No NFL coefficients, goalie or pitcher model effects. Historical fitting is training only; this is the fresh independent test.

| Model | Paired games | Brier | Log loss | Accuracy |
|---|---:|---:|---:|---:|
| model | 52 | 0.4685 | 0.6614 | 65.4% |
| fixed_elo | 52 | 0.4321 | 0.6222 | 61.5% |
| market | 52 | 0.4425 | 0.6330 | 57.7% |

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
| MTL at WSH | Oct 14 07:30 PM | WSH | 52.1% |
| DAL at COL | Oct 14 08:30 PM | COL | 53.9% |
| BUF at TOR | Oct 15 07:00 PM | BUF | 52.7% |
| NYI at OTT | Oct 15 07:00 PM | OTT | 55.0% |
| SEA at TBL | Oct 15 07:00 PM | TBL | 56.0% |
| VAN at FLA | Oct 15 07:00 PM | FLA | 58.0% |
| NYR at NJD | Oct 15 07:00 PM | NJD | 51.7% |
| PHI at DET | Oct 15 07:30 PM | DET | 51.3% |
| WPG at CHI | Oct 15 08:00 PM | WPG | 52.0% |
| SJS at NSH | Oct 15 08:00 PM | NSH | 52.1% |
| STL at MIN | Oct 15 08:00 PM | MIN | 53.4% |
| UTA at EDM | Oct 15 09:00 PM | EDM | 52.3% |
| CGY at VGK | Oct 15 10:00 PM | VGK | 58.9% |
| PIT at COL | Oct 16 09:00 PM | COL | 55.5% |
| BOS at ANA | Oct 16 10:00 PM | ANA | 50.6% |
| NJD at WSH | Oct 17 01:00 PM | WSH | 54.1% |
| CAR at WPG | Oct 17 03:30 PM | CAR | 55.8% |
| VAN at TBL | Oct 17 04:00 PM | TBL | 61.4% |
| SEA at FLA | Oct 17 06:00 PM | FLA | 53.7% |
| NYI at TOR | Oct 17 07:00 PM | NYI | 50.0% |
| BUF at MTL | Oct 17 07:00 PM | MTL | 51.8% |
| SJS at DET | Oct 17 07:00 PM | DET | 50.1% |
| OTT at PHI | Oct 17 07:00 PM | OTT | 53.0% |
| NYR at CBJ | Oct 17 07:00 PM | CBJ | 51.6% |
| DAL at CHI | Oct 17 07:00 PM | DAL | 53.0% |
| STL at NSH | Oct 17 08:00 PM | STL | 50.3% |
| BOS at LAK | Oct 17 09:00 PM | BOS | 54.0% |
| EDM at UTA | Oct 17 10:00 PM | UTA | 53.3% |
| PIT at VGK | Oct 17 10:00 PM | VGK | 56.5% |
| CBJ at MIN | Oct 18 06:00 PM | MIN | 55.6% |
| CAR at CGY | Oct 18 08:00 PM | CAR | 58.5% |
| ANA at NYR | Oct 19 07:00 PM | NYR | 51.8% |
| COL at PHI | Oct 19 07:00 PM | COL | 53.1% |
| SJS at TOR | Oct 19 07:30 PM | SJS | 50.4% |
| PIT at UTA | Oct 19 09:00 PM | UTA | 54.6% |

All eligible regular-season and playoff games are enrolled before start, including games without odds (unpriced games are excluded only from paired market metrics). First review after 100 settled games; enrollment continues. Unknown starters/lineups stay unknown. Delays or source conflicts can leave coverage gaps. These are experimental forecasts, not betting recommendations.


[Full benchmark review, calibration and uncertainty](REVIEW.md)
