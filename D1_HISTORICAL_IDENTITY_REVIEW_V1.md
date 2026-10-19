# Historical D1-associated institution identity review

Run `python sports_historical_d1_identity_review.py` to assemble source-backed
review candidates from the completed NCAA-owned and ESPN archives. Both content
seals and all original receipts are verified first. Existing source quarantine
and cross-season provider-ID exclusions still apply. This reader adds no
runtime aliases and certifies no institutional identity or Division I membership.

A candidate requires the same home/away orientation and exact UTC start in both
sources, with one independently exact-normalized opponent name as its anchor.
There must be exactly one NCAA candidate for that anchor/time. At least two
distinct game pairs against two distinct opponents must support the institution
in **each** of the separate source seasons. NCAA slug and ESPN team ID must stay
stable, and name/slug/team-ID mappings must remain one-to-one across the packet.
Reused game identities and cross-season game-ID overlap cannot support a pair.

No fuzzy name distance, suffix expansion, nearest-time choice, score or outcome
selects the proposed institution. Changed starts, ambiguous anchors, insufficient
evidence and competing mappings are excluded from proposals. Exact spellings,
stable source identifiers, paired original game IDs, side, anchor, start time,
receipt/response hashes and observation times accompany every proposal.

The October 19 archive produces 127 candidate pairs and 112 excluded pairs.
These are institutions appearing in D1-associated games; visiting schools may
belong to other divisions. The packet is not an official membership directory.
Review remains required before any separate, pinned spelling policy could be
introduced. No training, historical evaluation, forecasts, promotion, outcome
grading or wagers are enabled. Source identity review cannot attest historical
pregame feature availability.
