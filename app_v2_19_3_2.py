"""Tyler AI v2.19.3.2 — quota-aware compact champion training.

Keeps the v2.19.3.1 fail-safe training and promotion gates intact while
reducing repeated benchmark prompt/output volume and turning Groq daily-token
429s into a bounded local cooldown with a safe, actionable error. A provider
quota failure still occurs before a round is persisted, so the current session
can resume with the same command after the cooldown/reset.
"""

import os
import re
import time
import types

import app_v2_19_3_1 as v21931
import skill_lab as labmod


v21931.base.VERSION = "2.19.3.2-quota-aware-compact-training"
v21931.base.VERSION_SHORT = "v2.19.3.2"

base = v21931.base
app = v21931.app
ENGINE = v21931.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21931.EXECUTOR
DRILL_EXECUTOR = v21931.DRILL_EXECUTOR
PLANNER = v21931.PLANNER
OPS = v21931.OPS
REVIEW_GATE = v21931.REVIEW_GATE
PROMOTION = v21931.PROMOTION
MERGE_GATE = v21931.MERGE_GATE
SKILL_LAB = v21931.SKILL_LAB
TRAINER = v21931.TRAINER
verify_production = v21931.verify_production
BENCHMARK_TRANSPORT = v21931.BENCHMARK_TRANSPORT
MAX_MUTATED_FIELDS = v21931.MAX_MUTATED_FIELDS
MUTATION_ATTEMPT_CATEGORY = v21931.MUTATION_ATTEMPT_CATEGORY
MAX_NOVELTY_OPTIONS = v21931.MAX_NOVELTY_OPTIONS
MUTATION_TRANSPORT = v21931.MUTATION_TRANSPORT
MAX_LOCAL_FALLBACK_OPTIONS = v21931.MAX_LOCAL_FALLBACK_OPTIONS
MUTATION_OUTCOME_CATEGORY = v21931.MUTATION_OUTCOME_CATEGORY
OUTCOME_LEARNING_MODE = v21931.OUTCOME_LEARNING_MODE


def _bounded_env_int(name, default, low, high):
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(low, min(high, value))


# The prior round reserved 950 output tokens (800 benchmark + 150 mutation).
# Compact tagged responses are already enforced, so 650 + 120 preserves useful
# answer/judge space while cutting the maximum reservation by about 19%.
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = _bounded_env_int(
    "TRAINING_BENCHMARK_OUTPUT_BUDGET", 650, 450, 800
)
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = _bounded_env_int(
    "TRAINING_CANDIDATE_OUTPUT_TOKENS", 120, 100, 150
)
BENCHMARK_OUTPUT_BUDGET = ITERATIVE_BENCHMARK_OUTPUT_BUDGET


def _set_module_constant_chain(root, name, value):
    """Update the layered module globals used by already-defined functions."""
    seen = set()
    pending = [root]
    while pending:
        module = pending.pop()
        identity = id(module)
        if identity in seen:
            continue
        seen.add(identity)
        if hasattr(module, name):
            setattr(module, name, value)
        for attr_name, child in vars(module).items():
            if attr_name.startswith("v2") and isinstance(child, types.ModuleType):
                pending.append(child)


_set_module_constant_chain(
    v21931, "BENCHMARK_OUTPUT_BUDGET", ITERATIVE_BENCHMARK_OUTPUT_BUDGET
)
_set_module_constant_chain(
    v21931,
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET",
    ITERATIVE_BENCHMARK_OUTPUT_BUDGET,
)
_set_module_constant_chain(
    v21931,
    "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    ITERATIVE_CANDIDATE_OUTPUT_TOKENS,
)


def _clip(value, limit):
    value = labmod._norm(value)
    if len(value) <= limit:
        return value
    shortened = value[:limit].rsplit(" ", 1)[0].rstrip(" ,;:")
    return (shortened or value[:limit]).rstrip() + "…"


