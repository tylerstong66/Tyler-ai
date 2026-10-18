# NBA closed-season original source replay

Research only. `NO_BET: true`, `actual_wagers: 0`; training, historical evaluation,
forecasting, promotion and official result grading remain disabled.

`sports_nba_historical_owned.py` pins the NBA-owned public Stats
`scheduleleaguev2` endpoint to LeagueID 00 and seasons 2024-25 (training source
split) and 2025-26 (validation source split). The season names describe source
partitions, not trained models. Public request headers follow nba_api 1.11.4;
no cookies, login or credentials are used. The older CDN route still returned
HTTP 403 during this investigation; this collector does not repair that route.

Each response retains original bytes in deterministic gzip plus a SHA-256
receipt, observation timestamp, exact URL, season identity and parsed rows.
The existing 8 MB response ceiling remains unchanged. Acquisition verifies
retained files before network access, fetches only a missing closed season,
and never overwrites an original. Replay checks league, season/game IDs, date
bounds, final chronology, source digest and normalized equality.

`sports_historical_nba_crosscheck.py` replays original ESPN daily receipts and
NBA season receipts. Team codes and scheduled starts determine identity before
scores are examined. Existing 30-minute agreement and 72-hour ambiguity guards
remain intact. Each result carries NBA and ESPN original/receipt digests and
its own observation timestamps. Another game's later receipt cannot authorize
a result. Unknown team codes (including the 2026 All-Star mini-tournament)
remain explicitly pending. NBA preseason, All-Star, play-in and Cup-final IDs
are outside the existing official regular-season/playoff parser scope.

## Reproduced 2026-10-18 source results

| Split | NBA regular/playoff IDs | ESPN IDs | Strict agreeing finals | Pending |
| --- | ---: | ---: | ---: | ---: |
| 2024-25 source training | 1,314 | 1,323 | 1,185 | 138 |
| 2025-26 source validation | 1,315 | 1,324 | 1,203 | 121 |

Training pending: 128 ambiguous identities, eight unmatched official IDs,
two kickoff disagreements. Validation pending: 113 ambiguous identities,
four unmatched IDs, four unsupported All-Star team-code games. These are
unverified observations, not findings of incorrect scores.

The NBA-owned receipts were observed in October 2026. They are postgame result
research, never evidence that features or predictions existed before tipoff.
No accuracy, calibration or betting-performance claim follows from agreement.
The earlier frozen source-content index covers provider daily inputs and NCAA
FBS weeks; these new independent NBA receipts append outside its v1 scope.

## Checks

```
python -m unittest -v test_sports_nba_historical_owned test_sports_historical_nba_crosscheck test_sports_nba_final_receipts
python sports_historical_nba_crosscheck.py --split train
python sports_historical_nba_crosscheck.py --split validation
```

Both read-only PR CI and the bounded acquisition workflow replay both splits.
NBA acquisition failure cannot authorize publication of partial NBA receipts.
Other leagues retain their independent source publication gates.
