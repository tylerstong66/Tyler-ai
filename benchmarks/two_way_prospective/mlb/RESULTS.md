# Tyler MLB prospective paper test

Recorded: **3** · Settled: **1** · Pending: **2**

**NO BET — actual wagers $0.**

Frozen team-Elo logistic model versus fixed Elo and timestamped market odds. No NFL coefficients, goalie or pitcher model effects. Historical fitting is training only; this is the fresh independent test.

| Model | Paired games | Brier | Log loss | Accuracy |
|---|---:|---:|---:|---:|
| model | 1 | 0.3855 | 0.5781 | 100.0% |
| fixed_elo | 1 | 0.3728 | 0.5652 | 100.0% |
| market | 1 | 0.4871 | 0.6802 | 100.0% |

| Game | Start (Eastern) | Model pick | Win probability |
|---|---|---|---:|
| LAD at MIL | Oct 11 08:00 PM | MIL | 56.1% |
| LAD at MIL | Oct 12 05:00 PM | MIL | 56.1% |
| CLE at TB | Oct 12 08:00 PM | TB | 58.3% |

All eligible regular-season and playoff games are enrolled before start, including games without odds (unpriced games are excluded only from paired market metrics). First review after 100 settled games; enrollment continues. Unknown starters/lineups stay unknown. Delays or source conflicts can leave coverage gaps. These are experimental forecasts, not betting recommendations.
