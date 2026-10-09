"""Require task-specific mechanisms after the shared sports policy context."""
import app_v2_19_3_24 as previous
import sports_validation
from sports_explanation_checks import topics

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
math_module, coverage_module = previous.math_module, previous.coverage_module
VERSION = "2.19.3.25-sports-task-mechanisms"
VERSION_SHORT = "v2.19.3.25"
HARNESS_VERSION = "sports-validation-v15-task-mechanisms"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
module = previous
while True:
    module.HARNESS_VERSION = HARNESS_VERSION
    if module is harness.previous:
        break
    module = module.previous
sports_validation.HARNESS_VERSION = HARNESS_VERSION


def task_rules(request_text, facts):
    """Use request intent and application metrics, never case IDs or expected text."""
    required = topics(request_text, facts)
    rules = []
    if "game_script_link" in required:
        rules.append(
            "For this connected football ticket, explain shared quarterback/receiver opportunity and give at least one actual hypothetical if/when branch: an offense protecting a lead may run more, lowering passing opportunities for both; low opponent scoring may support that script. Conversely, a deficit may raise passing attempts while making opponent-under success less plausible. Choose a relevant mechanism and explain its consequence for the requested legs; do not just name game script or say the mechanism is unknown. Opponent-under is not game-total-under. These hypotheses supply neither a fixed correlation sign nor magnitude, a participant fact, or joint ticket probability. Reject independent multiplication when dependence is material, and require a joint model before claiming value."
        )
    if "positive_ev_meaning" in required:
        rules.append(
            "For this positive point-estimate EV calculation, connect the supplied probability-to-break-even gap to the strength of the requested recommendation. A gap that barely clears break-even is fragile: a small overestimate could put the true probability below break-even and reverse expected profit. Explain probability-model error relative to this gap, rather than only saying inputs are unverified. A larger supplied gap also needs evidence and uncertainty bounds before being called robust; do not invent an error size, range or guarantee. The calculated gap is already shown in metrics, so use qualitative prose without numerals. Outcome variance affects risk, and offered-price EV already includes juice; neither is an extra subtraction from positive EV."
        )
    return rules


math_module.EXPLANATION_TASK_RULES = task_rules
harness.JUDGE_EXTRA_RULES = (*harness.JUDGE_EXTRA_RULES,
    "When the request asks for a strong recommendation from a marginal positive probability gap, correct metrics and generic unverified-input language are insufficient. Require an explanation of the small gap's sensitivity to probability-model error. Numbers are already in metrics; do not require repeating them in prose or subtracting vig twice.",
)
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION,
                sports_task_mechanisms_required=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_25.py"})
__all__ = previous.__all__
