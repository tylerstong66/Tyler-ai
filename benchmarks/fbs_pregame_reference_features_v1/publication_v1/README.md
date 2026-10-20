# FBS reference-feature publication receipts

The two reports bind ten original FBS reference-feature files to separate
GitHub server observations before both source-reported scheduled starts.
They do not rewrite feature records or source receipts.

The second five records were frozen by the existing collector at
2026-10-20T00:18:00.941101+00:00. They are games 401858271, 401858272,
401861965, 401862808 and 401864525. Their original saved starts run from
October 23 at 23:00 UTC through October 24 at 02:30 UTC.

GitHub archive-check run 39416209392 was created at 2026-10-20T11:36:56Z
against immutable head 29f0b3f75d65af710aeaab921657a147b516e1b5. Native run
metadata, Git tree entries and decoded original blobs were checked before
preparing the second report. The CI workflow freshly replays both reports
through GitHub's native run and contents APIs, including exact sizes, blob
SHA1s, decoded original bytes and all original source/feature checks.
A saved report alone requires that fresh API replay; inspect the workflow
result before calling it independently verified.

```
python sports_fbs_feature_publication.py --replay benchmarks/fbs_pregame_reference_features_v1/publication_v1/first_cohort.json
python sports_fbs_feature_publication.py --replay benchmarks/fbs_pregame_reference_features_v1/publication_v1/second_cohort.json
```

The claim is limited to exact original bytes observed by GitHub after freeze
and before both saved starts. It does not attest source origin, public
repository visibility, actual kickoff, predictions, model performance or
wagering value. No fitting, evaluation, forecasts, promotion or wagers are
enabled. NO_BET remains true and actual wagers zero.
