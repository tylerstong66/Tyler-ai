"""Ground quote-change explanations and accept equivalent causal language."""
import re

import app_v2_19_3_21 as previous
import sports_validation
from sports_explanation_checks import topics

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
math_module = previous.previous.math_module
coverage_module = previous.previous.coverage_module
VERSION = "2.19.3.22-sports-quote-grounding-causal-language"
VERSION_SHORT = "v2.19.3.22"
HARNESS_VERSION = "sports-validation-v12-quote-grounding-causal-language"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
module = previous
while True:
    module.HARNESS_VERSION = HARNESS_VERSION
    if module is harness.previous:
        break
    module = module.previous
sports_validation.HARNESS_VERSION = HARNESS_VERSION

# Equivalent causal connectors still need a lead/trail branch and a directional
# passing/rushing consequence. Presence is necessary, not semantic proof.
CAUSAL_DIRECTION = re.compile(
    r"\b(?:if|when|while|with|because|since|where)\b(?P<branch>[^.;!?]{0,260})", re.I
)
SCRIPT = re.compile(r"\b(?:leading|trailing|lead|behind|ahead|run[- ]heavy|pass[- ]heavy)\b", re.I)
DIRECTION = re.compile(r"\b(?:increas|reduc|decreas|rais|lower|more|less|fewer|boost|suppress|grow|fall)\w*\b", re.I)
VOLUME = re.compile(r"\b(?:pass(?:ing)?|rush(?:ing)?|running|attempts?|opportunit\w*|volume)\b", re.I)


def causal_direction(prose):
    return any(SCRIPT.search(m["branch"]) and DIRECTION.search(m["branch"]) and
               VOLUME.search(m["branch"]) for m in CAUSAL_DIRECTION.finditer(prose))


def unsupported_consensus(prose):
    """Reject affirmative quote-to-consensus inferences, allowing caveats."""
    for clause in re.split(r"[;.!?]", prose):
        for claim in re.finditer(
                r"\b(?:reflect\w*|indicat\w*|establish\w*|prov\w*|show\w*|confirm\w*)"
                r"[^,;.!?]{0,65}\b(?:market|bookmaker|betting)\s+consensus\b", clause, re.I):
            prefix = clause[:claim.start()]
            if re.search(r"\b(?:does not|doesn't|cannot|can not|do not|never|not|without)\s*$", prefix, re.I):
                continue
            if re.search(r"\b(?:whether|unknown (?:if|whether))(?:\s+(?:it|this|that|the change|the quote))?\s*$", prefix, re.I):
                continue
            return True
    return False


def missing(request_text, answer):
    errors = previous.previous.missing(request_text, answer)
    prose = str(answer.get("rationale", "")) + " " + str(answer.get("uncertainty", ""))
    if "game_script_link" in topics(request_text):
        name = "explanation_missing_directional_conditional_mechanism"
        errors = [x for x in errors if x != name]
        if not causal_direction(prose):
            errors.append(name)
    if (answer.get("metrics") or {}).get("previous_implied_probability") is not None:
        if unsupported_consensus(prose):
            errors.append("explanation_quote_change_does_not_establish_market_consensus")
    return sorted(set(errors))


def background(request_text, facts):
    lines = previous.background(request_text, facts)
    if (facts.get("metrics") or {}).get("previous_implied_probability") is not None:
        lines += [
            "This supplies a bookmaker quote change, not market-wide evidence. Do not infer changed market consensus, sharp action, a verified fair probability or a new estimate from that quote alone.",
            "Explain that changing the price and threshold requires reassessing the probability at the new number and the break-even price. The old edge may disappear even with the same matchup. Withhold a recommendation until current-price value is supported.",
        ]
    return lines


coverage_module.missing = missing
math_module.EXPLANATION_BACKGROUND = background
harness.JUDGE_EXTRA_RULES = (*harness.JUDGE_EXTRA_RULES,
    "A supplied quote change alone is not evidence of market consensus or sharp action. Require reassessment at the new number and price; do not invent the new fair probability. An unrelated uncertainty caveat does not excuse an affirmative unsupported claim.",
    "Causal language such as since or where is acceptable when it supplies an actual lead/trail branch and directional passing/rushing consequence. Still reject checklist echoes and unsupported correlation magnitude or fixed signs.",
    "Variance changes risk, not expectation even when an estimate is unavailable. Do not accept claims that variance overwhelms or erases an edge. Negated warnings such as never implying that variance erases an edge are not affirmative errors.",
)
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT, sports_harness_version=HARNESS_VERSION,
                sports_quote_change_grounding_required=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_22.py"})
__all__ = previous.__all__
