# Tyler MLB prospective paper test

Recorded: **15** · Settled: **10** · Pending: **5**

**NO BET — actual wagers $0.**

Frozen team-Elo logistic model versus fixed Elo and timestamped market odds. No NFL coefficients, goalie or pitcher model effects. Historical fitting is training only; this is the fresh independent test.

| Model | Paired games | Brier | Log loss | Accuracy |
|---|---:|---:|---:|---:|
| model | 7 | 0.4962 | 0.6894 | 42.9% |
| fixed_elo | 7 | 0.4806 | 0.6739 | 71.4% |
| market | 7 | 0.5575 | 0.7515 | 42.9% |

| Game | Start (Eastern) | Model pick | Win probability |
|---|---|---|---:|
| LAD at MIL | Oct 11 08:00 PM | MIL | 56.1% |
| LAD at MIL | Oct 12 05:00 PM | MIL | 56.1% |
| CLE at TB | Oct 12 08:00 PM | TB | 58.3% |
| CLE at TB | Oct 13 08:00 PM | TB | 58.3% |
| MIL at LAD | Oct 14 08:00 PM | LAD | 51.4% |
| TB at CLE | Oct 15 01:00 PM | CLE | 50.5% |
| MIL at LAD | Oct 15 08:00 PM | LAD | 51.4% |
| TB at CLE | Oct 16 06:00 PM | CLE | 50.5% |
| MIL at LAD | Oct 16 09:00 PM | LAD | 50.8% |
| TB at CLE | Oct 17 08:00 PM | CLE | 51.2% |
| TB at MIL | Oct 23 08:00 PM | MIL | 57.5% |
| TB at MIL | Oct 24 08:00 PM | MIL | 57.5% |
| MIL at TB | Oct 26 08:00 PM | TB | 50.0% |
| MIL at TB | Oct 27 08:00 PM | TB | 50.0% |
| MIL at TB | Oct 28 08:00 PM | MIL | 50.5% |

All eligible regular-season and playoff games are enrolled before start, including games without odds (unpriced games are excluded only from paired market metrics). First review after 100 settled games; enrollment continues. Unknown starters/lineups stay unknown. Delays or source conflicts can leave coverage gaps. These are experimental forecasts, not betting recommendations.


[Full benchmark review, calibration and uncertainty](REVIEW.md)
