"""Tyler AI v2.19.3.1 — fail-safe mutation outcome persistence.

Fixes a production worker timeout observed after a completed champion-training round.
v2.19.3 performed optional mutation-outcome bookkeeping after the candidate,
benchmark run, training round, and session had already been durably saved. A slow
Supabase TLS connection during that redundant bookkeeping could let Gunicorn kill
the worker and turn a completed round into an empty HTTP 500.

v2.19.3.1 makes the already-persisted candidate + benchmark + round/session records
the durable source of truth for mutation learning. The response path performs zero
database reads/writes after the core training result is complete. A deterministic,
idempotent outcome view is computed locally and cached in-process. Cross-session
history is reconstructed in bounded bulk reads before candidate generation instead
of N+1 reads after benchmarking.
"""

from datetime import datetime, timezone
import time
import types

import app_v2_19_3 as v2193
import skill_lab as labmod

v2193.base.VERSION = "2.19.3.1-fail-safe-outcome-persistence"
v2193.base.VERSION_SHORT = "v2.19.3.1"

base = v2193.base
app = v2193.app
ENGINE = v2193.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v2193.EXECUTOR
DRILL_EXECUTOR = v2193.DRILL_EXECUTOR
PLANNER = v2193.PLANNER
OPS = v2193.OPS
REVIEW_GATE = v2193.REVIEW_GATE
PROMOTION = v2193.PROMOTION
MERGE_GATE = v2193.MERGE_GATE
SKILL_LAB = v2193.SKILL_LAB
TRAINER = v2193.TRAINER
verify_production = v2193.verify_production
BENCHMARK_OUTPUT_BUDGET = v2193.BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = v2193.BENCHMARK_TRANSPORT
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = v2193.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = v2193.ITERATIVE_CANDIDATE_OUTPUT_TOKENS
MAX_MUTATED_FIELDS = v2193.MAX_MUTATED_FIELDS
MUTATION_ATTEMPT_CATEGORY = v2193.MUTATION_ATTEMPT_CATEGORY
MAX_NOVELTY_OPTIONS = v2193.MAX_NOVELTY_OPTIONS
MUTATION_TRANSPORT = v2193.MUTATION_TRANSPORT
MAX_LOCAL_FALLBACK_OPTIONS = v2193.MAX_LOCAL_FALLBACK_OPTIONS
MUTATION_OUTCOME_CATEGORY = v2193.MUTATION_OUTCOME_CATEGORY
OUTCOME_LEARNING_MODE = v2193.OUTCOME_LEARNING_MODE
HARMFUL_SEMANTIC_BLOCK_THRESHOLD = v2193.HARMFUL_SEMANTIC_BLOCK_THRESHOLD
CATASTROPHIC_SCORE_DELTA = v2193.CATASTROPHIC_SCORE_DELTA
CATASTROPHIC_PASS_RATE_DELTA = v2193.CATASTROPHIC_PASS_RATE_DELTA

# Outcome-history reads happen before candidate generation and are optional. They
# are deliberately far below Gunicorn's 30-second worker timeout.
OUTCOME_DB_CONNECT_TIMEOUT_SECONDS = 0.8
OUTCOME_DB_READ_TIMEOUT_SECONDS = 1.5
OUTCOME_HISTORY_CACHE_SECONDS = 180.0
OUTCOME_HISTORY_CANDIDATE_LIMIT = 700
OUTCOME_HISTORY_RUN_LIMIT = 1000

_HISTORY_CACHE = {}
_LOCAL_OUTCOMES = {}


def _cache_key(skill_id, base_version):
    return (labmod._slug(skill_id), int(base_version or 1))


def _dedupe_outcomes(items):
    seen = set()
    out = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        key = (
            str(item.get("candidate_id") or ""),
            str(item.get("evaluation_id") or ""),
            str(item.get("phase") or ""),
        )
        if key == ("", "", ""):
            key = ("outcome", str(item.get("outcome_id") or ""), "")
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(item))
    return out


