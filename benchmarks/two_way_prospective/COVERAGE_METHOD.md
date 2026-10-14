# Forecast and odds coverage audit

**NO BET — actual wagers $0.**

`python sports_benchmark_coverage.py` reads saved artifacts only. It verifies forecast/result linkage through the scoring review validator and verifies hashes of retained official schedule and ESPN scoreboard snapshots before counting games. Each cohort is audited independently. Every capture workflow refreshes the coverage reports after collection and scoring review, including when a source step fails.

## Enrollment denominator

The audit starts at each cohort's saved start/freeze timestamp. It reconstructs the latest observed official schedule by game ID and lists games scheduled through the latest source observation plus 24 hours. NFL scope remains its frozen regular-season, 100-forecast protocol; NHL/MLB include their existing eligible regular-season and playoff schedules and continue enrollment. Games before cohort start are outside scope.

Started scheduled games without predictions are surfaced separately from games awaiting enrollment and games whose normal scheduling status is unverified. Pregame schedule observations within the 24-hour window distinguish an observed enrollment opportunity from a gap without such an observation. They do not prove all feature, venue, identity and provider eligibility gates passed. Captures now retain explicit decisions, including already enrolled, outside window, started, excluded, and NFL's cap. Saved exclusion reasons are retained, including resolved ones.

This denominator is limited to official games actually present in retained snapshots; it cannot prove the upstream source returned a complete schedule. Source absence, uncaptured failed attempts, and schedule revisions can leave unknowns. Postponed or suspended games are not declared missed eligible games solely from their nominal start time. Conflicting or revised schedules warrant inspection rather than an invented zero-gap guarantee.

The report lists the largest intervals between audited capture directories (explicitly incomplete manifests are skipped). These expose possible collection delay; they neither measure continuous uptime nor prove scheduler failure. Source observation timestamps can precede capture creation when a verified cache is reused. No historical forecast is reconstructed, generated or backfilled by this audit.

## Prices at enrollment versus later prices

Original forecasts and benchmark metrics continue to use only their immutable enrollment-time market field. NFL's priced ties count as priced coverage but are excluded from decisive binary market comparisons. NHL/MLB games count once, regardless of model count.

Both collectors now retain compact odds diagnostics: number of bookmaker records, usable paired current moneylines, missing pairs and malformed prices. Only two valid American moneylines from the same provider's current slots form a pair. Opening, spread, total, one-sided or invalid prices are not substituted. Invalid price records are diagnosed without blocking an otherwise valid model forecast.

Older reduced snapshots retain usable pairs but not the original bookmaker schema. An empty reduced `odds` list proves the parser exposed no usable pair; it does not establish whether the raw source had no odds, unsupported fields, or invalid values. Reports explicitly preserve this uncertainty.

Later **archived pregame** pairs can explain why a first-capture price was missing. These are audit evidence only and are not retrospectively promoted into a new market cohort or scored comparisons. Postgame observations never repair missing prices.

For future collections, `sports_market_evidence.collect_followups` saves the first usable later quote for an originally unpriced forecast under `market_followups/<game_id>.json`, exclusively and separately. It requires the immutable prediction hash; unique saved ESPN ID; exact home/away/start; a retained hashed matching scoreboard; pregame/uncompleted state; and both observation and local recording before the saved start. Cached observations before the prediction was recorded are not accepted as later quotes. The price remains an observed current quote, never a verified closing line. These quote records link to their prediction and source with hashes and cannot replace an existing follow-up or any prediction/result. Their count is reported separately; the current scoring reviews do not use them. Any future scoring of this different quote-selection policy must be explicitly labeled as a separate analysis.

No schedule frequency, model weights, frozen assets, forecast selection window, wagers, or existing score definitions change.
