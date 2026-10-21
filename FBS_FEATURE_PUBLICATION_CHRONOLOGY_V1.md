# FBS original feature server chronology

A separate GitHub server audit verified the exact five original FBS feature
files at immutable head `7e96214fae10b8794eaec51e7299939666d2772a`.
GitHub created archived-receipt workflow run 39303918194 at
2026-10-19T18:36:33Z, after their 18:31:11.792063Z freeze and before both
sources' saved starts for every record. The earliest saved start is October 20,
23:00 UTC. These are feature observations, not frozen predictions.

`sports_fbs_feature_publication.py` replays the protocol, original source
captures, crosswalk, historical source seals and reference features before
checking GitHub's server run identity and exact committed file bytes. It uses
the shared bounded fixed-repository evidence reader. Each file must satisfy its
own freeze <= server observation < both saved starts. Original FBS records
remain unchanged and continue to decline publication attestation themselves;
this separate report supplies the narrower server observation evidence.

The first verification used newly retrieved connected GitHub run, commit,
directory-tree and decoded file evidence because the unauthenticated API had
reached its rate limit. The adapter verified the run's exact head, traversed its
immutable tree to regular-file entries, preserved decoded original bytes and
bound those bytes to each original file's Git/SHA-256 digests. It did not treat
a parsed JSON document as REST file metadata. The CLI uses the direct bounded
GitHub API client, with optional GITHUB_TOKEN.

The retained report is
`benchmarks/fbs_pregame_reference_features_v1/publication_v1/first_cohort.json`.

```sh
python sports_fbs_feature_publication.py --replay benchmarks/fbs_pregame_reference_features_v1/publication_v1/first_cohort.json
```

Replay always queries GitHub again, revalidates the original sources and compares
all saved report fields except its new check time. The explicit original cohort
stays fixed as future records arrive. A saved JSON file is a replay recipe, not
standalone independent proof. CI tests the reader offline and verifies retained
file digests while explicitly declining fresh server attestation.

The claim covers GitHub server observation of these exact committed feature
bytes before saved scheduled starts. It does not certify repository public
visibility, source-origin truth, actual kickoff, current team strength or model
quality. Prior-season roster/coach changes and current-season form remain
unmodeled. No forecast, fitting, evaluation, promotion, runtime model activation
or wagering behavior changes. NO_BET remains true and wagers remain zero.

On October 21, the same auditor separately verified the remaining 45 future
feature records against GitHub run 39594047657, created at 11:43:19 UTC on
immutable head `f68aaf3ba2183a5a3688b1008b12dfb8407f20ac`. Every original
freeze preceded that server observation, which preceded both sources' saved
starts; the earliest of these games starts October 22 at 23:00 UTC. Connected
GitHub evidence traversed the immutable tree to regular-file entries and fetched
each original file as base64 bytes. No parsed document was treated as REST
file metadata. The existing auditor verified exact Git/SHA-256 hashes and
decoded bytes after replaying original source and historical dependencies.

The new recipe is
`benchmarks/fbs_pregame_reference_features_v1/publication_v1/remaining_cohort_20261021.json`.
Use the same CLI `--replay` option for a fresh GitHub API recheck. It verifies
45 records, overlapping two in the original five-record recipe; their union
covers the 48 feature records present at this checkpoint. The three games
whose saved starts had already passed are covered only by the earlier recipe;
this later observation does not retroactively attest them. These remain
features, not predictions. Offline CI checks retained bytes, individual
chronology and scope, without claiming a fresh GitHub server query.
