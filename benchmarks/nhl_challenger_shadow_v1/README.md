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
fail closed rather than producing synthetic data.

The existing prospective integrity reader validates official final settlements
and recomputes the original model, Elo and market scores from the original
frozen forecasts. The shadow produces a read-only mutable
`scoreboard.latest.json`, evaluating its own frozen probability on **those
same games**. An as-of report does not score a result whose verification
timestamp is in the future. Unpriced games count toward eligible prospective
shadow scores but cannot enter same-market paired comparisons.

The scoreboard reports settled/pending counts, unpriced/all-game probability
scores, identical-market-paired game metrics, independent Eastern scheduled
date block-bootstrap intervals where at least five blocks exist, and the
first-100-enrolled checkpoint. These are **descriptive**; five dates and/or
100 games cannot establish profitability or authorize wagering/model promotion.
The selected 2025 development candidate stays fixed; observing 2026 outcomes
may inform later research but must not modify this shadow's frozen weights.

The scheduled GitHub workflow `Sports prospective paper tests` runs the
isolated NHL challenger step after the existing NHL/MLB primary enrollment,
then stages only the existing prospective directories and the independent
shadow directory. This creates zero new sportsbook bets and requires no Render
deployment or user API keys.

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
