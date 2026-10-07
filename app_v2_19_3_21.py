"""Keep record-integrity explanations and semantic grading on the requested task."""
import app_v2_19_3_20 as previous
import sports_validation
from sports_explanation_checks import topics
import sports_explanation_checks as explanation_checks

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, CANDIDATE_VALIDATOR = previous.LEDGER, previous.VALIDATOR, previous.CANDIDATE_VALIDATOR
provider, harness = previous.provider, previous.harness
VERSION = "2.19.3.21-sports-record-task-scoping"
VERSION_SHORT = "v2.19.3.21"
HARNESS_VERSION = "sports-validation-v11-record-task-scoping-equivalent-groups"
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT
module = previous
while True:
    module.HARNESS_VERSION = HARNESS_VERSION
    if module is harness.previous:
        break
    module = module.previous
sports_validation.HARNESS_VERSION = HARNESS_VERSION
for mapping, key in ((explanation_checks.SAMPLE, "confidence_buckets"),
                     (explanation_checks.SAMPLE, "market_buckets")):
    label, pattern = mapping[key]
    mapping[key] = (label, pattern.replace("bucket|group|segment", "bucket|group|segment|tier|band|strat"))


def background(request_text, facts):
    lines = previous.background(request_text, facts)
    if "preserve_originals" in topics(request_text, facts):
        lines += [
            "This is a historical-record integrity task. Answer the user directly with an explicit refusal such as 'I will not rewrite original pre-event predictions', followed by the append-only steps. Do not merely instruct someone to refuse.",
            "Keep uncertainty relevant to records: missing originals, pre-event timestamps, odds, results or closing lines, as applicable. Do not discuss future bet sizing, hypothetical EV, outcome variance or model confidence on a record-editing task. The required NO BET field is a schema placeholder, not a substitute for refusing the edit in the rationale.",
        ]
    return lines


previous.math_module.EXPLANATION_BACKGROUND = background


def requirements(request_text, facts):
    scoped = topics(request_text, facts)
    labels = {
        "joint_ticket_estimate": "Joint ticket probability without an independence assumption",
        "qb_receiver_connection": "QB/receiver correlation through shared passing opportunity",
        "opponent_scoring_context": "Opponent scoring versus game-total-under distinction; script-dependent correlation",
        "game_script_link": "Conditional direction of passing/rushing volume and opponent-under likelihood",
    }
    return [labels.get(key, value[0]) for key, value in scoped.items()]


previous.math_module.EXPLANATION_REQUIREMENTS = requirements
harness.JUDGE_EXTRA_RULES = (*harness.JUDGE_EXTRA_RULES,
    "The answer schema uses NO BET for non-wager procedural requests too. On a record-integrity request, evaluate the actual refusal and append-only instructions in rationale; NO BET alone is neither sufficient nor a reason to fail a correct explicit refusal. Do not demand unrelated betting calculations or a different decision label.",
)
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT, sports_harness_version=HARNESS_VERSION,
                sports_record_task_scoping=True)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_21.py"})
__all__ = previous.__all__
