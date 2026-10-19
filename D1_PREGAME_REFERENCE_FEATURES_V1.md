# Prospective D1 prior-season reference features

`sports_d1_pregame_features.py` prepares independently sealed D1 feature
observations for the 2026–27 target window. The protocol uses the last eight
corroborated 2025–26 source results per team whose actual retained receipts are
available before the new feature freeze. It uses no reconstructed availability,
current-season form, odds, probabilities or trained model.

```
python sports_d1_pregame_features.py
python sports_d1_pregame_features.py --collect
```

The default command is read-only. Explicit collection appends eligible records
under `benchmarks/d1_pregame_reference_features_v1/records`. It never replaces
an existing record. Every existing record must replay from its original source
and reference receipts before any new file is written.

Protocol SHA256:
`2aeef95b5322d9f3ef9995c8720383edcf5ddb32fd2d06d5325f6516cae8ef3b`.
The reference reader replays both historical content seals and the reviewed D1
identity policy. It additionally binds original ESPN provider names and team IDs
to each historical source row. Both teams need eight eligible prior results;
changed provider identities, late history and missing history stay unenrolled.

Current source matching retains the existing strict NCAA/ESPN crosswalk; this
change enables no new live-school aliases. Enrollment requires unique provider
game IDs, exact current provider team ID/name continuity, matching source
starts, explicit scheduled/pregame state, regular-season provider stage and
both schedule observations no more than 12 hours old. The source and crosswalk
must precede the feature freeze, which must precede both saved starts. Aware
caller clocks are normalized to UTC before serialization.

NCAA daily request URLs must retain the fixed 2026 season parameter. The target
request window is October 30, 2026 through April 7, 2027; these dates describe
supported source requests, not an attestation of the first official game or
institutional membership. Source games outside that window cannot enroll.

The October 19 real-data preflight replayed 5,977 corroborated reference games,
found zero current D1 crosswalk matches and created zero records. A successful
preflight does not mean current D1 games exist. Status separately reports any
college crosswalk's presence, current D1 source-game availability and match
counts. The collector publishes new D1 files only after successful validation;
an empty records directory is not required before the first eligible game.

These are reference features, not predictions. Roster/coach changes and current
season form remain unmodeled. No current institutional-membership certification,
independent publication timestamp, actual tipoff, model quality or profit is
claimed. New cohorts require separate publication and lifecycle checks.
Forecasting, training, historical evaluation, promotion and wagers stay disabled.
