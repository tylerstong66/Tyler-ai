# NBA original feature chronology, version 1

The first prospective NBA reference-feature cohort has 16 records frozen at
2026-10-19T13:33:36.525177Z. GitHub's server created archived receipt workflow
run [39262563627](https://github.com/tylerstong66/Tyler-ai/actions/runs/39262563627)
at 2026-10-19T13:43:22Z with immutable head
`f160b9ba98148b67dd8ecb077e27b291a39a9361`. A live API audit verified the
exact bytes of all 16 feature files at that head. This precedes both sources'
saved start times for every record; the first saved start is October 20, 19:00 UTC.

`sports_nba_feature_publication.py` first replays original source-backed feature
records and both historical source seals. It then queries the fixed repository's
workflow run, requires its repository/head repository/workflow identity, uses
GitHub's server `created_at` rather than author-controlled Git commit dates,
and fetches each file at the run's exact head SHA. File path, regular-file type,
size, Git blob SHA-1, decoded original bytes and SHA-256 are bound together.
Every enrolled record must satisfy freeze <= server observation < both saved
starts. Wrong repository, fork, run, workflow, future timestamps, mismatched
bytes or any late/unavailable member fail the complete requested audit.

The retained report is
`benchmarks/nba_pregame_features_v1/publication_v1/first_cohort.json`.
It records the exact member IDs, hashes and API observation. A saved JSON report
is a replay recipe, not standalone independent proof. Replay always queries
GitHub again, revalidates original sources and compares the full report except
its new check time. It retains the explicitly listed original cohort when new
feature records are added; it makes no claim about those additional records.

```sh
python sports_nba_feature_publication.py --replay benchmarks/nba_pregame_features_v1/publication_v1/first_cohort.json
# Audit every currently retained record against another specific server-observed head:
python sports_nba_feature_publication.py --run-id RUN_ID
```

The API client uses bounded HTTPS responses and an optional `GITHUB_TOKEN` for
GitHub rate limits. CI runs offline regression tests; network failure cannot be
silently converted into successful attestation. Unavailable or deleted GitHub
evidence makes live replay fail.

The claim is limited to GitHub server observation of exact committed feature
bytes before saved scheduled starts. It does not certify repository public
visibility, actual tipoff, source-origin accuracy or prediction performance.
No existing feature record is changed. These remain features, not predictions;
NO_BET is true, wagers are zero, and training, historical evaluation, forecasting
and promotion remain disabled.
