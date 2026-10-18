# Historical provider identity and split audit

`sports_historical_identity_audit.py` verifies original daily source bytes and
receipt metadata before auditing NBA, FBS and D1 men's basketball separately.
Game identity includes league, so numeric provider IDs shared by different
sports do not collide. Repeat observations of one game never increase the
unique-game count.

The audit quarantines any game ID present in training and validation, changed
team/start/stage/state/site/score observations, events outside their declared
split, events outside the requested UTC date or following UTC date, and finals
observed at or before their saved start. The one-day allowance accommodates
US evening games crossing UTC midnight; it does not attest exact local game
dates or complete official schedules. No source or receipt is rewritten.

Every audit retains daily receipt and original-response digests. CI and the
historical source workflow retain the audit as a 30-day artifact. The workflow
continues retaining authentic source observations even when individual games
are quarantined; corrupt source bytes abort before publication.

Initial local replay of 390 daily receipts: 7,961 distinct provider game IDs,
0 repeated observations and 0 detected quarantines. All currently retained
rows in that snapshot were training-season data; there were no validation
source dates yet. This cannot certify unseen validation data or independent
finals. All 440 offline sports tests passed, including duplicate-date,
cross-split contamination, changed-score, future-event and corruption cases.

Official-result corroboration and full source coverage remain unresolved.
Training, evaluation, forecasts, promotion and wagering stay disabled.

After PR #129's automatic post-merge collector, a fresh checkout independently
replayed 450 daily receipts: 8,306 distinct provider game IDs, 0 repeats and
0 quarantines. Each sport had 150 training dates and zero validation dates at
that capture. This update remains an acquisition/identity audit, not a model
benchmark or evidence of an edge.
