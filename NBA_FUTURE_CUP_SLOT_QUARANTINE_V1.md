# Current NBA schedule: original future Cup slots

The current official 2026–27 NBA schedule responds successfully, but contains
regular-season NBA Cup bracket slots whose opponents are not assigned yet.
The strict legacy parser rejects missing team abbreviations. Its default
behavior and all v1 source receipts remain unchanged.

The current-source collector now uses an explicit v2 receipt and narrow
`FUTURE_NBA_CUP_BOTH_TEAMS_UNASSIGNED_V1` policy. Only future, pending,
regular-season-prefix Cup quarterfinal/semifinal slots with both team IDs equal
to integer zero, null team names/cities/tricodes/slugs and zero placeholder
scores enter quarantine. No side can be known, live, final or past. Unknown
competitions, malformed siblings, duplicate IDs, season mismatches and future
final claims still fail the complete response before archive writes.

Every original source byte is retained, including each quarantined slot. Its
original game digest and explicit ineligibility flags replay from the original
response. Quarantined IDs never enter team reconciliation or result agreement;
editing or removing their exclusion fails verification. Existing unsupported
game types, including preseason and the Cup championship's separate ID prefix,
remain excluded by the original game-kind rules. This is not a complete-season
schedule certification.

The separate v2 receipt reader checks exact source URL, capture timestamp,
source season, full-response hash, known-game count, regenerated quarantine,
linked ESPN manifest and schedule crosswalk. The final-result reader supports
both receipt versions and reports excluded slot IDs without grading them.
The collector uses the existing bounded public NBA transport profile.

The retained October 19 capture contains 1,200 concrete supported games and six
quarantined Cup slots. It corroborates 16 future NBA/ESPN schedule identities,
with zero agreeing final results and 16 pending observations. This is independent
schedule evidence, not a prediction, verified future outcome or enabled model.
Training, forecasts, grading, promotion, deployment and wagers remain disabled.
