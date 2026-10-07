"""Require explicit explanation coverage and distinguish math value from confidence."""
import json
import types

import app_v2_19_3_15 as previous
import sports_validation
from sports_answer_audit import audit_answer
from sports_explanation_checks import descriptions, missing

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
VERSION = "2.19.3.16-sports-explanation-coverage"
VERSION_SHORT = "v2.19.3.16"
HARNESS_VERSION = "sports-validation-v6-application-math-explicit-coverage"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
for module in (previous, previous.previous, previous.previous.previous, previous.previous.previous.previous, harness, harness.previous, sports_validation):
    module.HARNESS_VERSION = HARNESS_VERSION
previous.EXPLANATION_REQUIREMENTS = descriptions
harness.JUDGE_EXTRA_RULES = (
    "The app reports calculations in metrics; prose must not repeat numeric values. Do not fail correct math for omitted prose numerals.",
    "Positive estimated EV can coexist with a valid NO BET when probabilities are unverified, evidence missing or uncertainty large. Do not require betting or VALUE CANDIDATE from an unvalidated estimate.",
    "Positive EV means positive point-estimate expectation at the offered price. Variance changes risk, not expectation; no invented claim that it overwhelms or erases EV.",
    "Every expected behavioral point must be explicit. General words like role, market-specific or rigorous validation cannot substitute for omitted carries, snap/route role, ROI, confidence buckets or joint-ticket probability.",
)
_OLD_RUN, _OLD_JUDGE = previous._run, harness._judge


def _run(self, profile, request_text):
    output = _OLD_RUN(self, profile, request_text)
    if harness.previous._sports(profile) and previous._LIVE_INPUT.get():
        omissions = missing(request_text, json.loads(output))
        if omissions:
            raise RuntimeError("Sports explanation failed coverage checks: " + "; ".join(omissions))
    return output


def _judge(self, profile, case, output):
    if not harness.previous._sports(profile):
        return _OLD_JUDGE(self, profile, case, output)
    answer, errors = audit_answer(output, case)
    omissions = missing(case["input"], answer) if not errors else []
    if omissions:
        return {"case_id": case["case_id"], "input": case["input"], "output": output,
                "expected_behavior": case["expected_behavior"], "score": 0, "passed": False,
                "weaknesses": omissions, "strengths": [], "improvement": "; ".join(omissions),
                "evaluation_output": None, "objective_audit_passed": True,
                "objective_explanation_coverage_passed": False, "explanation_coverage_missing": omissions}
    result = _OLD_JUDGE(self, profile, case, output)
    result.update(objective_explanation_coverage_passed=not errors,
                  explanation_coverage_missing=[])
    return result


SKILL_LAB._run = types.MethodType(_run, SKILL_LAB)
SKILL_LAB._judge = types.MethodType(_judge, SKILL_LAB)
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION,
                sports_explanation_coverage_required=True,
                sports_manual_semantic_review_required=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_16.py", "sports_explanation_checks.py"})
__all__ = previous.__all__
