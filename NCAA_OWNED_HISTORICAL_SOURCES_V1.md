# NCAA-owned historical FBS original receipts

`sports_ncaa_historical_owned.py` retains at most three previously missing
NCAA-owned FBS source weeks per execution, with a fixed 1..21 week request
index. Source queries explicitly pin 2024 training or 2025 validation season;
currently the scheduled collector acquires training only. The index is not a
certified complete NCAA week calendar or official event census.

Every response is retained as original SHA-linked compressed bytes plus a
receipt with endpoint, season, week, acquisition time and replayed NCAA rows.
All existing seasons are verified before fetching more. Invalid scope, future
observations, missing/orphan files, wrong event season, malformed kickoff,
contradictory final chronology, modified guards, mismatched digests, truncated
archives and decompression expansion fail closed. A failed provider batch
publishes no newly prepared weeks. Original source files are never overwritten.

The first three actual 2024 responses contain 102, 79 and 67 contests: 248
unique NCAA contest IDs, no conflicting repeated IDs. All are reported finals
from the NCAA-owned source. They have not yet been independently joined with
ESPN historical IDs, so no result corroboration or model evaluation claim is
made. These 2026 acquisitions cannot become historical pregame forecasts.

The existing historical workflow keeps provider and NCAA-owned acquisition
outcomes separate and stages independent sources only on successful receipt
verification. Independent source unavailability does not certify results or
block retention of separately validated ESPN evidence. CI replays every
retained independent week. Training, forecasting, official grading, promotion,
production deployment and actual wagers remain disabled.
