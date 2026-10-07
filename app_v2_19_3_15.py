"""Sports answers combine application-owned math with checked model explanations."""
import json
import re
import types
from contextvars import ContextVar

import app_v2_19_3_14 as previous
import sports_validation
from sports_answer_audit import audit_answer, render_answer
from sports_input_metrics import calculate

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
VERSION = "2.19.3.15-sports-application-math"
VERSION_SHORT = "v2.19.3.15"
HARNESS_VERSION = "sports-validation-v5-application-math-low-2400-1200"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
for module in (previous, previous.previous, previous.previous.previous, harness, harness.previous, sports_validation):
    module.HARNESS_VERSION = HARNESS_VERSION
_LIVE_INPUT = ContextVar("sports_live_input", default=False)
_OLD_RUN = SKILL_LAB._run
EXPLANATION_REQUIREMENTS = lambda request_text, facts: []


def _run(self, profile, request_text):
    if not harness.previous._sports(profile):
        return _OLD_RUN(profile, request_text)
    facts = calculate(request_text, synthetic=not _LIVE_INPUT.get())
    metrics = facts["metrics"]
    # Price changes require a new analysis. Live free text never certifies a bet.
    if metrics["previous_implied_probability"] is not None:
        allowed = ["RE-EVALUATE"]
    elif _LIVE_INPUT.get() or metrics["expected_profit_per_unit"] is None or metrics["expected_profit_per_unit"] <= 0 or (metrics["lower_bound_edge_percentage_points"] is not None and metrics["lower_bound_edge_percentage_points"] <= 0):
        allowed = ["NO BET"]
    else:
        allowed = ["NO BET", "VALUE CANDIDATE"]
    prompt = "\n".join([
        "Explain this sports scenario with valid JSON only: decision, rationale, uncertainty. No other keys.",
        "Allowed decision(s): " + ", ".join(allowed),
        "The application computes and displays all metrics. Do not supply metrics or any numerals in your prose.",
        "Explain the supplied calculation's meaning without repeating numeric values. Never invent facts or estimates.",
        "rationale and uncertainty together must be <=130 words. Answer every requested behavioral point.",
        "Fulfill the checks with complete, scenario-specific explanations. Do not copy checklist directives such as Explain or Discuss as your answer.",
        "Refer to the supplied bookmaker price/line only. A single quote change does not establish broad market consensus or independent verification.",
        "Offered-price break-even already includes juice. Positive EV cannot be erased by subtracting vig again.",
        "Unverified probabilities and missing evidence can justify NO BET despite positive point-estimate EV.",
        "Outcome variance affects risk, not expected value. Missing model confidence is a reason to withhold a bet; never assert that variance erases an edge.",
        "Application-calculated context: " + json.dumps(facts),
        "Required explanation checks (address EACH explicitly, using brief semicolon-separated clauses): "
        + " | ".join(EXPLANATION_REQUIREMENTS(request_text, facts)),
        self._context(profile),
        *harness.ANSWER_EXTRA_RULES[-3:],
        "The three-key explanation contract above overrides any request for model-generated metrics.",
    ])
    raw = harness._complete(lambda: self.engine.complete([
        {"role": "system", "content": prompt}, {"role": "user", "content": str(request_text)},
    ], tokens=harness.ANSWER_OUTPUT_TOKENS, temperature=.1, json_mode=True))
    try:
        answer = json.loads(raw)
    except (TypeError, ValueError):
        raise RuntimeError("Sports explanation JSON invalid.") from None
    if not isinstance(answer, dict) or set(answer) != {"decision", "rationale", "uncertainty"}:
        raise RuntimeError("Sports explanation must follow the three-key contract.")
    if answer["decision"] not in allowed:
        raise RuntimeError("Sports explanation violated the application decision gate.")
    for key in ("rationale", "uncertainty"):
        if not isinstance(answer[key], str) or not answer[key].strip() or re.search(r"\d", answer[key]):
            raise RuntimeError("Sports explanation must be nonempty prose without numerals.")
    if len((answer["rationale"] + " " + answer["uncertainty"]).split()) > 130:
        raise RuntimeError("Sports explanation exceeded its word budget.")
    answer["metrics"] = metrics
    answer["calculation_provenance"] = facts["provenance"]
    answer["calculation_assumptions"] = facts["assumptions"]
    answer["input_issues"] = facts["issues"]
    answer["uncertainty"] += " " + " ".join([facts["provenance"], *facts["assumptions"], *facts["issues"]])
    return json.dumps(answer)


SKILL_LAB._run = types.MethodType(_run, SKILL_LAB)
_OLD_ENGINE_RUN = ENGINE.run_skill


def _engine_run(self, skill_name, request_text):
    if harness.previous._slug(skill_name) != harness.previous.SPORTS_ID:
        return _OLD_ENGINE_RUN(skill_name, request_text)
    profile = self.get_skill(skill_name)
    if not profile:
        raise ValueError("Sports Betting Analyst not found.")
    token = _LIVE_INPUT.set(True)
    try:
        output = SKILL_LAB._run(profile, request_text)
    finally:
        _LIVE_INPUT.reset(token)
    answer, errors = audit_answer(output, input_text=str(request_text))
    if errors:
        raise RuntimeError("Sports answer failed checks: " + "; ".join(errors))
    return render_answer(answer)


ENGINE.run_skill = types.MethodType(_engine_run, ENGINE)
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION, sports_application_owned_math=True,
                sports_live_push_assumption_enabled=False, automatic_skill_activation_enabled=False)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_15.py", "sports_input_metrics.py"})
__all__ = previous.__all__
