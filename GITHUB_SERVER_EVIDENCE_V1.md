# Shared immutable GitHub evidence reader

`sports_github_server_evidence.py` centralizes the existing NBA/MLB publication
readers' fixed-repository HTTPS transport, server run metadata checks and exact
immutable JSON blob verification. The sport-specific readers retain their own
cohort identity, source replay, freeze/start chronology and report schemas.
Original records and saved NBA/MLB reports are unchanged.

The client accepts only this repository's numeric workflow-run endpoint and
benchmark JSON file paths at a literal 40-character commit SHA. Traversal,
foreign origins/repositories, arbitrary API routes and mutable refs fail before
network access. Responses are streamed with a 1 MB bound, explicit timeouts and
redirects disabled. Optional GITHUB_TOKEN goes only into the request header.

Run metadata must match the caller's expected workflow and event, exact
repository/head repository/run ID and an aware server timestamp no later than
the audit clock. File evidence must match regular-file type, exact path, size,
Git object SHA and decoded original bytes. Neither a hash alone nor a matching
file name is enough. Original benchmark bytes are also bounded.

This common layer establishes no sport-specific eligibility and cannot certify
source truth, public visibility, actual event start or model quality. Callers
must still require their own freeze <= server observation < each saved start,
validate original sources and keep saved-report replay separate from a live
server query. No model, forecast or wagering behavior changes.
