# MLB original forecast server chronology

A live GitHub API audit verified the exact bytes of 22 independently frozen
forecast files: 19 hitter records and three winner records across games
849810, 849816 and 849817. The file cohort is explicit and stays fixed as future
forecasts arrive. Existing predictions and their original no-bet guards remain
unchanged. The separate schedule audit still exposes +8/+120-minute drift.

The report uses these GitHub server workflow creation timestamps:

| Run | Server-created UTC | Immutable head | Original files covered |
|---|---|---|---:|
| 38823222875 | 2026-10-15 23:22:53 | fffbce21aea93b20aa2289894432f099babe91e6 | 9 |
| 38960280012 | 2026-10-16 20:10:16 | 956631461effce9df395fbdde74777378341ced5 | 6 |
| 39054406857 | 2026-10-17 17:35:11 | 836a0d21dc685449ac528895e5889153da3467a3 | 7 |

Each scheduled scoreboard run identifies a fixed commit containing the exact
forecast blobs. The auditor verifies repository/head repository, scheduled event,
workflow path, run ID and 40-character commit SHA. It fetches each original file
at that exact head and checks regular-file type, path, size, Git blob SHA-1 and
decoded bytes against the separately verified record and file SHA-256. Every
file must satisfy its own freeze <= server observation < original saved start.
The later hitter start cannot substitute for the winner cohort's earlier start.
Git author/committer dates are not used as server evidence.

The explicit retained recipe is
`benchmarks/mlb_cohort_publication_v1/first_three_games.json`.

```sh
python sports_mlb_cohort_publication.py --replay benchmarks/mlb_cohort_publication_v1/first_three_games.json
```

Replay revalidates retained original cohort records and source evidence, queries
GitHub again and compares the entire report except its new check time. A saved
JSON file alone is not independent server proof. API loss, unavailable runs,
changed files or late timestamps fail live verification. The fixed-origin,
bounded client supports optional `GITHUB_TOKEN`; no token is printed or saved.
CI runs offline tests and checks that retained file metadata matches the recipe;
it explicitly does not claim fresh server verification.

The claim is narrow: GitHub's server observed commits containing these exact
forecast bytes before their saved scheduled starts. It does not establish
repository public visibility, original source accuracy, actual first pitch,
calibration or profitable performance. Older hitter records still lack original
response bytes, and winner sources are reduced snapshots. Original-source
validation remains incomplete, so issue #98 remains open. The cross-cohort
schedule module itself continues to report that it did not perform server checks;
this separate report supplies the publication evidence without rewriting it.

No new forecasts, fitting, historical evaluation, merged cohort metrics, model
promotion, runtime activation or wagers are enabled. NO_BET remains true.
