# Unambiguous NHL original-price JSON

Manual odds capture, archived-capture replay and direct original-price parsing
now use the existing strict source JSON reader. Duplicate keys at every object
depth and the non-standard `NaN`, `Infinity` and `-Infinity` constants reject
before archiving or constructing a quote.

Previously an original response could contain both `"price": 5000` and
`"price": -110` for the same side, with the last value silently selected. The
archive bridge also accepted a duplicate `actual_wagers` manifest key whose last
value was zero. Hashing ambiguous original bytes did not remove that ambiguity.

Four regression tests exercise sixteen adversarial cases across manual capture,
direct source parsing, manifest replay and rehashed original-body replay. All
sixteen were accepted before the repair. Existing valid originals retain their
bytes and hashes; no receipt or forecast is rewritten. The focused three-module
suite passes 46 tests.

This repair makes no API request and enables no polling or paid service. Provider
price observations remain unqualified for sportsbook execution, closing lines
and paper ROI. No forecast, model fitting, first-100 NHL selection, outcome,
promotion or wager changes; `NO_BET=true`, actual wagers zero.