def _bounded_records(lab, category, limit):
    """Best-effort bounded record read used only for learning context.

    Production uses a short direct Supabase request. Unit/in-memory environments
    fall back to the lab store. Failure returns [] so learning history can degrade
    gracefully without blocking safe candidate generation.
    """
    url = str(getattr(base, "SUPABASE_URL", "") or "").rstrip("/")
    if not url:
        try:
            return lab._records(category, limit)
        except Exception:
            return []

    params = {
        "select": "id,created_at,memories,category,importance",
        "order": "created_at.desc",
        "limit": int(limit),
        "category": f"eq.{category}",
    }
    try:
        response = base.requests.get(
            f"{url}/rest/v1/memories",
            headers=base.supabase_headers(),
            params=params,
            timeout=(OUTCOME_DB_CONNECT_TIMEOUT_SECONDS, OUTCOME_DB_READ_TIMEOUT_SECONDS),
        )
        if not response.ok:
            return []
        rows = response.json()
    except BaseException as exc:
        # Never swallow process-control exceptions such as KeyboardInterrupt or
        # SystemExit outside this narrowly bounded optional history fetch.
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        return []

    out = []
    for row in rows if isinstance(rows, list) else []:
        item = labmod._parse_row(row)
        if item:
            out.append(item)
    return out


def _outcome_from_candidate_run(candidate, run, phase="durable_history"):
    candidate = dict(candidate or {})
    run = dict(run or {})
    diff = dict(candidate.get("mutation_diff") or {})
    direction = v2193._direction_from_diff(diff)
    replacement = v2193._replacement_from_diff(diff)
    if not direction or not replacement:
        return None
    if candidate.get("parent_verified_score") is None:
        return None
    if candidate.get("parent_verified_pass_rate") is None:
        return None

    parent_score = float(candidate.get("parent_verified_score") or 0)
    parent_pass = float(candidate.get("parent_verified_pass_rate") or 0)
    candidate_score = float(run.get("average_score") or 0)
    candidate_pass = float(run.get("pass_rate") or 0)
    score_delta = round(candidate_score - parent_score, 1)
    pass_delta = round(candidate_pass - parent_pass, 1)
    candidate_id = candidate.get("candidate_id")
    evaluation_id = run.get("run_id")
    outcome_id = "MTO-" + labmod._hash([
        candidate.get("skill_id"), candidate_id, evaluation_id, phase,
    ])[:10].upper()
    target_case = candidate.get("mutation_target_case_id")
    case_ids = [
        item.get("case_id") for item in (run.get("case_results") or [])
        if item.get("case_id")
    ]
    outcome_class = v2193._classify_delta(score_delta, pass_delta)
    return {
        "kind": "skill_mutation_outcome_view",
        "outcome_id": outcome_id,
        "source": "durable_candidate_and_benchmark_records",
        "persisted_via_existing_records": True,
        "skill_id": candidate.get("skill_id"),
        "base_version": int(candidate.get("base_version") or 1),
        "phase": phase,
        "candidate_id": candidate_id,
        "evaluation_id": evaluation_id,
        "parent_candidate_id": candidate.get("parent_candidate_id"),
        "mutation_attempt_id": candidate.get("mutation_attempt_id"),
        "mutation_key": candidate.get("mutation_key"),
        "mutation_diff": diff,
        "direction": direction,
        "replacement": replacement[:700],
        "target_case_id": target_case,
        "target_weakness": candidate.get("mutation_target_weakness"),
        "parent_score": parent_score,
        "parent_pass_rate": parent_pass,
        "candidate_score": candidate_score,
        "candidate_pass_rate": candidate_pass,
        "score_delta": score_delta,
        "pass_rate_delta": pass_delta,
        "outcome": outcome_class,
        "catastrophic": bool(
            score_delta <= CATASTROPHIC_SCORE_DELTA
            or pass_delta <= CATASTROPHIC_PASS_RATE_DELTA
        ),
        "affected_case_ids": case_ids,
        # Exact per-case deltas require a second reference-run read. v2.19.3.1
        # intentionally avoids that read after a completed benchmark. The target
        # case remains available as conservative directional evidence.
        "damaged_case_ids": [target_case] if target_case and outcome_class == "harmful" else [],
        "improved_case_ids": [target_case] if target_case and outcome_class == "beneficial" else [],
        "case_deltas": [],
        "case_delta_mode": "targeted_without_post_benchmark_read",
    }


