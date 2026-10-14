# Automatic prospective benchmark reviews

`python sports_benchmark_review.py` reads the saved NFL, NHL and MLB forecasts
and settled result files. It performs no network requests, enrollment,
settlement, training, model changes, or wagering. The existing collection
workflow generates reviews after its collection steps, even if one sport fails,
then preserves the review alongside the audit records. Reports are linked from
each sport's existing results page and from [the overview](REVIEW_ALL.md).

## Samples and scoring

- Every game counts once per sport, regardless of how many models score it.
  Cohorts remain separate.
- NHL/MLB model and fixed-Elo scores cover all decisive settlements, including
  unpriced games. Market comparisons use exactly the same priced games for
  every model.
- NFL v2/v1 three-outcome Brier, log loss and argmax accuracy include ties.
  Conditional two-way scores exclude ties, and market comparisons also require
  a saved pregame market probability. A two-way market cannot fairly receive a
  three-outcome score without a saved tie probability.
- Brier is the sum of squared errors over outcomes (range 0–2), so two-way
  Brier is `2*(p-y)^2`. Log loss uses natural logarithms; lower is better.
  Existing binary scoring clips probabilities to `[1e-12, 1-1e-12]` for log loss.
- Accuracy selects the highest probability, with home winning an exact
  two-way probability tie. NFL three-way argmax uses home, away, tie order.
  Accuracy differences are percentage-point differences.

## Calibration and uncertainty

Five fixed bins cover `[0, .2), [.2, .4), [.4, .6), [.6, .8), [.8, 1]`.
Conditional-home calibration uses decisive games. NFL also reports each full
outcome separately across all settled games. Empty bins are unavailable, never
zero performance. Observed-rate Wilson 95% intervals are explicitly labelled
as descriptive intervals assuming independent games.

Mean-score and paired-difference uncertainty uses 2,000 deterministic percentile
block-bootstrap resamples, seed `20261014`. NFL blocks are season/week; NHL/MLB
blocks are the Eastern scheduled game date. Resampling retains all games within
a selected block, and each draw is weighted by its resulting number of games.
Paired differences use model minus baseline on the same games and same blocks.
Negative Brier/log-loss differences favor the model; positive accuracy
differences favor the model.

Intervals are withheld below five blocks. This is a minimum reporting guard,
not a claim that five blocks is enough for reliable inference. Dependence across
blocks can remain. Reports are exploratory/descriptive, are repeatedly updated,
and are not sequential tests or automatic model-promotion decisions. These
review calculations were added after initial results were observed; they are
not represented as a preregistered confirmatory analysis.

## Integrity, completion, and milestone

The reader verifies forecast hashes, pregame and market/source timestamps,
result-to-forecast hash linkage, final score/outcome consistency and matching
metadata. It recomputes each stored score from saved probabilities and the
settled outcome; disagreement with the stored score withholds that cohort's
metrics and fails the review step. Other cohorts still receive reports.
Missing directories are errors. Reports contain a digest of their exact inputs.
They do not independently re-fetch or re-adjudicate official game outcomes;
result provenance remains the collector's saved evidence.

Latest capture completion, per-game errors, exclusions, optional availability
errors and any newer saved collection failure remain visible. The NFL manifest
lacks a completion flag and must be corroborated with the successful workflow
run. A newly generated review does not itself prove collection succeeded.

`review_due=true` and `review_status=ready_for_human_review` begin at 100 verified
settlements per sport and remain true thereafter. Counts of settled, decisive,
priced, and independent time blocks remain visible. An integrity error makes
the milestone unverifiable (`review_due=null`), not an inferred zero.
This reporting flag does not alter existing enrollment rules, authorize
retraining, stop the monitor, or establish profitability.

**NO BET — actual wagers $0.**
