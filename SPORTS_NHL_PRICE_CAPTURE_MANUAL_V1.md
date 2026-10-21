# Manual research odds-original collection — disabled by default

This is the next independent preparation step, not live prospective profitability enrollment.

- New manual GitHub Actions workflow: .github/workflows/nhl_price_source_manual.yml.
- Collect command: python sports_profitability_capture.py --capture.
- HTTP source: exactly https://api.the-odds-api.com/v4/sports/icehockey_nhl/odds, American h2h DraftKings in the US; the account API key is passed only as a protected request parameter and is never copied into saved URLs, manifests, output messages or Git commits.
- Requires separately configured GitHub Actions repository secret THE_ODDS_API_KEY. Without it, manual runs fail explicitly and preserve no data; no scheduled activity is enabled. No account or paid plan is authorized by this repository change.
- Original JSON HTTP entity-body bytes (not reconstructed historical quotes) are SHA-256 archived under benchmarks/nhl_price_source_observations_v1/originals/ with exclusive, timestamped sanitized manifests in captures/. A repeated identical response retains one original and separate new observation manifests. No historical quote availability is inferred.
- Every original source manifest retains all returned vs still-future vs already-started event counts, publisher path and sanitized parameters, retrieval time, and explicitly false sportsbook executability / bookmaker publication-time / last-close / paper ROI flags.
- A successful manually dispatched workflow saves the original source evidence into main and uploads an artifact. GitHub's repository commit provides an independently observable publication record after that upload, but the capture script does not claim its own clock proves GitHub publication.
- Original game IDs, book offer availability, exact official/ESPN start crosswalk, last pre-start sportsbook quote, and immutable separate pre-event selection must still pass their stronger independent gates before any new paper ROI or CLV is reportable.
- No existing forecasts, quote files, NHL challenger weights/results, checkpoints, graded predictions or promotions are changed. No bet placements are attempted.

## Next dependency

The user must independently choose/obtain an odds API key and add it as THE_ODDS_API_KEY in GitHub repository Actions secrets (or authorize a connected secret-management action if available). The workflow is manual-only; do not enable automation or make a live API request without the configured credential and proper source scope. The Odds API free plan may provide live NHL odds, but neither its free tier nor any aggregator timestamps guarantee sportsbook executability.

NO_BET=true. Actual wagers $0. Model promotion disabled.
