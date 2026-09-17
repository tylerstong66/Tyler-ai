"""Tyler AI v2.19.2.3.1 — single-line mutation parser repair.

The v2.19.2.3 CI gate correctly caught that a collapsed one-line tagged mutation
could leave an invalid partial first-pass block and skip compact recovery. This
small overlay preserves the resilient transport and deterministic fallback while
repairing that exact parser path. No skill activation, tool permissions, benchmark
budgets, or promotion gates are changed.
"""

import re

import app_v2_19_2_3 as v21923

v21923.base.VERSION = "2.19.2.3.1-single-line-mutation-parser-repair"
v21923.base.VERSION_SHORT = "v2.19.2.3.1"

base = v21923.base
app = v21923.app
ENGINE = v21923.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21923.EXECUTOR
DRILL_EXECUTOR = v21923.DRILL_EXECUTOR
PLANNER = v21923.PLANNER
OPS = v21923.OPS
REVIEW_GATE = v21923.REVIEW_GATE
PROMOTION = v21923.PROMOTION
MERGE_GATE = v21923.MERGE_GATE
SKILL_LAB = v21923.SKILL_LAB
TRAINER = v21923.TRAINER
verify_production = v21923.verify_production
BENCHMARK_OUTPUT_BUDGET = v21923.BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = v21923.BENCHMARK_TRANSPORT
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = v21923.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = v21923.ITERATIVE_CANDIDATE_OUTPUT_TOKENS
MAX_MUTATED_FIELDS = v21923.MAX_MUTATED_FIELDS
MUTATION_ATTEMPT_CATEGORY = v21923.MUTATION_ATTEMPT_CATEGORY
MAX_NOVELTY_OPTIONS = v21923.MAX_NOVELTY_OPTIONS
MUTATION_TRANSPORT = v21923.MUTATION_TRANSPORT
MAX_LOCAL_FALLBACK_OPTIONS = v21923.MAX_LOCAL_FALLBACK_OPTIONS

_ORIGINAL_TAGGED_MUTATION_OPTIONS = v21923._tagged_mutation_options


def _compact_tagged_mutation_options(raw, limit):
    """Parse one or more mutation records even when all tags share one line."""
    compact = str(raw or "").replace("**", "").replace("__", "").replace("`", "")
    compact = re.sub(r"```(?:text|yaml|markdown)?", "", compact, flags=re.I).replace("```", "")
    field_pattern = re.compile(
        r"(TARGET[ _-]?KIND|TARGET[ _-]?INDEX|REPLACEMENT|RATIONALE)\s*(?:=|:|->|—)\s*",
        flags=re.I,
    )
    matches = list(field_pattern.finditer(compact))
    if not matches:
        return []

    blocks = []
    current = {}
    key_map = {
        "TARGETKIND": "TARGET_KIND",
        "TARGETINDEX": "TARGET_INDEX",
        "REPLACEMENT": "REPLACEMENT",
        "RATIONALE": "RATIONALE",
    }
    for idx, match in enumerate(matches):
        raw_key = re.sub(r"[^A-Z]", "", match.group(1).upper())
        key = key_map.get(raw_key)
        if not key:
            continue
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(compact)
        value = compact[match.end():end].strip(" \t\r\n,;|-")
        if key == "TARGET_KIND" and "TARGET_KIND" in current:
            blocks.append(current)
            current = {}
        current[key] = value
    if current:
        blocks.append(current)

    out = []
    for block in blocks:
        try:
            out.append(v21923._coerce_mutation(block))
        except Exception:
            continue
        if len(out) >= max(1, int(limit)):
            break
    return out


def _tagged_mutation_options_v219231(raw, limit):
    """Use normal multiline parsing first, then always try compact recovery if needed."""
    out = _ORIGINAL_TAGGED_MUTATION_OPTIONS(raw, limit)
    if out:
        return out[:max(1, int(limit))]
    return _compact_tagged_mutation_options(raw, limit)


# _parse_mutation_slate_resilient is defined in v2.19.2.3 and resolves this
# module attribute dynamically, so replacing it repairs the existing transport
# without changing candidate generation, novelty tracking, or fallback logic.
v21923._tagged_mutation_options = _tagged_mutation_options_v219231

_ORIGINAL_SAFE_SOURCE_FILES = v21923._safe_source_files_v21923


def _safe_source_files_v219231():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_2_3_1.py"]))


v21923.v21922.v21921.v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v219231
EXECUTOR.safe_source_files_fn = _safe_source_files_v219231


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "MAX_MUTATED_FIELDS", "MUTATION_ATTEMPT_CATEGORY", "MAX_NOVELTY_OPTIONS",
    "MUTATION_TRANSPORT", "MAX_LOCAL_FALLBACK_OPTIONS",
    "_compact_tagged_mutation_options", "_tagged_mutation_options_v219231",
]
