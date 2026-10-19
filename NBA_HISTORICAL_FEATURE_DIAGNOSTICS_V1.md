# NBA source-backed feature diagnostics v1

This NBA-only reader verifies both original source-content seals, replays the
separate exact-tipoff source crosscheck, and derives chronological team-form
features from the corroborated result subset. No model is fitted or evaluated.

Run `python sports_historical_nba_features.py --split train` or
`--split validation`. CI retains both outputs separately for 30 days.

Every target uses a cutoff one second before the earlier source scheduled
start. The fixed ten-game window describes prior mean points scored, allowed
and margin, plus days since the latest eligible prior scheduled start. Missing
history stays null; zero prior games means no eligible observations, not proof
that the team had played no games. Only the corroborated subset is represented;
the window does not certify a complete official schedule. Days between starts
are not measured rest after a verified game-completion timestamp.

Two entirely separate states expose the availability distinction:

| View | When a prior result becomes available | Historical claim |
|---|---|---|
| `observed_receipt_time` | Later of the original NBA and ESPN observation times | Verifiable receipt chronology only |
| `reconstructed_24h` | Later source scheduled start plus 24 hours | Explicit unverified reconstruction assumption |

No current-game score, same-time game, future game, or not-yet-available result
can enter a target's features. The most recent eligible games are chosen by
event time even if source receipts arrived out of order. Each call isolates one
season/split. No fitted coefficients, odds or probabilities are consumed, and
validation output never updates training state.

Every feature record carries original target and prior game IDs and SHA256
links into the accompanying accepted-source row index, whose original source
receipt and response hashes are replayed by the trusted reader. A protocol
digest and the complete source-crosscheck report digest accompany the output.
The cutoff is a diagnostic boundary, not a historical prediction freeze.

At the October 19 retained archive, 1,310 training and 1,315 validation target
games replay. Both-team reconstructed history exists for 1,294 and 1,299
targets respectively; **zero** have both-team prior history available under
the observed receipt timestamps, which were recorded after those seasons.
Reconstruction does not change that absence of original pregame evidence.

All training, historical evaluation, forecasting, promotion and wager guards
remain disabled. These diagnostics do not authorize a trained candidate,
certify historical pregame publication, or backfill paper predictions.
