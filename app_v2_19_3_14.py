"""Bounded sports completion budgets for Gemini 3 reasoning models."""
import app_v2_19_3_13 as previous
import sports_validation

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider = previous.provider
harness = previous.previous.previous
VERSION = "2.19.3.14-sports-flash-completion-budget"
VERSION_SHORT = "v2.19.3.14"
HARNESS_VERSION = "sports-validation-v4-low-thinking-2400-1200"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
for module in (previous, previous.previous, harness, harness.previous, sports_validation):
    module.HARNESS_VERSION = HARNESS_VERSION
harness.ANSWER_OUTPUT_TOKENS = 2400
harness.JUDGE_OUTPUT_TOKENS = 1200
_OLD_COMPLETE = harness._complete


def _complete(fn):
    token = provider._SPORTS_THINKING_CONTEXT.set("LOW")
    try:
        return _OLD_COMPLETE(fn)
    finally:
        provider._SPORTS_THINKING_CONTEXT.reset(token)


harness._complete = _complete
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_harness_version=HARNESS_VERSION,
                sports_answer_output_tokens=2400, sports_judge_output_tokens=1200,
                sports_thinking_level="LOW", automatic_skill_activation_enabled=False)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_14.py"})
__all__ = previous.__all__