def _durable_history(lab, active):
    """Bulk reconstruct cross-session outcome evidence with bounded I/O."""
    key = _cache_key(active.get("skill_id"), active.get("version"))
    now = time.monotonic()
    cached = _HISTORY_CACHE.get(key)
    if cached and now - cached.get("loaded_at", 0) <= OUTCOME_HISTORY_CACHE_SECONDS:
        return list(cached.get("outcomes") or [])

    legacy = _bounded_records(lab, MUTATION_OUTCOME_CATEGORY, 500)
    candidates = _bounded_records(
        lab, labmod.SKILL_CANDIDATE_CATEGORY, OUTCOME_HISTORY_CANDIDATE_LIMIT
    )
    runs = _bounded_records(
        lab, labmod.SKILL_BENCHMARK_RUN_CATEGORY, OUTCOME_HISTORY_RUN_LIMIT
    )

    sid = labmod._slug(active.get("skill_id"))
    version = int(active.get("version") or 1)
    current_suite = None
    for run in runs:
        if (
            labmod._slug(run.get("skill_id")) == sid
            and str(run.get("target_kind") or "").lower() == "active"
            and run.get("suite_hash")
        ):
            current_suite = run.get("suite_hash")
            break

    candidate_map = {}
    for candidate in candidates:
        cid = candidate.get("candidate_id")
        if not cid or cid in candidate_map:
            continue
        if labmod._slug(candidate.get("skill_id")) != sid:
            continue
        if int(candidate.get("base_version") or -1) != version:
            continue
        candidate_map[cid] = candidate

    reconstructed = []
    for run in runs:
        if str(run.get("target_kind") or "").lower() != "candidate":
            continue
        if labmod._slug(run.get("skill_id")) != sid:
            continue
        if current_suite and run.get("suite_hash") and run.get("suite_hash") != current_suite:
            continue
        candidate = candidate_map.get(run.get("candidate_id"))
        if not candidate:
            continue
        try:
            fingerprint = lab._profile_fingerprint(lab._candidate_profile(candidate))
            if run.get("profile_fingerprint") and run.get("profile_fingerprint") != fingerprint:
                continue
        except Exception:
            pass
        item = _outcome_from_candidate_run(candidate, run)
        if item:
            reconstructed.append(item)

    merged = _dedupe_outcomes(list(legacy) + reconstructed)
    _HISTORY_CACHE[key] = {"loaded_at": now, "outcomes": merged}
    return list(merged)


def _remember_local_outcome(outcome):
    if not outcome:
        return
    key = _cache_key(outcome.get("skill_id"), outcome.get("base_version"))
    bucket = _LOCAL_OUTCOMES.setdefault(key, {})
    bucket[outcome.get("outcome_id")] = dict(outcome)


def _build_learning_context_v21931(lab, active):
    key = _cache_key(active.get("skill_id"), active.get("version"))
    durable = _durable_history(lab, active)
    local = list((_LOCAL_OUTCOMES.get(key) or {}).values())
    outcomes = _dedupe_outcomes(durable + local)
    stats = v2193._direction_stats(outcomes)
    harmful = [item for item in outcomes if item.get("outcome") == "harmful"]
    beneficial = [item for item in outcomes if item.get("outcome") == "beneficial"]
    return {
        "skill_id": active.get("skill_id"),
        "base_version": int(active.get("version") or 1),
        "outcomes": outcomes,
        "direction_stats": stats,
        "harmful": harmful,
        "beneficial": beneficial,
        "outcome_count": len(outcomes),
        "history_transport": "bounded_bulk_reconstruction",
    }


