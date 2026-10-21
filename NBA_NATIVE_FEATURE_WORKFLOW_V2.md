# Native daily reference features in the existing source workflow

The shared NCAA/NBA source workflow explicitly runs the separate native daily
feature protocol only after a newly collected native v2 daily source receipt
passes exact complete NBA/ESPN pregame agreement and original-byte replay.
There is no new schedule. Missing, unsupported, stale or non-pregame sources
cannot cause fallback to an older receipt or bypass original feature guards.

The step runs explicit `--collect`, then exactly audits every retained native
feature file against its own original clock and sources. Only successful
collection plus replay permits staging the new protocol's records directory.
Artifacts retain its collection status, audit, sealed protocol and original
records. The same serialized, current-main checkout and publication path remains
in force. Native record and capture paths do not trigger this source workflow,
so its bot publication cannot loop into repeated collection.

Durable workflow status separately records whether native feature collection
was checked, newly frozen observations, total replayed native records, withheld
targets and the exact current source capture. Counts are null when unchecked,
not an invented zero. Report guards require features-only status, disabled
training/evaluation/forecasting/promotion, NO_BET=true and integer zero wagers.
Old full-season v1 source and feature outcomes remain separate; native success
cannot mark them successful. The old source-only receipt flags are unchanged:
a daily source alone does not authorize feature or model use. This separate
sealed protocol supplies the explicit feature-only step.

Source capture repetition and cross-version feature overlap do not add
independent games. Repeated collection never updates the two first records or
any later frozen file. New records require separate pre-start publication
evidence; merely being emitted by a workflow does not certify public visibility,
source truth or actual tipoff. This pipeline enrolls no predictions or results
and calculates no accuracy. NO_BET=true; wagers zero; model promotion disabled.
