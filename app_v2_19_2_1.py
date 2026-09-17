"""Tyler AI v2.19.2.1 — deterministic constrained-mutation index repair.

Hotfix for malformed model-selected mutation indexes. If the model selects an
existing mutation section but gives an out-of-range 1-based line number, Tyler
repairs that number deterministically to the nearest valid line before applying the
single-field mutation. The one-field drift gate, champion protection, benchmark
checks, two-run confirmation, and human promotion gate remain unchanged.
"""

import app_v2_19_2 as v2192

v2192.base.VERSION = "2.19.2.1-constrained-index-repair"
v2192.base.VERSION_SHORT = "v2.19.2.1"

base = v2192.base
app = v2192.app
ENGINE = v2192.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v2192.EXECUTOR
DRILL_EXECUTOR = v2192.DRILL_EXECUTOR
PLANNER = v2192.PLANNER
OPS = v2192.OPS
REVIEW_GATE = v2192.REVIEW_GATE
PROMOTION = v2192.PROMOTION
MERGE_GATE = v2192.MERGE_GATE
SKILL_LAB = v2192.SKILL_LAB
TRAINER = v2192.TRAINER
verify_production = v2192.verify_production
BENCHMARK_OUTPUT_BUDGET = v2192.BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = v2192.BENCHMARK_TRANSPORT
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = v2192.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = v2192.ITERATIVE_CANDIDATE_OUTPUT_TOKENS
MAX_MUTATED_FIELDS = v2192.MAX_MUTATED_FIELDS

_ORIGINAL_SINGLE_MUTATION = v2192._single_mutation


def _repair_target_index(parent, mutation):
    """Return a copy of mutation whose 1-based target index is valid.

    The selected section is preserved. Only the line number may be repaired, and it
    is clamped to the nearest existing line. Empty selected sections still fail
    closed instead of silently switching semantic sections.
    """
    fixed = dict(mutation or {})
    kind = fixed.get("target_kind")
    if kind == "instruction":
        target = list((parent or {}).get("instructions") or [])
    elif kind == "criterion":
        target = list((parent or {}).get("success_criteria") or [])
    else:
        raise RuntimeError("Mutation target kind is invalid.")
    if not target:
        raise RuntimeError("Mutation selected a parent section with no mutable lines.")
    requested = int(fixed.get("target_index") or 0)
    resolved = min(max(requested, 1), len(target))
    fixed["requested_target_index"] = requested
    fixed["target_index"] = resolved
    fixed["index_repaired"] = requested != resolved
    return fixed


def _single_mutation_with_index_repair(parent, mutation):
    fixed = _repair_target_index(parent, mutation)
    instructions, criteria, diff = _ORIGINAL_SINGLE_MUTATION(parent, fixed)
    diff = dict(diff or {})
    diff.update({
        "requested_index": fixed.get("requested_target_index"),
        "resolved_index": fixed.get("target_index"),
        "index_repaired": bool(fixed.get("index_repaired")),
        "index_repair_mode": "clamp_to_nearest_existing_line",
    })
    return instructions, criteria, diff


# app_v2_19_2._constrained_propose_candidate resolves _single_mutation through its
# module globals at call time, so this preserves the tested candidate pipeline while
# repairing malformed line numbers before any candidate is saved or benchmarked.
v2192._single_mutation = _single_mutation_with_index_repair

_PREVIOUS_STATUS = app.view_functions.get("status")


def status_v21921():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["constrained_mutation_index_repair_enabled"] = True
    data["constrained_mutation_index_repair_mode"] = "clamp_to_nearest_existing_line"
    capabilities = data.setdefault("capabilities", [])
    if "deterministic_mutation_index_repair" not in capabilities:
        capabilities.append("deterministic_mutation_index_repair")
    return base.jsonify(data)


app.view_functions["status"] = status_v21921

_ORIGINAL_SAFE_SOURCE_FILES = v2192._safe_source_files_v2192


def _safe_source_files_v21921():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_2_1.py"]))


v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v21921
EXECUTOR.safe_source_files_fn = _safe_source_files_v21921


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "MAX_MUTATED_FIELDS", "_repair_target_index", "_single_mutation_with_index_repair",
]
