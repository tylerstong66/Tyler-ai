"""Require a directional conditional mechanism, not a game-script checklist echo."""
import re

import app_v2_19_3_19 as previous
import sports_validation
from sports_explanation_checks import missing as old_missing, topics

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
math_module, coverage_module = previous.math_module, previous.coverage_module
VERSION = "2.19.3.20-sports-conditional-mechanisms"
VERSION_SHORT = "v2.19.3.20"
HARNESS_VERSION = "sports-validation-v10-directional-game-script-mechanisms"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
module = previous
while True:
    module.HARNESS_VERSION = HARNESS_VERSION
    if module is harness.previous:
        break
    module = module.previous
sports_validation.HARNESS_VERSION = HARNESS_VERSION

CONDITIONAL_DIRECTION = re.compile(
    r"\b(?:if|when|while|with|because)\b.{0,65}\b(?:leading|trailing|lead|behind|ahead|run[- ]heavy|pass[- ]heavy)\b"
    r".{0,140}\b(?:increas|reduc|decreas|rais|lower|more|less|fewer|boost|suppress|grow|fall)\w*\b",
    re.I | re.S,
)


def missing(request_text, answer):
    errors = old_missing(request_text, answer)
    if "game_script_link" in topics(request_text):
        prose = str(answer.get("rationale", "")) + " " + str(answer.get("uncertainty", ""))
        if not CONDITIONAL_DIRECTION.search(prose):
            errors.append("explanation_missing_directional_conditional_mechanism")
    return sorted(set(errors))


def background(request_text, facts):
    if "game_script_link" not in topics(request_text, facts):
        return []
    return [
        "Conditional football mechanics are hypotheses, not observed facts: if an offense protects a lead by running more, passing opportunities can fall for both quarterback and receiver; low opponent scoring can make that script more plausible. If opponent scoring creates a deficit, passing attempts may rise while opponent-under success becomes less likely. These examples do not establish a fixed sign, game-specific strength, or a joint probability.",
        "Answer with an actual conditional mechanism and its directional consequence, not a statement that game script must be discussed or that leading/trailing changes volume.",
    ]


coverage_module.missing = missing
math_module.EXPLANATION_BACKGROUND = background
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT, sports_harness_version=HARNESS_VERSION,
                sports_directional_game_script_check_required=True,
                sports_application_conditional_background=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_20.py"})
__all__ = previous.__all__
