# MLB immutable prospective hitter shadow ledger v1

**NO BET — not live player-prop advice.** This module is explicitly separate from production Tyler AI (current v2.19.3.38). The task is to collect genuinely frozen future-event evidence, not to claim a profitable betting model.

## Freeze before first pitch

\`\`\`bash
python sports_mlb_prop_prospective.py capture --game-id 849810 --hitter-id 683734 --hitter-side away --output benchmarks/mlb_hitter_props_shadow_v1/predictions/849810_683734.json
\`\`\`

The above game is a historical October 15, 2026 example. The command must run before *that particular event's scheduled first pitch*, otherwise it fails.

It checks MLB official game ID, pregame status and scheduled first pitch, participant's active-roster identity and team side, and sufficient regular-season per-game historical data. The conditional experimental model uses **only previous local-date games**, never game-day stats or any same-day doubleheader outcomes. The serialized forecast includes fixed model version, two conditional event probabilities (1+ hit, 1+ HR **given at least one AB**), source retrieval receipts, evidence digests, freeze timestamp, and its own SHA256 content seal. Records are written by exclusive file creation (\`open('x')\`); existing predictions cannot be overwritten.

For verifiably *prospective* evidence, the frozen file must also be committed to GitHub **before first pitch**, and the GitHub commit date, repository visibility and GitHub workflow logs must be retained. File hash alone cannot prove pregame publication time.

## Independently settle a final

\`\`\`bash
python sports_mlb_prop_prospective.py settle --prediction benchmarks/mlb_hitter_props_shadow_v1/predictions/849810_683734.json --output benchmarks/mlb_hitter_props_shadow_v1/settlements/849810_683734.json
\`\`\`

Settlement occurs only after official MLB game final state, verifies game ID, start time, both team IDs and hitter player ID against the frozen prediction, and reads *official final boxscore* batting counts. It produces a **separate sealed record** referencing the prediction's exact original digest. The prediction is never edited.

If the hitter is absent from the official final boxscore or records **zero at-bats**, the record is *ineligible for this conditional event metric* rather than a false loss. If at least one official AB occurs, the settlement saves observed 1+ hit and 1+ HR labels and Brier errors for the exact frozen probabilities.

It does **not** decide sportsbook void/resettlement rules. This is not an executable wagering ledger; actual wager count remains zero.

## Testing

\`\`\`bash
python -m unittest -v test_sports_mlb_prop_prospective
\`\`\`

Tests cover identity, timestamps, model readiness, immutable digests, exclusive writes, finalized scoring, no-AB ineligibility, missing boxscore, wrong player, and after-start suppression.

## What must happen next

1. Actually freeze at least one official upcoming MLB event and commit the exact file to GitHub **before first pitch**. Record GitHub server commit time as independent time evidence.
2. After final, settle the event into a **different file** without rewriting prediction.
3. Repeat prospectively across many games, seasons and players; address lineup appearance/void rules and price quotations before comparing to betting markets.
4. Never label a conditional at-bat event probability as the unconditional chance a real sportsbook ticket wins. Never promote to betting recommendations based on a frozen handful of predictions.
