# Native-v2 feature lifecycle across retained final-source dates

Run `python sports_nba_native_v2_retained_finals.py` for a read-only report over
the native-v2 frozen feature cohort. The single-date v3 audit remains unchanged.
This report preserves older source dates instead of making their games appear
unresolved merely because the latest page covers another date.

The builder bounds both source inventories, replays every retained v3 NBA
receipt and ESPN capture, and independently validates the original native-v2
feature protocol, records and source dependencies. Valid captures without NBA
requests are replayed and counted separately. Empty or unsupported NBA pages
supply no final claim and never imply cancellation.

All accepted final claims for a frozen game are compared before any receipt
pair is chosen. Differences in team identity, start, actual start/end, season
stage or scores are quarantined, including earlier contradictions that a later
matching receipt could otherwise hide. The report retains capture identifiers,
manifest digests and normalized-row digests for contradictory claims. Provider
identity quarantines also remain visible.

All retained NBA identity context is checked before choosing a pair. A later
native final or provider event assigning the same matchup within 30 minutes
of the frozen start to another game ID quarantines that feature, including
provider previews with no final score. An earlier clean pair cannot hide the
competing identity.

After consistency is established, selection uses the earliest native final
observation and earliest provider final observed at or after the native reported
end. Selection never searches for a favorable score. The existing daily
classifier still requires the frozen teams and exact original starts; both
sources agreeing on a changed start cannot rewrite or settle the frozen record.
Repeated observations count once per feature identity.

At the October 24 retained snapshot there are 29 frozen feature records:

| Original Eastern date | Records | Source-comparison state |
| --- | ---: | --- |
| October 22 | 2 | Matching retained NBA/ESPN research observations |
| October 23 | 12 | Matching retained NBA/ESPN research observations |
| October 24 | 8 | Awaiting their original scheduled starts |
| October 25 | 7 | Awaiting their original scheduled starts |

That yields 14 distinct matching observations and 15 pending future features,
without pooling the older v1 feature cohort. It does not create 14 graded
predictions or certify that the official schedule/source inventory is complete.

The scheduled workflow publishes a separate artifact and `native_v2_retained_*`
status fields. The `native_v2_features_v3_*` fields retain their single-date
meaning. Offline integration also replays the history report and requires
unchanged tracked evidence.

No collection, prediction or source backfill, outcome enrollment, settlement,
training, grading, promotion or wager occurs. Source origin, receipt clocks,
publication timing and actual tipoff remain independently unattested.
`NO_BET=true`, actual wagers zero, and all model gates remain disabled.
