# Immutable MLB hitter shadow scorecard v1

A read-only evaluator for the frozen MLB conditional 1+ hit and 1+ home-run research experiment. It is intentionally *not* a real-money betting record, source of sportsbook prices, or calibrated prediction model.

Run locally from the repository root:

\`\`\`bash
python sports_mlb_prop_shadow_scoreboard.py
python -m unittest -v test_sports_mlb_prop_shadow_scoreboard
\`\`\`

## Model audit

Read original sealed \`benchmarks/mlb_hitter_props_shadow_v1/predictions/<game_id>_<hitter_id>.json\` forecasts, verify content hashes, status, pregame timestamp and player/game identities. Read settled results from a **different** directory, verify their hashes and pointers back to the exact original freeze, and verify outcomes and Brier values against unchanged model probabilities.

The report separates:

- Frozen player-game forecasts, and distinct official MLB game IDs.
- Pending (game not yet officially settled), ineligible (zero AB or absent final boxscore), and scored outcomes.
- The number of distinct games that have eligible player outcomes (to avoid counting teammates as independent game environments).
- Brier and log loss for 1+ hit and 1+ HR, compared with fixed exploratory priors (0.60 and 0.08) for the deliberately **conditional on 1+ official AB** event.
- The fact that independent GitHub *server* pregame publication attestations are not contained in this local report. Check commit timestamps separately.
- Explicit false flags for demonstrated market edge, calibration and actual wagering.

The scoreboard reads only; it never edits an original prediction or a final result, never fetches sportsbook prices, and never places bets. A lower loss compared to fixed experimental priors does **not** establish profitable predictions or calibrated forecasts. The selected sample and within-game correlation limit generalization.

The official-final collection workflow prints this report after each run (no extra write to forecast files). Its first population consisted of seven hitter forecasts from one Brewers-Dodgers contest on October 15, 2026; all of those files were committed prior to their official scheduled first pitch. Until the game is official final, the expected report is **7 pending, 0 scored**, not an accuracy number.

Future improvements need independent publication timestamp attestation, confidence intervals by date/game cluster, more diverse hitter/game samples, verified actual lineup and at-bat exposure, known sportsbook settlement rules, and legitimate odds/closing-line collection.
