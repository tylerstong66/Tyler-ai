# Read-only FBS frozen feature cohort state

`sports_fbs_feature_cohort.py` replays the original FBS reference-feature cohort,
original source captures and historical source seals. It associates those
features with the separate deduplicated college result-observation dataset;
it never creates forecasts, modifies records or computes prediction accuracy.

The first real replay shows five pending feature observations, zero corroborated
results, zero identity quarantines and zero schedule shifts. Current source-pair
ages and saved source states are explicit. A stale pregame snapshot cannot prove
that a game is still pregame; passing the original saved start is only a clock
comparison, not proof of actual kickoff. Missing games do not imply cancellation.

Every row retains original source starts, later source starts and signed drift,
the frozen record digest and original source IDs. A result requires the original
NCAA/ESPN pair, both ESPN team IDs and matching NCAA school identities, replayed
source evidence, valid untied integer scores and postgame observations after
both original and reported starts and the original freeze. A later start never
replaces an original saved timestamp.

The dataset retains earlier agreeing final evidence after a game leaves a later
scoreboard, so normal slate rollover does not erase a source observation. But
an identity change, later contradictory result or dataset quarantine withholds
that observation. Later absence and later contradiction are separate cases.
Malformed scores, unverified source flags, duplicate results and future source
timestamps fail closed. Original feature and result files remain unchanged.

A successful cohort report certifies neither fresh acquisition nor independent
publication time. The separate source-status receipt exposes acquisition
outcomes, and the separate replayable GitHub report covers original feature
publication chronology. This report also does not attest source origin,
institutional membership or actual kickoff.

The source workflow uploads the read-only lifecycle artifact and records
`FBS_FEATURE_COHORT_AUDIT`; archived CI also runs its tests and source replay.
All current no-training/no-evaluation/no-forecast/no-promotion/no-wager guards
remain in effect. NO_BET stays true, actual wagers zero.

```sh
python sports_fbs_feature_cohort.py
```
