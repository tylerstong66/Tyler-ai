# Native NBA daily source collection in the shared workflow

The existing `college_nba_source_observation.yml` workflow collects both
original v1 and separately versioned v2 source observations. The v2 step runs
only after fresh ESPN archives pass their original-body audit. It requires
the complete next Eastern date to match exact teams and UTC tipoffs, while
all games are still regular-season pregame at the actual response clock.

Each version's success or failure is reported independently. A v2 daily
success cannot certify the full-season endpoint, silently replace a failed
v1 receipt, enable feature enrollment, or turn on forecasts. The status
receipt retains both the trigger SHA and the exact current-main revision
checked out when the serialized run began.

Only successfully collected and replayed v2 captures are published.
The exact new raw body and canonical receipt are also retained as a CI
artifact. Capture paths do not trigger this workflow, so publication cannot
start another collection loop. The existing schedule is unchanged; GitHub
schedule delivery remains best effort.

NO_BET=true; actual wagers zero. Training, forecasting, promotion, and
independent final-outcome certification remain disabled.