def _compact_benchmark_context(self, profile):
    """Build a complete but bounded profile reused across every benchmark case."""
    lines = [
        f"ACTIVE SKILL: {_clip(profile.get('name'), 120)}",
        f"PURPOSE: {_clip(profile.get('purpose'), 600)}",
        f"PROFILE VERSION: {int(profile.get('version') or 1)}",
    ]
    tools = labmod._as_list(profile.get("allowed_tools"))
    if tools:
        lines.append("ALLOWED TOOLS: " + ", ".join(_clip(x, 80) for x in tools[:20]))

    instructions = labmod._as_list(profile.get("instructions"))
    if instructions:
        lines.append("INSTRUCTIONS:")
        lines.extend("- " + _clip(item, 260) for item in instructions[:10])

    criteria = labmod._as_list(profile.get("success_criteria"))
    if criteria:
        lines.append("SUCCESS CRITERIA:")
        lines.extend("- " + _clip(item, 220) for item in criteria[:10])

    # A single compact example retains learned style without repeating as many
    # as eight full examples in each of the five benchmark answer calls.
    examples = self.engine.examples_for_skill(profile["skill_id"], 1)
    if examples:
        item = examples[0]
        lines.extend([
            "TRAINING EXAMPLE:",
            "Input: " + _clip(item.get("input"), 180),
            "Ideal output: " + _clip(item.get("ideal_output"), 360),
        ])
    return "\n".join(lines)[:4200]


SKILL_LAB._context = types.MethodType(_compact_benchmark_context, SKILL_LAB)


_ORIGINAL_SKILL_COMPLETE = ENGINE.complete
_QUOTA_BLOCKED_UNTIL = 0.0
_QUOTA_WAIT_SECONDS = 0


def _is_daily_token_limit(error):
    text = str(error or "").lower()
    return (
        "rate limit reached" in text
        and ("tokens per day" in text or "tpd" in text)
    )


def _retry_seconds(error, default=300):
    text = str(error or "")
    match = re.search(
        r"try again in\s*(?:(\d+)m)?\s*(\d+(?:\.\d+)?)s",
        text,
        flags=re.I,
    )
    if not match:
        return int(default)
    minutes = int(match.group(1) or 0)
    seconds = float(match.group(2) or 0)
    return max(1, int(minutes * 60 + seconds + 1))


def _quota_message(wait_seconds):
    minutes = max(1, (int(wait_seconds) + 59) // 60)
    return (
        "Groq's daily token quota is temporarily exhausted. No training round "
        "was consumed and the current session is preserved. Wait about "
        f"{minutes} minute(s), then retry the same continue-training command."
    )


def _quota_aware_complete(messages, tokens=700, temperature=0.2, json_mode=False):
    global _QUOTA_BLOCKED_UNTIL, _QUOTA_WAIT_SECONDS
    remaining = int(max(0, _QUOTA_BLOCKED_UNTIL - time.monotonic()))
    if remaining > 0:
        raise RuntimeError(_quota_message(remaining))
    try:
        return _ORIGINAL_SKILL_COMPLETE(
            messages,
            tokens=tokens,
            temperature=temperature,
            json_mode=json_mode,
        )
    except RuntimeError as exc:
        if not _is_daily_token_limit(exc):
            raise
        wait_seconds = _retry_seconds(exc)
        _QUOTA_WAIT_SECONDS = wait_seconds
        _QUOTA_BLOCKED_UNTIL = time.monotonic() + wait_seconds
        raise RuntimeError(_quota_message(wait_seconds)) from None


ENGINE.complete = _quota_aware_complete


_PREVIOUS_STATUS = app.view_functions.get("status")


def status_v21932():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["quota_aware_training_enabled"] = True
    data["compact_training_context_enabled"] = True
    data["training_benchmark_output_budget"] = ITERATIVE_BENCHMARK_OUTPUT_BUDGET
    data["training_candidate_output_budget"] = ITERATIVE_CANDIDATE_OUTPUT_TOKENS
    data["training_round_output_budget"] = (
        ITERATIVE_BENCHMARK_OUTPUT_BUDGET + ITERATIVE_CANDIDATE_OUTPUT_TOKENS
    )
    data["automatic_skill_activation_enabled"] = False
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "quota_aware_training",
        "compact_benchmark_context",
        "provider_cooldown_guard",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v21932

_ORIGINAL_SAFE_SOURCE_FILES = v21931._safe_source_files_v21931


def _safe_source_files_v21932():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_3_2.py"]))


v21931.v2193.v219231.v21923.v21922.v21921.v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v21932
EXECUTOR.safe_source_files_fn = _safe_source_files_v21932


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "MAX_MUTATED_FIELDS", "MUTATION_ATTEMPT_CATEGORY", "MAX_NOVELTY_OPTIONS",
    "MUTATION_TRANSPORT", "MAX_LOCAL_FALLBACK_OPTIONS",
    "MUTATION_OUTCOME_CATEGORY", "OUTCOME_LEARNING_MODE",
    "_compact_benchmark_context", "_quota_aware_complete",
]
