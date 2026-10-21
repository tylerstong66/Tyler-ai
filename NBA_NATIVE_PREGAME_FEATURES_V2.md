# Separate native-daily NBA reference features

The original v1 feature collector depends on a full-season NBA endpoint that is
currently unavailable. Its sixteen existing records, protocol, source contracts
and scheduled collection gate remain unchanged. This explicit v2 feature protocol
uses a separately replayed native daily receipt and its independently archived,
exactly agreeing ESPN source. It never substitutes a daily page into a v1 record.

The new protocol is sealed in
`benchmarks/nba_native_pregame_features_v2/protocol.json`; new records belong only
under its `records` directory. The default command is inert. Use
`python sports_nba_native_pregame_features.py --audit` for read-only replay or
`--collect` for explicit local append-only observation collection. No scheduled
collector or production model adopts it in this change. Collection performs no
HTTP requests: it audits retained original sources and historical references.

Every new record requires a complete one-to-one, regular-season, pregame daily
receipt with exact team identities and UTC starts, from the existing native v2
source protocol. The linked ESPN manifest must have its original exact digest.
Both complete-response clocks must be at or before freeze and before both saved starts, and
both sources must be at most twelve hours old. Freeze is sampled after dependency
audit, inside a bounded five-minute local audit/creation interval. Started,
stale or insufficient-reference targets remain unrecorded; unknown source state
or inconsistent inputs fail. There is no fallback to an older source receipt.

Historical references use the unchanged sealed v1 reference definition: the
last ten exactly corroborated 2025–26 games per team available at freeze,
including regular-season and playoff references under that sealed policy.
Only new target games must be regular season.
Original historical source seals, row identities and receipt chronology are
replayed. Missing or later results cannot enter a feature. Mean points for,
against and margin, time since the latest prior scheduled start and all original
reference rows remain visible. Time between scheduled starts is not measured
rest after an attested actual game end. Prior-season roster changes and current
season form are not modeled; the accepted subset is not a complete schedule.

Before appending anything, the collector replays all existing v2 feature files,
their original source captures and the bounded native source inventory. Each
file must exactly equal a recomputation at its own original freeze, with its
original protocol, native/ESPN manifest and raw-response hashes. Rehashed feature
edits or gate changes still fail. Filenames and source game IDs must agree;
symlink paths, unknown files and oversized inputs fail. Writes are exclusive.
Later audits do not update old features. Static checks do not provide protection
against arbitrary concurrent operating-system mutation.

These are feature observations, not forecasts. Game IDs can overlap existing
v1 features or repeated source captures and must not be pooled as additional
independent games. No result is graded, original forecast backfilled, accuracy
computed, publication/origin attested or full-season availability certified.
Training, historical evaluation, forecasting and promotion remain disabled.
NO_BET=true and actual wagers zero. Any subsequent real records need their own
original-clock retention and separate GitHub pre-start publication evidence.
