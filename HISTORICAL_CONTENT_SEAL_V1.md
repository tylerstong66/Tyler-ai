# Frozen historical input content seal

`sports_historical_content_seal.py` verifies the original completion snapshot's
fixed v1 input scope: the 1,104 provider day responses/receipts and 42 FBS-owned
week responses/receipts, totaling 2,292 original files. It recomputes every byte
hash and the sorted-index SHA256 and compares it with the frozen completion
manifest. Missing/nonregular/oversized files or altered research guards fail.

This catches a coordinated change to a source and its matching daily receipt,
even if the receipt's individual response hash was also updated. CI checks the
seal, and historical acquisition checks it before fetching additional evidence.

The v1 scope is reconstructed from the original league/season date protocol and
FBS week index, not from an unrestricted current directory glob. Legitimate new
D1/NBA independent source directories can append without changing or silently
reinterpreting the old v1 seal. Future protocol changes need a separate version.

This is a byte-integrity check. It does not attest source origin, publication
time, semantic correctness, schedule completeness or model eligibility. Those
checks remain separate; training/evaluation/forecasting/promotion/wagers stay off.

All 467 offline sports tests passed. The actual v1 2,292-file snapshot verifies;
regressions cover coordinated changes, missing files, enabled guard metadata
and append-only addition of an independent source scope.
