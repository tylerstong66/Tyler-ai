# Native NBA Final break-status diagnostic

The original October 21 receipt `20261021T100537057931Z` requested October 20
and retained SHA256 `2be5aae7d00b49c52432de7e79bdf03e0facd646fbffba9aaf25f522be718bbf`.
Its three regular-season regulation-final cards have `gameBreakStatus: "Final"`.
The unchanged v2 parser requires an empty break status and therefore correctly
retains the whole page as `UNSUPPORTED_OR_NOT_COMPLETE_FINAL_PAGE`.

`sports_nba_final_games_page_v3.py` is an isolated, opt-in diagnostic reader
for the explicitly observed `Final` value. It shares the existing complete-page,
regulation-only, franchise identity, four-period score totals, unique teams,
season/date, explicit-null envelope and original response-clock checks. Empty,
missing and unknown break statuses fail. Mixed/live, overtime, postseason,
incomplete and inconsistent pages still fail as a whole.

Run `python sports_nba_final_games_page_v3.py --capture 20261021T100537057931Z`.
The command first exactly replays the original v2 receipt, then binds the
diagnostic to the same original bytes, manifest digest and receipt observation
clock. It repeats receipt verification with one fixed audit clock before
returning. No network request or repository write occurs. Integrated CI retains
this separate diagnostic artifact and checks tracked inputs remain unchanged.

The diagnostic reads three source claims, not three independently corroborated
outcomes. It enrolls no results, computes no accuracy, changes no feature or
forecast and supplies no publication or source-origin attestation. Existing
collectors and the native feature lifecycle continue using v2. A future
collector integration needs a separate versioned receipt protocol and evaluation
against independent ESPN originals; this diagnostic does not silently reinterpret
already canonical v2 manifests. NO_BET remains true, wagers zero and promotion
disabled.
