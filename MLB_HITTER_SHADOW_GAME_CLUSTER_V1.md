# Game-cluster-aware MLB hitter shadow scoring v1

The first frozen MLB hitter forecasts comprise seven players from **one official MLB game**. Those outcomes share an opponent, venue, weather, scheduling and game script. Treating them as seven independent games would dramatically overstate the model's precision. This research-only upgrade builds an explicit game-cluster uncertainty gate into the scoreboard.

## Comparison

Score \`1+ hit\` and \`1+ HR\` **conditional on recording at least one official at-bat**, only for verified settled forecasts. The model is compared with unchanged exploratory reference probabilities (0.60 for 1+ hit and 0.08 for 1+ HR), not with any real FanDuel line or bookmaker market.

A descriptive mean loss difference is reported as \`fixed_prior_Brier - shadow_model_Brier\` (positive favors the shadow model).

Only after **at least 30 distinct officially settled games AND at least 150 eligible player-game observations** for the event will the report calculate a deterministic 600-replicate **game-cluster bootstrap percentile interval**. The bootstrap resamples full *game clusters*, keeping teammate outcomes together, and reports the 95% interval for the reference-minus-model Brier difference.

Until those thresholds are met, no interval or statistical superiority marker is reported. Meeting them is not proof of calibration, generalizable edge, profitability or independent GitHub server timestamp attestation.

## Remaining limitations

- Repeated players across separate games can remain dependent. This game-cluster bootstrap only protects against same-game overcounting, not all longitudinal correlation.
- The selected player sample is not statistically random, and the conditional-at-bat event differs from actual sportsbook settlement rules.
- The static reference priors are exploratory, not actual betting odds or a professional model.
- Frozen SHA256 predictions and Git metadata require independent publication-time verification for true prospective claims.
- No sportsbook odds or real wagers are involved.
- Positive intervals can indicate a retrospective Brier difference but **cannot by themselves demonstrate a profitable betting edge**.

Results appear under \`metrics.hit.game_cluster_uncertainty\` and \`metrics.hr.game_cluster_uncertainty\` in the existing scoreboard and its public GitHub snapshot. Tyler's authenticated \`sports mlb shadow scoreboard\` command already includes these metrics; no new Render application version is required.

Run:

\`\`\`bash
python -m unittest -v test_sports_mlb_shadow_uncertainty test_sports_mlb_prop_shadow_scoreboard
python sports_mlb_prop_shadow_scoreboard.py
\`\`\`

The original seven forecast files and any settlements stay untouched.
