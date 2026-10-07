"""Extend explanation coverage to auditable historical-record handling."""
import app_v2_19_3_16 as previous
import sports_validation

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
VERSION = "2.19.3.17-sports-record-explanation-coverage"
VERSION_SHORT = "v2.19.3.17"
HARNESS_VERSION = "sports-validation-v7-application-math-process-coverage"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
for module in (previous, previous.previous, previous.previous.previous, previous.previous.previous.previous, previous.previous.previous.previous.previous, harness, harness.previous, sports_validation):
    module.HARNESS_VERSION = HARNESS_VERSION
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION,
                sports_record_explanation_coverage_required=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_17.py"})
__all__ = previous.__all__
