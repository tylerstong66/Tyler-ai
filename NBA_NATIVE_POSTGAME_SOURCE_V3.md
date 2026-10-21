# Isolated NBA native Final-break source protocol (v3)

The explicitly opt-in observer accepts literal Final break status in the strict null-envelope NBA regulation-final page. It reuses the existing recent-date request and response clocks, bounded transport, append-only compressed original body, canonical receipt, original-byte replay, and zero-to-three-day Eastern lookback. Prior v1 and v2 receipt roots and parser contracts are unchanged.

Run python sports_nba_postgame_observation_v3.py --audit to replay the isolated root, or --collect --days-back 1 for an explicitly requested live capture. The default CLI is inert. A separate source-only workflow step now explicitly invokes the v3 collector after the unchanged ESPN replay gate, audits every retained v3 receipt, and publishes only verified original archives. V3 has its own run artifact, success and page-status fields; v2 flags remain unchanged.

An unsupported overtime, live, partial, malformed, postseason, or mixed page retains the original bytes with zero supported final games. A source page is not independently corroborated, does not attest actual tipoff, cannot grade forecasts or enroll outcomes, and never enables models, training, settlement or wagers. Previously saved v2 source bytes remain original v2 receipts, even when a separate diagnostic can inspect their Final-break format.

Future integration must include independent original receipt and counterpart verification, preserve the existing v2 lifecycle, and maintain separate status and artifact fields. No full-season NBA source access or prediction readiness is claimed. NO_BET=true, actual wagers zero, no model promotion.
