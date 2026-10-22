# Independent pre-event NHL/ESPN identity crosswalk (research only)

A frozen probability and a saved odds-provider event must not be associated solely because a team name or kickoff time looks similar. This offline, forward-only crosswalk replays two separately SHA-256-archived original raw sources: the official NHL schedule for the **Eastern date** of the saved game and the ESPN NHL scoreboard for that date.

The parser demands one official 10-digit NHL game ID, normal regular-season/playoff pre-event status, original home/away NHL team IDs and abbreviations, an exact pre-event ESPN game with the same start and teams, a unique ESPN event ID, and compatible neutral-site status. Source URLs, dates, original byte hashes, retrieval chronology, and a recorded-before-start time must agree. Ambiguous source rows, changed starts, started games, missing official IDs, aliases that are not pre-reviewed, and contradictory teams/venues fail closed.

It produces only an immutable, hashed original event crosswalk with official team IDs, exact ESPN team names, original source SHA-256s and zero-wager research flags. It can supply the identity input to the separate manual odds-archive parser after that parser is integrated, but does **not** certify the external odds provider event, bookmaker executability, price age, a last pre-start offering, GitHub-server publication, or independent profitability. It never creates or backfills a forecast.

This initial crosswalk only reads already retained source bytes. It does not collect original NHL/ESPN schedules. Missing prior evidence is an exclusion, not an invitation to infer historical availability.

NO_BET=true; actual wagers $0; model promotion disabled. Existing NHL baseline and first-100 challenger remain unchanged.
