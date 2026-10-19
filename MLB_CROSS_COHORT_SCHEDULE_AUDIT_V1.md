# Independently frozen MLB cohort schedule audit

`sports_mlb_cross_cohort_audit.py` is a read-only audit of the team-winner and
conditional hitter cohorts. It does not merge forecasts, results, metrics or
first-100 checkpoints. It compares only matching official MLB game IDs with
consistent home/away team IDs and hitter orientation. A mismatch fails closed.

The actual retained audit covers 19 player-games across three games:

| Official game | Hitter records | Hitter saved start minus winner saved start |
|---|---:|---:|
| 849810 | 7 | 0 minutes |
| 849816 | 6 | +8 minutes |
| 849817 | 6 | +120 minutes |

The signed differences reflect independently saved schedules. They are neither
proof of source corruption nor permission to replace an original start. Even
zero drift does not make two separate freezes contemporaneous observations.
Issue #98 originally tracks game 849817; the same audit reveals the eight-minute
difference for game 849816.

Each comparison retains both paths, file SHA-256, sealed record digest, original
freeze/generation timestamps and saved starts. Winner evidence includes verified
original reduced snapshot hashes, original response digests and retrieval times;
the target's original official and ESPN schedule claims must agree with its saved
identity, pregame status and start. Hitter sources retain their exact URLs,
response digests, retrieval times and replay availability. Game, roster, player,
season and pregame chronology are validated separately. Declared raw archives
must replay and match original game/team/start claims; absent/corrupt declared
archives are errors, never silently downgraded into legacy evidence.

There is a material unresolved limitation in the current 19 older hitter records:
their original source response bytes were not retained. The winner cohort stores
reduced factual snapshots rather than full original responses. Matching seals
and digests validate retained content; they cannot reconstruct missing originals.
This audit therefore leaves `original_source_validation_complete` false and
lists the source gaps. It does not use today's feed, fabricate old market quotes,
attach new archive metadata to old signed records or alter the originals.
Independent server publication times are not attested by this module either.
Issue #98 remains open for these incomplete acceptance criteria.

Run locally or inspect the separate CI artifact:

```sh
python sports_mlb_cross_cohort_audit.py
```

No joint performance comparison is enabled. NO_BET remains true, wagers zero;
no new forecasts, fitting, historical evaluation, model promotion or runtime
deployment occur. Existing independent cohort reports remain unchanged.
