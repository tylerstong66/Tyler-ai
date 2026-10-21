# Native v3 frozen-feature source comparison

This opt-in, read-only diagnostic compares a specified, exactly replayed native
v2 postgame receipt through the separate Final-break-status v3 reader against
an independently audited ESPN receipt and the original frozen NBA features.
It does not create a new receipt or change the scheduled v2 lifecycle.

Reproduce the inspected source pair:

```
python sports_nba_v3_feature_diagnostic.py \
  --capture 20261021T100537057931Z \
  --provider-capture 20261021T100530748795Z
```

Without `--provider-capture`, the command uses the latest retained ESPN receipt;
it never falls back from an invalid receipt. Explicit capture identifiers are
bounded timestamp names. Both sources' original hashes and receipt clocks are
reported. Source claims use the original complete-response clock, never the
later inspection time. All frozen features and their original source and
historical-reference dependencies are replayed before comparison.

The pinned pair yields two source-agreement observations for `0022600001` and
`0022600002`. Game `0022600003` remains quarantined: NBA reports 01:30 UTC while
ESPN reports 01:50 UTC on October 21. Both original pregame starts were 01:30.
The original starts and 20-minute ESPN drift remain visible; agreeing scores
cannot override the exact-start gate. The comparison also retains both-team
identity, scope, original/current-start, freeze and source-reported actual-end
chronology checks. Dates outside the requested NBA page remain outside scope.

These are observations attached to frozen feature records, not model predictions
or enrolled outcomes. The existing v2 lifecycle still reports the unsupported
page and zero accepted final cards. No accuracy, training, forecasting, historical
evaluation, settlement or promotion is enabled. NO_BET=true and actual wagers zero.
