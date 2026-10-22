# NHL sportsbook-specific market observation adapter — research only

This adapter is **read-only and unqualified for profitability**. It does not access a live API, contain an API key, estimate the existence of an unobserved offer, create bets, change frozen models, settle games, or write to an existing ledger. It parses original bytes supplied by an independently archived **future** response from The Odds API v4's NHL odds endpoint.

Evidence specification: https://the-odds-api.com/liveapi/guides/v4/

- Pinned request: NHL icehockey_nhl, h2h moneyline, bookmaker draftkings, American prices. Remove API keys and sensitive query strings from any retained source URL; record the exact sanitized request parameters separately.
- Archive original response bytes (not reserialized provider JSON), their SHA-256, actual retrieval time and actual archive time before kickoff. Do not create a missing past snapshot using The Odds API historical endpoint.
- For each official verified NHL matchup, require exact full home and away team names and exact original UTC start between official source and external feed; reject ambiguous or duplicated events. Require exact selected two-outcome h2h market from DraftKings, both American prices and market-specific last_update, and no alternative lines/handicaps/periods. A bookmaker-level last_update is insufficient. Market last_update is preserved as aggregator_market_last_seen_at ONLY; provider_updated_at remains null because the aggregator timestamp cannot independently certify the sportsbook's own publication time. Merely changing available_to_paper to true cannot make the stored observation satisfy the later paper eligibility gate.
- Fail when price data was updated after retrieval, became older than 10 minutes at retrieval, or was archived more than five minutes after retrieval, or after kickoff.
- The archived quote's available_to_paper and last_pre_start_offering_verified flags are BOTH FALSE. It CANNOT be ingested as qualified paper ROI or CLV because a third-party odds aggregate observation doesn't itself certify DraftKings execution or a certified last pre-start sportsbook quote.
- The output is a hashed, exact-market **observation for future source-readiness diagnostics only**. It is never a decision to wager.

Remaining blockers to real prospective ROI: provision a licensed/authenticated future capture source, independently verify that selected sportsbook offers were truly available at the paper-selection time, persist original source and GitHub-server publication-time receipts, pin a schedule crosswalk from original official NHL team IDs/times to third-party event IDs, and independently verify bookmaker-specific closing availability. These require genuine future observations and cannot be repaired with historical guesses.

NO_BET=true. Actual wagers $0. Model promotion disabled.

## Tested manual-capture to parser interoperability

The read-only sports_profitability_capture_bridge.py bridge accepts only a previously archived raw response and exact research manifest from benchmarks/nhl_price_source_observations_v1. It verifies the original SHA-256 against content-addressed bytes, the sanitized exact provider request parameters (regions=us, markets=h2h, bookmakers=draftkings, oddsFormat=american; the sport is in the endpoint path), preserved team/start/source fields, the observed source event denominator, and separate retrieval/archive timestamps. The original collector now stores archived_at explicitly; missing old metadata is rejected rather than guessed. A manifest's local filename is checked for self-consistency but is not independent server proof. The bridge's returned observation always retains NO_BET=true, actual_wagers=0, qualified_for_paper_roi=false and publication_server_attested=false. It cannot create bets, authorize market availability, certify original NHL team IDs or alter the profitability policy.

Synthetic collector-to-parser integration tests exercise the exact resulting manifest/body format, stale or fabricated timestamps, forged source counts, path escape, corrupted source bytes, unsafe parameters, identity/start mismatch, and tampered eligibility flags. There is still no real price qualification, certified sportsbook close or proof of an exploitable edge.
