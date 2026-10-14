# Tyler MLB prospective paper test

Recorded: **6** · Settled: **4** · Pending: **2**

**NO BET — actual wagers $0.**

Frozen team-Elo logistic model versus fixed Elo and timestamped market odds. No NFL coefficients, goalie or pitcher model effects. Historical fitting is training only; this is the fresh independent test.

| Model | Paired games | Brier | Log loss | Accuracy |
|---|---:|---:|---:|---:|
| model | 2 | 0.5323 | 0.7260 | 50.0% |
| fixed_elo | 2 | 0.5549 | 0.7496 | 50.0% |
| market | 2 | 0.6075 | 0.8024 | 50.0% |

| Game | Start (Eastern) | Model pick | Win probability |
|---|---|---|---:|
| LAD at MIL | Oct 11 08:00 PM | MIL | 56.1% |
| LAD at MIL | Oct 12 05:00 PM | MIL | 56.1% |
| CLE at TB | Oct 12 08:00 PM | TB | 58.3% |
| CLE at TB | Oct 13 08:00 PM | TB | 58.3% |
| MIL at LAD | Oct 14 08:00 PM | LAD | 51.4% |
| TB at CLE | Oct 15 01:00 PM | CLE | 50.5% |

All eligible regular-season and playoff games are enrolled before start, including games without odds (unpriced games are excluded only from paired market metrics). First review after 100 settled games; enrollment continues. Unknown starters/lineups stay unknown. Delays or source conflicts can leave coverage gaps. These are experimental forecasts, not betting recommendations.


[Full benchmark review, calibration and uncertainty](REVIEW.md)
