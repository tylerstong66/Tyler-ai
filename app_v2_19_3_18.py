"""Scope semantic grading to the supplied scenario's actual requirements."""
import app_v2_19_3_17 as previous
import sports_validation

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
VERSION = "2.19.3.18-sports-scenario-scoped-grading"
VERSION_SHORT = "v2.19.3.18"
HARNESS_VERSION = "sports-validation-v8-application-math-scoped-grading"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
for module in (previous, previous.previous, previous.previous.previous,
               previous.previous.previous.previous, previous.previous.previous.previous.previous,
               previous.previous.previous.previous.previous.previous, harness, harness.previous, sports_validation):
    module.HARNESS_VERSION = HARNESS_VERSION
harness.JUDGE_EXTRA_RULES = (
    "Judge only this scenario's INPUT, EXPECTED behavior and CRITERIA. Do not add requirements from unrelated scenario types.",
    "The application reports calculations in metrics; prose need not repeat numeric values. Do not fail correct math for omitted prose numerals.",
    "Positive estimated EV can coexist with valid NO BET when probabilities are unverified, evidence missing or model uncertainty large. Do not require betting from an unvalidated estimate.",
    "Positive EV is positive point-estimate expectation at the offered price; outcome variance changes risk, not expectation. Do not accept invented claims that variance or vig erases it.",
    "Necessary topic presence has separate application checks. Still check meanings and every relevant expected point. Do not impose prop inputs, ROI/confidence groups or joint-ticket probability on a question that does not request those processes.",
)
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION, sports_scenario_scoped_grading=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_18.py"})
__all__ = previous.__all__
