# Fresh NFL paper test

Started October 11, 2026. The first **12** future-game forecasts were recorded between **11:28:39 and 11:28:40 a.m. Eastern**, before the first eligible 1 p.m. kickoff. Every game matched the pinned nflverse schedule and ESPN exactly by home team, away team and kickoff time. The already-started Eagles–Jaguars game was excluded. No original Tyler paper forecasts were altered.

[Current results and saved predictions](RESULTS.md)

## Frozen comparison

Use the v2 model frozen earlier on October 11 and the previously frozen v1 model, with no retraining or coefficient changes during this prospective test. `config.json` checks hashes for both models and their warmup snapshots. The inspected 2025 results are used only as completed pre-2026 feature history; they are not rescored to select parameters. New 2026 finals update feature state only after their eligibility delays.

For each eligible game within 24 hours of kickoff, save v2, v1 and the ESPN-observed DraftKings moneyline pair in one exclusive JSON artifact. Use the first recorded eligible forecast, retain its source snapshots and hash, and never overwrite it. A second run verifies the existing ledger rather than reissuing forecasts. Cap enrollment at 100 games. Original production cohorts remain separate.

The market quote is the **current quote observed at the saved retrieval time**, using ESPN's `close` slot. It is not a verified closing line. Remove two-way vig for conditional comparisons; exclude ties from binary metrics and retain them in full three-outcome scoring. No hypothetical staking, ROI or bet-placement code is included.

## Inputs and availability

Warmup: pinned 2010–2024 games and stats. Current history: 285 completed 2025 games and 65 completed 2026 games at initial retrieval. All 8,856 team-game stats pairs were checked against the corresponding schedule. Prior result eligibility assumes kickoff +24 hours and efficiency stats +48 hours, capped by actual generation time. No future result or live box score is consumed. Historical revised data cannot establish exact publication times; present-day retrieval proves only that the snapshot was available at this prediction cutoff.

The initial public source GETs completed from 11:20 to 11:21 a.m. Eastern. Their source response hashes and retrieval timestamps were retained. After shared unauthenticated GitHub API requests were rate limited, the first enrollment reused those same verified captures, under a 30-minute maximum age, without fabricating new retrieval times. Future scheduled runs fetch live sources and use the workflow's built-in GitHub token only for public GitHub metadata rate limits; no Tyler authentication or external account credentials are used.

Official NFL report publication metadata was checked before retaining **152 factual player game-designation records**, including QB statuses. These are game designations, not inferred inactive lists or confirmed starting quarterbacks. Player identity uses a source-team-and-name key rather than claiming a verified league player ID. Raw article text is not republished; extracted factual records and the original response hash are retained. Missing coverage stays unknown.

**QB and injury effects remain disabled in both frozen models.** Thus a model can prefer a team despite an important absence. This is a limitation of the experiment, not a claim of betting value. The evidence is saved for audit and a future separately trained candidate.

## Collection and scoring

The `NFL prospective paper test` GitHub workflow runs on merge, hourly at minute 15 and on manual dispatch. It makes public GETs, captures new eligible forecasts, and checks saved pending event IDs. A result is settled only when ESPN declares the event completed and final scores agree with the pinned schedule. ID, teams, kickoff and prediction hash must match. Conflicts remain pending and are logged. Collector failures retain an explicit incomplete-state error; they never count as successful collection.

Scores include paired binary Brier, conditional log loss, accuracy, full three-outcome losses and approximate season/week-block uncertainty once enough blocks exist. No model is promoted automatically. After 100 games settle, the runner stops fetching sources; the workflow remains manually available. Scheduled runs can be delayed, and schedules or sources can change, so enrollment and settlement timing are not guaranteed.

New snapshots are deduplicated by content hash. Existing predictions/results and the first run's evidence remain immutable. The saved `summary.json` and `RESULTS.md` update as verified results arrive. This repository test is separate from Tyler's existing private paper-results dashboard.

```sh
python -m pip install requests==2.32.5
python sports_prospective_test.py
python -m unittest test_sports_prospective_test test_sports_efficiency_candidate test_sports_historical_benchmark
```

NO BET. Actual wagers $0.
