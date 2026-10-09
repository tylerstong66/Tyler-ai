"""Do not turn missing evidence into measured uncertainty or require independence."""
import re

import app_v2_19_3_25 as previous
import sports_validation
from sports_explanation_checks import topics

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
math_module, coverage_module = previous.math_module, previous.coverage_module
VERSION = "2.19.3.26-sports-uncertainty-scope"
VERSION_SHORT = "v2.19.3.26"
HARNESS_VERSION = "sports-validation-v16-uncertainty-scope"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
module = previous
while True:
    module.HARNESS_VERSION = HARNESS_VERSION
    if module is harness.previous:
        break
    module = module.previous
sports_validation.HARNESS_VERSION = HARNESS_VERSION


def task_rules(request_text, facts):
    required = topics(request_text, facts)
    rules = [
        "Missing evidence leaves the size of model error and outcome variance UNKNOWN. Do not say either is high, low, extreme or large relative to an edge merely because evidence is missing or unverified. Explain what is unknown and which data would resolve it. Hypothetical mechanisms are allowed; unmeasured magnitudes are not observed facts.",
        *[r for r in previous.task_rules(request_text, facts) if not r.startswith("For this positive point-estimate EV")],
    ]
    if "joint_ticket_estimate" in required:
        rules.append(
            "A joint distribution can model dependent legs; independence is NOT necessary to evaluate joint probability. The limitation here is missing joint-probability evidence. Do not say 'cannot evaluate joint probability without an independence assumption'. Reject unsupported multiplication of marginal probabilities and require a defensible joint estimate."
        )
    if "positive_ev_meaning" in required:
        gap = facts["metrics"]["edge_percentage_points"]
        rules.append(
            f"The current supplied conditional probability gap above offered-price break-even is {gap:.6g} percentage points, already displayed in metrics. This arithmetic margin is not a measurement of model error. State the positive point-estimate expected profit, then explain that a downward estimation error crossing break-even would reverse its sign. Without supplied error bounds the size and likelihood of that error are unknown. Do not call every positive gap narrow or assert that model error is large relative to it. A larger supplied gap also needs evidence before being called robust. Use qualitative prose without numerals; price-adjusted EV already includes juice and outcome variance affects risk, not expectation."
        )
        if re.search(r"\bstrong\b|\bconfident\b", str(request_text), re.I):
            rules.append(
                "Address the requested strength explicitly: assess the actual supplied gap, rather than positive EV alone. If the estimate only marginally clears break-even, even a small downward probability error could reverse expected profit. That conditional sensitivity is a reason not to call a marginal unverified estimate a strong bet; it is not evidence that an error of that size has occurred."
            )
    return rules


_OLD_MISSING = coverage_module.missing
INDEPENDENCE_REQUIRED = re.compile(
    r"\b(?:cannot|can't|impossible to)\s+(?:evaluate|estimate|calculate|compute|price)"
    r"[^.;!?]{0,85}\b(?:joint|ticket|parlay)\b[^.;!?]{0,65}\bwithout (?:an? )?independence assumption\b", re.I
)
UNMEASURED_MAGNITUDE = re.compile(
    r"\b(?:outcome )?(?:variance|volatility)(?: and model uncertainty)?\s+(?:(?:is|are|remains?)\s+)?(?:too\s+)?(?:high|extreme|elevated|large)\b"
    r"|\b(?:probability[- ]model|model|estimation|probability) error\s+(?:is|remains?)\s+(?:too\s+)?(?:large|high|small|negligible)\b", re.I
)


def missing(request_text, answer):
    errors = _OLD_MISSING(request_text, answer)
    prose = str(answer.get("rationale", "")) + " " + str(answer.get("uncertainty", ""))
    for clause in re.split(r"[;.!?]", prose):
        for match in INDEPENDENCE_REQUIRED.finditer(clause):
            prefix = clause[:match.start()]
            if re.search(r"\b(?:do not say|never say|wrong to say|not true that|incorrect that)\s+(?:(?:we|i|tyler)\s+)?$", prefix, re.I):
                continue
            errors.append("explanation_independence_not_required_for_joint_probability")
        # This guard catches a specific causal error, not every qualitative risk
        # statement. Necessary lexical checks still require semantic review.
        if not re.search(r"\b(?:unverified|missing|absent|unknown|stale)\b", clause, re.I):
            continue
        for match in UNMEASURED_MAGNITUDE.finditer(clause):
            prefix = clause[:match.start()]
            if re.search(r"\b(?:not evidence that|does not establish|cannot conclude|do not claim|never claim|not a claim that)\s*$", prefix, re.I):
                continue
            if re.search(r"^\s*(?:if|when)\b", clause, re.I):
                continue
            errors.append("explanation_missing_evidence_does_not_measure_uncertainty_magnitude")
    return sorted(set(errors))


math_module.EXPLANATION_TASK_RULES = task_rules
coverage_module.missing = missing
harness.JUDGE_EXTRA_RULES = (*harness.JUDGE_EXTRA_RULES,
    "Missing/stale/unverified evidence does not measure variance or probability-model error. Fail FACTS for an unsupported high/extreme variance level or a claim model error is large relative to the edge. Conditional sensitivity to an error is valid; it does not prove that error exists. A supplied probability gap need not be narrow merely because inputs are unverified.",
    "Independence is not required for joint probability: a joint distribution can model dependent legs. Reject statements that joint probabilities cannot be evaluated without assuming independence; require joint evidence instead.",
)
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION,
                sports_uncertainty_magnitude_grounding=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_26.py"})
__all__ = previous.__all__
