"""Permit supplied identifiers and preserve complete numeric-prose failures."""
import json
import re
import types

import app_v2_19_3_18 as previous
import sports_validation
from sports_answer_audit import audit_answer

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
math_module = previous.previous.previous.previous
coverage_module = previous.previous.previous
VERSION = "2.19.3.19-sports-explanation-diagnostics"
VERSION_SHORT = "v2.19.3.19"
HARNESS_VERSION = "sports-validation-v9-supplied-identifiers-failed-prose-records"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
module = previous
while True:
    module.HARNESS_VERSION = HARNESS_VERSION
    if module is harness.previous:
        break
    module = module.previous
sports_validation.HARNESS_VERSION = HARNESS_VERSION
IDENTIFIER = re.compile(r"\b(?=\w*[A-Za-z])(?=\w*\d)\w+\b")


def unsupported_numeric_prose(prose, request_text):
    supplied = {match[0].casefold() for match in IDENTIFIER.finditer(str(request_text))}
    remaining = IDENTIFIER.sub(lambda match: "" if match[0].casefold() in supplied else match[0], prose)
    return bool(re.search(r"\d", remaining))


math_module.NUMERIC_PROSE_CHECK = unsupported_numeric_prose
math_module.SAVE_EXPLANATION_CONTRACT_FAILURES = True
_OLD_JUDGE = coverage_module._judge


def _judge(self, profile, case, output):
    if not harness.previous._sports(profile):
        return _OLD_JUDGE(self, profile, case, output)
    try:
        answer = json.loads(output)
    except (ValueError, TypeError):
        return _OLD_JUDGE(self, profile, case, output)
    if not isinstance(answer, dict):
        return _OLD_JUDGE(self, profile, case, output)
    errors = list(answer.get("explanation_contract_errors") or [])
    for key in ("rationale", "uncertainty"):
        value = answer.get(key)
        if isinstance(value, str) and unsupported_numeric_prose(value, case["input"]):
            errors.append("unsupported_numeric_prose_in_" + key)
    if not errors:
        return _OLD_JUDGE(self, profile, case, output)
    _, audit_errors = audit_answer(output, case)
    errors = sorted(set(errors + audit_errors))
    return {"case_id": case["case_id"], "input": case["input"], "output": output,
            "expected_behavior": case["expected_behavior"], "score": 0, "passed": False,
            "weaknesses": errors, "strengths": [], "improvement": "; ".join(errors),
            "evaluation_output": None, "objective_audit_passed": not audit_errors,
            "objective_explanation_contract_passed": False,
            "explanation_contract_errors": errors}


SKILL_LAB._judge = types.MethodType(_judge, SKILL_LAB)
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION,
                sports_supplied_identifier_prose_allowed=True,
                sports_failed_numeric_prose_diagnostics_saved=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_19.py"})
__all__ = previous.__all__
