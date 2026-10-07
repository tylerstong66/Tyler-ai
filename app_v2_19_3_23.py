"""Scope variance negation and avoid unrelated quote-change prompt contamination."""
import app_v2_19_3_22 as previous
import sports_validation

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
VERSION = "2.19.3.23-sports-negation-input-isolation"
VERSION_SHORT = "v2.19.3.23"
HARNESS_VERSION = "sports-validation-v13-negation-input-isolation"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
module = previous
while True:
    module.HARNESS_VERSION = HARNESS_VERSION
    if module is harness.previous:
        break
    module = module.previous
sports_validation.HARNESS_VERSION = HARNESS_VERSION
harness.JUDGE_EXTRA_RULES = (*harness.JUDGE_EXTRA_RULES,
    "Check each claimed observation against the literal INPUT. A prompt instruction is not a supplied observation. For example, do not accept an observed quote change when the INPUT contains no quote or change. General instructions to check line movement are appropriate; claiming it was observed is not.",
)
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION, sports_input_observation_isolation=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_23.py"})
__all__ = previous.__all__
