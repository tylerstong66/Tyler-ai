# Preserved first-100-enrolled reviews

The cumulative reviews continue to update for every verified result. Their
`review_due` flag still begins at 100 settled games. A separate checkpoint
preserves one fixed enrollment window per independent NFL/NHL/MLB cohort.

## Selection and completion

Select the first 100 saved forecasts by `recorded_at` converted to UTC, breaking
exact timestamp ties with `game_id`. Do not select on prediction, outcome,
market-price availability, kickoff order, or which game settles first. If a
game in the selected window is delayed, the checkpoint waits for it; a later
settlement cannot substitute for it. Ongoing enrollment and cumulative scoring
continue. A permanently unresolved selected result leaves this checkpoint
pending and visible for review; no automatic replacement or imputation occurs.

Before completion, `first_100_checkpoint` reports `collecting_forecasts` or
`awaiting_selected_results`, plus selected, settled, pending, and remaining
enrollment counts. These are counts of games, never numbers of model scores.
The fixed window and cumulative 100-settlement flag can reach readiness at
different times. This checkpoint rule was added after early results were
observed. It is an evaluation audit improvement, not a preregistered or blind
confirmatory test, a new forecast cohort, or independent validation of the
earlier exploratory analyses.

When all selected forecasts have verified results, the existing offline review
step saves `checkpoints/first_100_enrolled/REVIEW.json` and `REVIEW.md` under
that cohort. The JSON retains the ordered game IDs, exact forecast/result input
digest, recalculated metrics, calibration, descriptive block uncertainty, and
collection evidence visible at creation. Selection includes NFL ties and
unpriced forecasts. NFL ties remain in three-outcome evaluation and outside
decisive two-way comparisons; market comparisons use only the same eligible
priced decisive games. Other models still receive all eligible games.

## Preservation and integrity

Later review runs validate the saved JSON digest and Markdown digest, the
selection order, and the selected forecast/result input digest. They do not
rewrite a completed snapshot as later games settle or capture metadata changes.
Removing a selected record, inserting an earlier enrollment, modifying selected
inputs, corrupting a saved report, or leaving only one checkpoint file produces
a visible checkpoint integrity error. Existing files are retained for review.
Changing the checkpoint rules requires a separately named/versioned analysis,
never silent replacement of the preserved review.

Checkpoint errors do not erase otherwise verified cumulative metrics or block
other leagues' reports. They do fail the review command's exit status so the
existing workflow exposes the error and retains audit records. A corrupt
forecast/result still fails the existing whole-cohort scoring integrity check.
An unrelated later collection failure remains visible in the current review;
the checkpoint's original collection evidence is historical, not a claim of
current service health.

The existing collector workflow already runs and saves the review step. This
change creates no new schedule, dispatch, network calls, forecasts, settlements,
training, model promotion, or wagers. There is no saved checkpoint until its
actual selected results exist; tests use synthetic data only in temporary
directories.

Hashes provide reproducible input linkage and accidental-change detection,
not a cryptographic signature or an independent re-adjudication of official
finals. Probability quality, market comparisons, calibration, and uncertainty
still require human assessment. Repeated monitoring intervals are descriptive,
not sequential significance tests. Neither 100 settlements nor preservation
establishes a profitable betting edge.

**NO BET / actual wagers $0.**
