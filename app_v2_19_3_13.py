"""One-case checkpoints for evaluating a pending sports profile without activation."""
import json

import app_v2_19_3_12 as previous
from sports_validation import SportsValidation

base, app, ENGINE = previous.base, previous.app, previous.ENGINE
SKILL_LAB, TRAINER, EXECUTOR = previous.SKILL_LAB, previous.TRAINER, previous.EXECUTOR
LEDGER, VALIDATOR, provider = previous.LEDGER, previous.VALIDATOR, previous.provider
VERSION = "2.19.3.13-sports-candidate-checkpoints"
VERSION_SHORT = "v2.19.3.13"
HARNESS_VERSION = previous.HARNESS_VERSION  # Answer/judge contract is unchanged.
base.VERSION, base.VERSION_SHORT = VERSION, VERSION_SHORT

CANDIDATE_VALIDATOR = SportsValidation(
    SKILL_LAB, previous.previous.previous._get_rows, previous.previous.previous._save_row,
    provider.TRAINING_PROVIDER, provider.GEMINI_MODEL, base.now_iso,
    candidate_fn=lambda: SKILL_LAB.latest_candidate("Sports Betting Analyst"),
)
_OLD_HANDLE = base.handle_message


def handle_message(message):
    command = str(message or "").strip().lower()
    if command not in {"start sports candidate validation", "continue sports candidate validation", "show sports candidate validation"}:
        return _OLD_HANDLE(message)
    try:
        if command.startswith("start"):
            result = CANDIDATE_VALIDATOR.start()
        elif command.startswith("continue"):
            result = CANDIDATE_VALIDATOR.advance()
        else:
            result = CANDIDATE_VALIDATOR.latest() or {"status": "not_started"}
    except (ValueError, RuntimeError, TypeError) as exc:
        return base.base_payload("sports_candidate_validation", str(exc), success=False,
                                 used_tools=["sports_candidate_validation"]), 409
    return base.base_payload("sports_candidate_validation", json.dumps(result, indent=2, allow_nan=False),
                             success=True, used_tools=["sports_candidate_validation"]) | {"sports": result}, 200


base.handle_message = handle_message
_OLD_STATUS = app.view_functions["status"]


def status():
    data = dict(_OLD_STATUS().get_json() or {})
    data.update(version=VERSION, version_short=VERSION_SHORT,
                sports_candidate_validation_resumable=True, automatic_skill_activation_enabled=False)
    return base.jsonify(data)


app.view_functions["status"] = status
_OLD_SAFE_FILES = EXECUTOR.safe_source_files_fn
EXECUTOR.safe_source_files_fn = lambda: sorted(set(_OLD_SAFE_FILES()) | {"app_v2_19_3_13.py"})
__all__ = previous.__all__ + ["CANDIDATE_VALIDATOR"]
