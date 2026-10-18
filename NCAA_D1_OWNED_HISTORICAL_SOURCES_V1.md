# Independent NCAA D1 men's historical source receipts

The daily collector `sports_ncaa_d1_historical_owned.py` requests NCAA-owned
MBB division-1 responses for explicit 2024 training / 2025 validation dates.
It verifies every existing receipt before acquiring at most 20 missing dates,
completes training requests first, then advances to validation. Current/future
request days are rejected before fetching; original files are never overwritten.

Receipts retain original compressed bytes, response SHA256, source endpoint,
season/date, observation time and replayed original NCAA records. All candidate
responses are validated before any new day files are written. Wrong scope,
modified flags, future observations, missing source halves, decompression
expansion, digest/normalization changes and invalid kickoff chronology fail
closed. NCAA's displayed date must be within one calendar day of kickoff UTC,
which accommodates time zones while rejecting contradictory season dates.
All 42 existing FBS source receipts pass this added consistency check unchanged.

`python sports_historical_fbs_crosscheck.py --league NCAAM_D1` replays the new
source alongside the original ESPN daily archives. It uses exact school names,
unique schedule matching and matching finals, retains both digest chains and
never borrows 2026 FBS aliases. Repeated source days count a game only once.
The existing default FBS report remains canonically byte-equivalent.

The first three actual training dates contain 246 distinct NCAA contest IDs;
104 match ESPN finals under this conservative policy. Remaining IDs are not
called incorrect results; source-date coverage and identities are incomplete.

Historical collection publishes FBS and D1 source directories only when their
respective independent acquisition steps succeed. CI replays D1 originals and
retains a 30-day crosscheck artifact. New D1 sources append outside the original
2,292-file FBS/provider completion snapshot's historical scope; no original
snapshot or source bytes are rewritten.

No model training, evaluation, forecasting, final certification, promotion,
production deployment or wagers are enabled. All 464 offline sports tests pass.
