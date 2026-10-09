"""Allow one auditable explanation revision before grading, with unchanged decision gates."""
import app_v2_19_3_29 as previous
import sports_validation
from sports_answer_audit import _variance_erases_expectation, _double_counts_vig

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
math_module, coverage_module = previous.math_module, previous.coverage_module
VERSION = "2.19.3.30-sports-bounded-revision"
VERSION_SHORT = "v2.19.3.30"
HARNESS_VERSION = "sports-validation-v20-bounded-revision"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
module = previous
while True:
    module.HARNESS_VERSION = HARNESS_VERSION
    if module is harness.previous:
        break
    module = module.previous
sports_validation.HARNESS_VERSION = HARNESS_VERSION

def revision_checks(request_text, facts, answer):
    checked = {**answer, "metrics": facts["metrics"]}
    reasons = coverage_module.missing(request_text, checked)
    prose = answer["rationale"] + " " + answer["uncertainty"]
    if (facts["metrics"].get("expected_profit_per_unit") or 0) > 0:
        if _variance_erases_expectation(prose):
            reasons.append("positive_ev_explanation_confuses_variance_with_expectation")
        if _double_counts_vig(prose):
            reasons.append("positive_ev_explanation_double_counts_vig")
    return sorted(set(reasons))


math_module.EXPLANATION_REVISION_CHECKS = revision_checks

_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION,
                sports_bounded_explanation_revision=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_30.py"})
__all__ = previous.__all__
