"""Distinguish evidence uncertainty from outcome variance; scope explanations."""
import app_v2_19_3_23 as previous
import sports_validation

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
math_module = previous.previous.math_module
coverage_module = previous.previous.coverage_module
VERSION = "2.19.3.24-sports-evidence-uncertainty"
VERSION_SHORT = "v2.19.3.24"
HARNESS_VERSION = "sports-validation-v14-evidence-uncertainty"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
module = previous
while True:
    module.HARNESS_VERSION = HARNESS_VERSION
    if module is harness.previous:
        break
    module = module.previous
sports_validation.HARNESS_VERSION = HARNESS_VERSION
math_module.EXPLANATION_FINAL_RULES = (
    "Apply the full skill profile as policy, not as an answer checklist. Explain only the user's actual task and its required checks; omit unrelated prop, ledger or sample-performance material. Address missing evidence relevant to that task directly.",
    "Distinguish uncertainty about our estimate from randomness in outcomes. Missing or stale inputs leave the estimate unverified; they do not establish increased or extreme outcome variance. Do not invent a change in variance, event distribution, participation or correlation strength. Outcome variance does not erase expected value.",
    "A changed price changes break-even; a changed threshold changes the event being priced. Reassess the old edge for those reasons, never because randomness erases it. A qualitative dependence mechanism does not establish that another leg is highly likely, or give its conditional probability, without evidence for those thresholds and participants.",
    "Before responding, check each causal statement against the supplied evidence. Use conditional language for hypothetical mechanisms, and say which current inputs or modeling would be needed to evaluate them. Decline unsupported recommendations without replacing the requested explanation with generic policy text.",
)
harness.JUDGE_EXTRA_RULES = (*harness.JUDGE_EXTRA_RULES,
    "Evidence uncertainty is not outcome variance: reject unsupported claims that missing or stale data establishes increased/extreme variance or erases expected value. Quote changes require reassessment of price and event threshold, not invented variance changes.",
    "Qualitative QB/receiver dependence does not establish conditional magnitude or that another threshold is highly likely. A concrete conditional mechanism must still avoid unsupported strength claims; keyword coverage is not semantic proof.",
)
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION,
                sports_evidence_uncertainty_distinguished=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_24.py"})
__all__ = previous.__all__
