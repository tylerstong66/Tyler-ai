# NBA native null-envelope diagnostic reader v2

The October 20, 2026 public endpoint probe found an explicitly null
`isDateOverrideActive` on otherwise date-matched daily pages. The v1 parser
requires true. Existing v1 collectors, receipt schemas, roots, and replay
contracts remain unchanged.

The opt-in `sports_nba_games_page_v2.py` diagnostic accepts explicitly present
null only. It shares all bounded HTML/JSON, exact route/query/selected-date,
calendar completeness, regular-season identity, franchise, status, and future
tipoff checks with v1. Missing flags and all nonnull values are rejected.
Null does not attest that the UI override is active.

The access-probe workflow verifies archived native response lengths and SHA256
bindings before parsing current and next-day pages. It retains candidate
successes or explicit rejection reasons in an artifact, with the actual probe
clock and original body hash. It writes no accepted source receipts or
forecasts. Synthetic test mutations are marked as such; they are not live
source evidence.

A successful candidate parse still requires independent ESPN identity and
tipoff cross-checks, retained append-only native receipts, and prospective
feature chronology before any collector adoption. Full-season completeness,
independent receipt clocks, training, forecasting, promotion, and wagering
remain disabled. NO_BET=true; actual wagers zero.
