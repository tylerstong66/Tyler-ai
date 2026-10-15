# MLB hitter pregame shadow publication integrity v1

Research-only. No betting actions, model promotion or changes to production Tyler AI.

## Why this matters

Seven MLB 1+ hit/HR conditional shadow predictions were previously committed for October 15, 2026. We can evaluate them as pregame forecasts only insofar as we establish they were recorded before their corresponding games, remained unchanged, and were settled after official final results. A SHA-256 digest by itself does not establish when a file was actually published.

## Added safeguards

1. \`sports_mlb_prop_publish_guard.py\` inspects **all** staged Git paths and status codes: it requires each file to be a brand-new \`A\` addition under the immutable prediction directory. Modifications, deletions, renames, paths outside the directory and after-cutoff predictions fail closed. The JSON seal, game/player filename, NO BET flags and the minimum three-minute publication margin are revalidated.
2. \`sports_mlb_shadow_publication_audit.py\` reads **full Git history** to verify every prediction had exactly one file-changing commit, that the file was originally **added** rather than edited, and that its original committed Git blob still equals the current on-disk bytes. It compares author/committer Git metadata against the recorded freeze timestamp and official scheduled first pitch.
3. The daily pregame capture workflow fetches full Git history, tests the guard, refuses modifications and audits the entire immutable prediction corpus after the new commit, before pushing.
4. The separate scheduled GitHub read-only audit checks original history and full-byte equality again.

### Important evidence caveat

**Git commit author/committer timestamps are not independent receipt timestamps.** A Git author can set these timestamps, and the SHA-256 hash only commits to content, not when GitHub received the push. The report therefore explicitly states \`prospective_proof_established=false\` and \`independently_attested_publish_times=0\`, even when all commit metadata is chronologically consistent and historical edits are absent. Independent GitHub Actions run creation times and server-side publication receipts are useful additional corroboration where available, but they are not manufactured here.

The audit detects concrete publication-integrity problems and makes the evidence more transparent; it does not establish profitable sports betting, unconditional real prop probabilities, or statistical model skill.

## Usage

\`\`\`bash
python -m unittest -v test_sports_mlb_shadow_publication
python sports_mlb_shadow_publication_audit.py
python sports_mlb_prop_publish_guard.py   # only during a scheduled capture with new files staged
\`\`\`

The history audit requires a non-shallow repository checkout (\`fetch-depth: 0\`). The publication guard expects **only added prediction files staged** and refuses to run on an empty index.

The scoreboard continues to distinguish 7 frozen player-game records from 1 distinct MLB event and all pending/ineligible/settled states. Existing frozen files are never rewritten to add attestations.
