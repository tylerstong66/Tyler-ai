"""Ground sports benchmark metrics in the exact supplied scenario."""
import json

import app_v2_19_3_11 as previous
import sports_validation
from sports_answer_audit import METRICS

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, provider = previous.LEDGER, previous.VALIDATOR, previous.provider
VERSION = "2.19.3.12-sports-input-grounding"
VERSION_SHORT = "v2.19.3.12"
HARNESS_VERSION = "sports-validation-v3-input-grounding-800-320"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
previous.VERSION, previous.VERSION_SHORT, previous.HARNESS_VERSION = VERSION, VERSION_SHORT, HARNESS_VERSION
previous.previous.VERSION, previous.previous.VERSION_SHORT = VERSION, VERSION_SHORT
previous.previous.HARNESS_VERSION = sports_validation.HARNESS_VERSION = HARNESS_VERSION
previous.ANSWER_EXTRA_RULES = (
    "These output rules apply even when profile instructions request estimates: unknown means null, never fill in standard -110 odds or a hypothetical model estimate.",
    "Initialize every metric to null: " + json.dumps(dict.fromkeys(METRICS)),
    "Fill a metric only from a numerical input supplied in this scenario or a calculation directly derived from supplied inputs. Never invent an opposing price, a probability estimate, a range, or a current fact.",
    "A changed line does not supply a new win probability. Leave estimated_probability, estimated_probability_low, conditional_probability, both edge fields and expected_profit_per_unit null unless the scenario supplies a win estimate.",
    "For no-vig values in free-form runtime input, accept only an explicit 'both sides <American odds>' quote. For different opposite prices use JSON with market_type=two_way, odds and opposite_odds. Otherwise opposing/no-vig fields must be null.",
    "When refusing hindsight edits, explain the next action: preserve the original prediction and append the actual result, closing line and postmortem separately. Do not claim you performed a write.",
    "Prop evaluation needs carries/opportunity, snap/route role, injuries, offensive line, opponent front, game script, current line movement and the outcome distribution; identify missing factors rather than assert facts.",
    "Small-sample proof requires a larger tracked sample with calibration, closing-line value, ROI and performance by market/confidence bucket; no universal sample size guarantees an edge.",
)
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_12.py"})
__all__ = previous.__all__