# v2.19.3's candidate proposer resolves this module global at runtime.
v2193._build_learning_context = _build_learning_context_v21931


def _outcome_from_completed_result(result):
    result = dict(result or {})
    candidate = dict(result.get("candidate") or {})
    run = dict(result.get("evaluation") or {})
    if not candidate or not run:
        return None
    mode = result.get("mode")
    phase = "confirmation" if mode == "champion_confirmation" else "initial"
    outcome = _outcome_from_candidate_run(candidate, run, phase=phase)
    if not outcome:
        return None
    session = dict(result.get("session") or {})
    round_data = dict(result.get("round") or {})
    outcome["session_id"] = session.get("session_id")
    outcome["round_number"] = round_data.get("round_number")
    check = dict(result.get("champion_check") or {})
    outcome["champion_confirmation"] = bool(check)
    outcome["champion_confirmed"] = check.get("confirmed") if check else None
    outcome["created_at"] = datetime.now(timezone.utc).isoformat()
    return outcome


# The core method captured by v2.19.3 before it installed its post-benchmark
# bookkeeping wrapper. Calling this directly preserves all candidate, benchmark,
# champion, round, and session persistence while skipping redundant outcome I/O.
_CORE_ADVANCE = v2193._PREVIOUS_ADVANCE


def _advance_fail_safe(self, skill_name):
    result = _CORE_ADVANCE(skill_name)
    if not isinstance(result, dict):
        return result
    if result.get("mode") in {"candidate_round", "champion_confirmation"}:
        outcome = _outcome_from_completed_result(result)
        if outcome:
            _remember_local_outcome(outcome)
            result["mutation_outcome"] = outcome
            result["mutation_outcome_persistence"] = {
                "source_of_truth": [
                    "skill_candidate",
                    "skill_benchmark_run",
                    "skill_training_round",
                    "skill_training_session",
                ],
                "post_benchmark_database_reads": 0,
                "post_benchmark_database_writes": 0,
                "deterministic_outcome_id": True,
                "response_fail_safe": True,
            }
    return result


TRAINER.advance = types.MethodType(_advance_fail_safe, TRAINER)


_PREVIOUS_STATUS = app.view_functions.get("status")


def status_v21931():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["fail_safe_mutation_outcome_persistence_enabled"] = True
    data["post_benchmark_outcome_database_reads"] = 0
    data["post_benchmark_outcome_database_writes"] = 0
    data["mutation_outcome_source_of_truth"] = "existing_durable_training_records"
    data["mutation_history_bounded_bulk_reads_enabled"] = True
    data["mutation_history_read_timeout_seconds"] = OUTCOME_DB_READ_TIMEOUT_SECONDS
    data["automatic_skill_activation_enabled"] = False
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "fail_safe_mutation_outcome_persistence",
        "zero_post_benchmark_outcome_io",
        "deterministic_mutation_outcome_views",
        "bounded_bulk_mutation_history",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v21931

_ORIGINAL_SAFE_SOURCE_FILES = v2193._safe_source_files_v2193


def _safe_source_files_v21931():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_3_1.py"]))


v2193.v219231.v21923.v21922.v21921.v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v21931
EXECUTOR.safe_source_files_fn = _safe_source_files_v21931


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "MAX_MUTATED_FIELDS", "MUTATION_ATTEMPT_CATEGORY", "MAX_NOVELTY_OPTIONS",
    "MUTATION_TRANSPORT", "MAX_LOCAL_FALLBACK_OPTIONS",
    "MUTATION_OUTCOME_CATEGORY", "OUTCOME_LEARNING_MODE",
    "OUTCOME_DB_CONNECT_TIMEOUT_SECONDS", "OUTCOME_DB_READ_TIMEOUT_SECONDS",
    "OUTCOME_HISTORY_CACHE_SECONDS", "_bounded_records", "_outcome_from_candidate_run",
    "_durable_history", "_build_learning_context_v21931",
    "_outcome_from_completed_result", "_advance_fail_safe",
]
