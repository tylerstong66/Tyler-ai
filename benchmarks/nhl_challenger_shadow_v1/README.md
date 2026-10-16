# NHL forward-only challenger shadow, v1

**NO BET — actual wagers $0. No live model changes or promotions.**

This is a distinct prospective NHL shadow cohort, not a replacement for the
NHL baseline and not a historical replay. It starts at the deliberately future
UTC activation instant pinned in [protocol.json](protocol.json). The source
candidate was selected from an **already viewed 2025 development validation**
using 2024 NHL training. This selection is not preregistered or blind, and
historical development confidence intervals cannot be treated as an edge.

The shadow does not request network data. It uses only the existing, source-linked,
immutable primary NHL forecasts once they have been published, reads the Elo
features **from that same pregame forecast**, and applies the 2024-fitted
ridge-logistic weights pinned and checked against the offline 2025 development
report. The forecast is saved in separate
`benchmarks/nhl_challenger_shadow_v1/predictions/<game_id>.json`
with a digest of its original pregame forecast, model and protocol. Every
existing shadow forecast is independently checked against the original.

**Hard enrollment conditions:** both original generation and recording must
be at or after the pinned activation; the source must be a valid NHL no-bet
forecast with its intact original SHA256; the shadow must be recorded after
source creation but strictly **before** the original kickoff. Any prior forecast
or started game is skipped, even when it would have been possible to calculate
a probability retrospectively. The original pregame model weights, forecasts,
market odds, game IDs and timestamps are never modified. Missing/faulty inputs
fail closed rather than producing synthetic data. Before writing **any** new
shadow forecast in a run, the script validates all retained primary forecast and
settlement links and all previously written shadow records. An unrelated bad
source snapshot or tampered existing shadow must not generate a partial shadow
batch that an always-run GitHub audit step could accidentally commit.

The existing prospective integrity reader validates official final settlements
and recomputes the original model, Elo and market scores from the original
frozen forecasts. The shadow produces a read-only mutable
`scoreboard.latest.json`, evaluating its own frozen probability on **those
same games**. An as-of report does not score a result whose verification
timestamp is in the future. Unpriced games count toward eligible prospective
shadow scores but cannot enter same-market paired comparisons.

The scoreboard reports settled/pending counts, unpriced/all-game probability
scores, identical-market-paired game metrics, and *paired challenger-minus-baseline*
Brier, log-loss and accuracy differences versus the frozen primary model,
fixed Elo, and only the same games with saved pregame market quotes. Negative
Brier or log-loss deltas favor the challenger; positive accuracy differences
favor it. Every paired analysis resamples Eastern scheduled-date blocks,
withholding confidence intervals below five blocks. Unlike subtracting
independently estimated errors, these deltas use exactly the same scored
outcomes. The first-100-enrolled checkpoint is reported separately. These are **descriptive**; five dates and/or
100 games cannot establish profitability or authorize wagering/model promotion.
The selected 2025 development candidate stays fixed; observing 2026 outcomes
may inform later research but must not modify this shadow's frozen weights.

### Post-activation primary-forecast coverage

The scoreboard separately audits every **saved** primary NHL forecast whose
original generation and recording both occurred after the challenger activation.
It counts the forecasts enrolled in the independent shadow, and lists any source
forecasts first encountered after their saved scheduled kickoff as
`MISSED_SOURCE_FORECAST_NOT_BACKFILLED`. These misses are retained rather than
silently manufacturing a late candidate prediction. Existing shadow records
are rejected if their timestamp is ahead of the audit clock or their original
generation predates activation, even if an attacker recomputes their self-hash.

This is a **saved-primary-forecast denominator only**. It cannot prove the
official NHL source returned all scheduled games; the source-coverage audit
remains separate. It never loosens the no-wager rule.

### Immutable first-100-enrolled checkpoint

Once the **first 100 shadow forecasts by original UTC recording time** are all
verified as settled, the runner writes
`checkpoints/first_100_enrolled/REVIEW.json` exclusively. It captures exactly
those 100 frozen prediction hashes, the selected verified score rows, Brier/log
loss/accuracy summaries for the challenger and both original comparators,
and paired challenger-minus-baseline differences. It reports all 100 games
even when some have no saved market prices; market comparisons include only
their actually priced subset. A pending game within the first 100 must finish
before the checkpoint can be saved. Later games can never replace it.

Every subsequent run recomputes the checkpoint from its pinned inputs and
requires byte-equivalent JSON data, failing rather than silently overwriting
if any saved prediction, result, selection, or checkpoint content differs.
The mutable scoreboard points to the preserved checkpoint once available.
This checkpoint requests **human research review only**, with no promotion
or real wagering authorization.

### Prospective calibration and probability spread

The cumulative scoreboard and the immutable first-100 review independently
report fixed five-bin **home-win calibration** and the mean distance of predicted
home probability from 50%. They compare the 2024-trained challenger with the
already-frozen primary NHL model and fixed Elo on all eligible settled games.
They also compare all three with the saved pregame market on the **identical
originally priced games**. No postgame odds, historical challenger selection
results or omitted unpriced games enter the same-market cohort.

These diagnostics describe reliability and confidence concentration, not
predicted betting profits. Bin-wise Wilson observed-rate intervals assume
independent games and can be misleading for small or dependent samples;
the date-block Brier/log-loss uncertainty elsewhere in the report remains
separate. Empty samples report unavailable values, not artificial success.
No feature fitting or production model selection is triggered.

The scheduled GitHub workflow `Sports prospective paper tests` runs the
isolated NHL challenger step after the existing NHL/MLB primary enrollment,
then always stages the independently collected original prospective evidence,
but stages the separate challenger directory **only if the shadow verification
step completes successfully**. Failed shadow runs cannot accidentally publish
half-written immutable challenger predictions merely because GitHub's general
audit-preservation step still executes. This creates zero new sportsbook bets
and requires no Render deployment or user API keys.

## Reproduce

```bash
python -m unittest -v test_sports_nhl_challenger_shadow
python sports_nhl_challenger_shadow.py
```

The script is offline. The unit tests use synthetic games and exercise future
source rejection, after-start rejection, immutability and digest failures,
a verified completed game, and withholding future-dated results.

**The frozen run was authored and merged before its future activation; do not
claim that any prior 2026 games were part of this independent prospective trial.**
