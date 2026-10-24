# Tyler NHL prospective paper test

Recorded: **97** · Settled: **84** · Pending: **13**

**NO BET — actual wagers $0.**

Frozen team-Elo logistic model versus fixed Elo and timestamped market odds. No NFL coefficients, goalie or pitcher model effects. Historical fitting is training only; this is the fresh independent test.

| Model | Paired games | Brier | Log loss | Accuracy |
|---|---:|---:|---:|---:|
| model | 84 | 0.4841 | 0.6771 | 59.5% |
| fixed_elo | 84 | 0.4727 | 0.6653 | 58.3% |
| market | 84 | 0.4663 | 0.6580 | 54.8% |

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
| SJS at MTL | Oct 20 07:00 PM | MTL | 55.9% |
| COL at NJD | Oct 20 07:00 PM | COL | 51.1% |
| ANA at NYI | Oct 20 07:00 PM | NYI | 51.9% |
| LAK at WSH | Oct 20 07:00 PM | WSH | 59.2% |
| TOR at CBJ | Oct 20 07:00 PM | CBJ | 55.3% |
| WPG at STL | Oct 20 08:00 PM | STL | 53.3% |
| BOS at DAL | Oct 20 08:00 PM | DAL | 51.2% |
| MIN at EDM | Oct 20 09:00 PM | EDM | 50.7% |
| DET at SEA | Oct 20 09:40 PM | SEA | 52.9% |
| CAR at VAN | Oct 20 10:00 PM | CAR | 60.9% |
| TBL at VGK | Oct 20 10:30 PM | VGK | 53.0% |
| PHI at BUF | Oct 21 07:30 PM | BUF | 56.0% |
| FLA at OTT | Oct 21 07:30 PM | OTT | 53.5% |
| NSH at BOS | Oct 22 07:00 PM | BOS | 56.1% |
| NYR at TOR | Oct 22 07:00 PM | NYR | 50.2% |
| SJS at OTT | Oct 22 07:00 PM | OTT | 55.1% |
| ANA at NJD | Oct 22 07:00 PM | NJD | 53.6% |
| FLA at PIT | Oct 22 07:00 PM | PIT | 50.1% |
| LAK at NYI | Oct 22 07:30 PM | NYI | 56.0% |
| VGK at STL | Oct 22 08:00 PM | VGK | 50.8% |
| WPG at DAL | Oct 22 08:00 PM | DAL | 56.0% |
| MIN at CGY | Oct 22 09:00 PM | MIN | 52.9% |
| CAR at EDM | Oct 22 09:00 PM | CAR | 53.1% |
| UTA at SEA | Oct 22 10:00 PM | UTA | 50.6% |
| DET at VAN | Oct 22 10:00 PM | DET | 51.6% |
| MTL at CHI | Oct 23 08:00 PM | MTL | 53.8% |
| TBL at COL | Oct 23 09:00 PM | COL | 50.3% |
| ANA at PHI | Oct 24 01:00 PM | PHI | 52.8% |
| LAK at NJD | Oct 24 03:30 PM | NJD | 56.1% |
| SJS at BOS | Oct 24 07:00 PM | BOS | 55.3% |
| NYR at OTT | Oct 24 07:00 PM | OTT | 54.5% |
| NSH at PIT | Oct 24 07:00 PM | PIT | 53.0% |
| BUF at WSH | Oct 24 07:00 PM | WSH | 52.5% |
| VGK at CBJ | Oct 24 07:00 PM | VGK | 52.2% |
| CAR at STL | Oct 24 07:00 PM | CAR | 53.4% |
| TOR at EDM | Oct 24 07:00 PM | EDM | 56.8% |
| TBL at UTA | Oct 24 09:00 PM | TBL | 50.6% |
| DET at CGY | Oct 24 10:00 PM | CGY | 52.4% |
| MIN at SEA | Oct 24 10:00 PM | MIN | 50.3% |
| FLA at CHI | Oct 25 03:00 PM | FLA | 52.1% |

All eligible regular-season and playoff games are enrolled before start, including games without odds (unpriced games are excluded only from paired market metrics). First review after 100 settled games; enrollment continues. Unknown starters/lineups stay unknown. Delays or source conflicts can leave coverage gaps. These are experimental forecasts, not betting recommendations.


[Full benchmark review, calibration and uncertainty](REVIEW.md)
