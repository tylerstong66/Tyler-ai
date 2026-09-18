"""Tyler AI v2.19.3 — mutation outcome learning.

Builds on v2.19.2.3.1 without weakening any existing champion, benchmark,
promotion, or tool-permission safety gate. Every evaluated constrained mutation
is recorded with score/pass-rate deltas and per-case damage/improvement. Future
provider slates and deterministic fallback mutations are ranked using that
history, with close semantic repeats of catastrophic edits rejected before a
benchmark is spent.
"""

from contextvars import ContextVar
import re
import types

import app_v2_19_2_3_1 as v219231
import skill_lab as labmod

v219231.base.VERSION = "2.19.3-mutation-outcome-learning"
v219231.base.VERSION_SHORT = "v2.19.3"

base = v219231.base
app = v219231.app
ENGINE = v219231.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v219231.EXECUTOR
DRILL_EXECUTOR = v219231.DRILL_EXECUTOR
PLANNER = v219231.PLANNER
OPS = v219231.OPS
REVIEW_GATE = v219231.REVIEW_GATE
PROMOTION = v219231.PROMOTION
MERGE_GATE = v219231.MERGE_GATE
SKILL_LAB = v219231.SKILL_LAB
TRAINER = v219231.TRAINER
verify_production = v219231.verify_production
BENCHMARK_OUTPUT_BUDGET = v219231.BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = v219231.BENCHMARK_TRANSPORT
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = v219231.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = v219231.ITERATIVE_CANDIDATE_OUTPUT_TOKENS
MAX_MUTATED_FIELDS = v219231.MAX_MUTATED_FIELDS
MUTATION_ATTEMPT_CATEGORY = v219231.MUTATION_ATTEMPT_CATEGORY
MAX_NOVELTY_OPTIONS = v219231.MAX_NOVELTY_OPTIONS
MUTATION_TRANSPORT = v219231.MUTATION_TRANSPORT
# Outcome learning can reject an entire mutation direction after a harmful run.
# Keep a wider, still-bounded recovery slate so the remaining safe directions do
# not collapse to the same three deterministic edits on every request.
MAX_LOCAL_FALLBACK_OPTIONS = max(48, v219231.MAX_LOCAL_FALLBACK_OPTIONS)
v219231.v21923.MAX_LOCAL_FALLBACK_OPTIONS = MAX_LOCAL_FALLBACK_OPTIONS

MUTATION_OUTCOME_CATEGORY = "skill_mutation_outcome"
OUTCOME_HISTORY_LIMIT = 500
HARMFUL_SEMANTIC_BLOCK_THRESHOLD = 0.88
CATASTROPHIC_SCORE_DELTA = -15.0
CATASTROPHIC_PASS_RATE_DELTA = -20.0
OUTCOME_LEARNING_MODE = "persistent-delta-direction-and-semantic-ranking"
base.SPECIAL_MEMORY_CATEGORIES.add(MUTATION_OUTCOME_CATEGORY)

_LEARNING_CONTEXT = ContextVar("tyler_mutation_learning_context", default=None)


def _norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _words(value):
    return {
        token for token in re.findall(r"[a-z0-9]+", _norm(value).lower())
        if len(token) > 2
    }


def _semantic_similarity(left, right):
    a = _words(left)
    b = _words(right)
    if not a or not b:
        return 0.0
    return len(a.intersection(b)) / max(1, len(a.union(b)))


def _direction_from_diff(diff):
    diff = dict(diff or {})
    kind = _norm(diff.get("kind") or diff.get("target_kind")).lower()
    index = int(diff.get("resolved_index") or diff.get("index") or diff.get("target_index") or 0)
    return f"{kind}#{index}" if kind and index > 0 else None


def _replacement_from_diff(diff):
    diff = dict(diff or {})
    return _norm(diff.get("after") or diff.get("replacement"))


def _classify_delta(score_delta, pass_delta):
    score_delta = float(score_delta or 0)
    pass_delta = float(pass_delta or 0)
    if score_delta >= 0 and pass_delta >= 0 and (score_delta > 0 or pass_delta > 0):
        return "beneficial"
    if score_delta < 0 or pass_delta < 0:
        return "harmful"
    return "neutral"


def _persisted_outcomes(lab, active, limit=OUTCOME_HISTORY_LIMIT):
    sid = labmod._slug(active.get("skill_id"))
    version = int(active.get("version") or 1)
    return [
        item for item in lab._records(MUTATION_OUTCOME_CATEGORY, limit)
        if labmod._slug(item.get("skill_id")) == sid
        and int(item.get("base_version") or -1) == version
    ]


def _latest_candidate_run(lab, active, candidate_id):
    target = str(candidate_id or "").upper()
    suite_hash = lab._suite_hash(active["skill_id"])
    for run in lab.evaluations(active["skill_id"], "candidate", 500):
        if str(run.get("candidate_id") or "").upper() != target:
            continue
        if run.get("suite_hash") and run.get("suite_hash") != suite_hash:
            continue
        return run
    return None


def _historical_outcomes(lab, active, limit=300):
    """Derive learning evidence from older constrained candidates without rewriting history."""
    out = []
    seen = set()
    version = int(active.get("version") or 1)
    for candidate in lab.candidates(active["skill_id"], limit):
        cid = candidate.get("candidate_id")
        if not cid or cid in seen:
            continue
        seen.add(cid)
        if int(candidate.get("base_version") or -1) != version:
            continue
        diff = dict(candidate.get("mutation_diff") or {})
        direction = _direction_from_diff(diff)
        replacement = _replacement_from_diff(diff)
        if not direction or not replacement:
            continue
        run = _latest_candidate_run(lab, active, cid)
        if not run:
            continue
        parent_score = float(candidate.get("parent_verified_score") or 0)
        parent_pass = float(candidate.get("parent_verified_pass_rate") or 0)
        candidate_score = float(run.get("average_score") or 0)
        candidate_pass = float(run.get("pass_rate") or 0)
        score_delta = round(candidate_score - parent_score, 1)
        pass_delta = round(candidate_pass - parent_pass, 1)
        out.append({
            "kind": "derived_skill_mutation_outcome",
            "source": "historical_candidate",
            "skill_id": active.get("skill_id"),
            "base_version": version,
            "candidate_id": cid,
            "evaluation_id": run.get("run_id"),
            "parent_candidate_id": candidate.get("parent_candidate_id"),
            "mutation_key": candidate.get("mutation_key"),
            "mutation_diff": diff,
            "direction": direction,
            "replacement": replacement,
            "parent_score": parent_score,
            "parent_pass_rate": parent_pass,
            "candidate_score": candidate_score,
            "candidate_pass_rate": candidate_pass,
            "score_delta": score_delta,
            "pass_rate_delta": pass_delta,
            "outcome": _classify_delta(score_delta, pass_delta),
            "case_deltas": [],
        })
    return out


def _learning_outcomes(lab, active):
    persisted = _persisted_outcomes(lab, active)
    keys = {
        (item.get("candidate_id"), item.get("evaluation_id"))
        for item in persisted
    }
    merged = list(persisted)
    for item in _historical_outcomes(lab, active):
        key = (item.get("candidate_id"), item.get("evaluation_id"))
        if key not in keys:
            keys.add(key)
            merged.append(item)
    return merged


def _direction_stats(outcomes):
    grouped = {}
    for item in outcomes or []:
        direction = item.get("direction") or _direction_from_diff(item.get("mutation_diff"))
        if not direction:
            continue
        bucket = grouped.setdefault(direction, {
            "count": 0,
            "score_total": 0.0,
            "pass_total": 0.0,
            "beneficial_count": 0,
            "harmful_count": 0,
        })
        bucket["count"] += 1
        bucket["score_total"] += float(item.get("score_delta") or 0)
        bucket["pass_total"] += float(item.get("pass_rate_delta") or 0)
        if item.get("outcome") == "beneficial":
            bucket["beneficial_count"] += 1
        elif item.get("outcome") == "harmful":
            bucket["harmful_count"] += 1
    for direction, bucket in grouped.items():
        count = max(1, bucket["count"])
        bucket["average_score_delta"] = round(bucket["score_total"] / count, 2)
        bucket["average_pass_rate_delta"] = round(bucket["pass_total"] / count, 2)
        bucket["direction_value"] = round(
            bucket["average_score_delta"] + 0.25 * bucket["average_pass_rate_delta"], 2
        )
    return grouped


def _build_learning_context(lab, active):
    outcomes = _learning_outcomes(lab, active)
    stats = _direction_stats(outcomes)
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
    }


def _mutation_learning_rank(mutation, context):
    context = context or {}
    kind = _norm((mutation or {}).get("target_kind")).lower()
    index = int((mutation or {}).get("target_index") or 0)
    replacement = _norm((mutation or {}).get("replacement"))
    direction = f"{kind}#{index}" if kind and index else None
    stats = (context.get("direction_stats") or {}).get(direction) or {}
    score = float(stats.get("direction_value") or 0)
    strongest_harmful_similarity = 0.0
    strongest_beneficial_similarity = 0.0
    blocking_outcome_id = None

    for item in context.get("harmful") or []:
        prior = item.get("replacement") or _replacement_from_diff(item.get("mutation_diff"))
        similarity = _semantic_similarity(replacement, prior)
        strongest_harmful_similarity = max(strongest_harmful_similarity, similarity)
        severity = min(
            30.0,
            abs(float(item.get("score_delta") or 0)) +
            0.25 * abs(float(item.get("pass_rate_delta") or 0)),
        )
        score -= similarity * severity
        catastrophic = (
            float(item.get("score_delta") or 0) <= CATASTROPHIC_SCORE_DELTA
            or float(item.get("pass_rate_delta") or 0) <= CATASTROPHIC_PASS_RATE_DELTA
        )
        if catastrophic and similarity >= HARMFUL_SEMANTIC_BLOCK_THRESHOLD:
            blocking_outcome_id = item.get("outcome_id") or item.get("candidate_id")

    for item in context.get("beneficial") or []:
        prior = item.get("replacement") or _replacement_from_diff(item.get("mutation_diff"))
        similarity = _semantic_similarity(replacement, prior)
        strongest_beneficial_similarity = max(strongest_beneficial_similarity, similarity)
        benefit = min(
            20.0,
            max(0.0, float(item.get("score_delta") or 0)) +
            0.25 * max(0.0, float(item.get("pass_rate_delta") or 0)),
        )
        score += similarity * benefit

    return {
        "direction": direction,
        "score": round(score, 3),
        "hard_block": blocking_outcome_id is not None,
        "blocking_outcome_id": blocking_outcome_id,
        "harmful_similarity": round(strongest_harmful_similarity, 3),
        "beneficial_similarity": round(strongest_beneficial_similarity, 3),
    }


# v2.19.2.3 installed the resilient parser into v2.19.2.2. Keep that parser,
# but rank the returned slate using the request-local outcome history.
_v21922 = v219231.v21923.v21922
_ORIGINAL_MUTATION_PARSE = _v21922._parse_mutation_slate


def _outcome_sorted_parse(raw, limit=MAX_NOVELTY_OPTIONS):
    options = list(_ORIGINAL_MUTATION_PARSE(raw, limit))
    context = _LEARNING_CONTEXT.get()
    if not context or not context.get("outcomes"):
        return options[:max(1, int(limit))]
    ranked = []
    for order, mutation in enumerate(options):
        info = _mutation_learning_rank(mutation, context)
        if info.get("hard_block"):
            continue
        ranked.append((float(info.get("score") or 0), -order, mutation))
    if not ranked:
        raise RuntimeError(
            "Mutation generator returned no valid novelty options after outcome-learning safety ranking."
        )
    ranked.sort(reverse=True, key=lambda item: (item[0], item[1]))
    return [item[2] for item in ranked[:max(1, int(limit))]]


_v21922._parse_mutation_slate = _outcome_sorted_parse


# Apply the same learning policy to deterministic local recovery so formatting or
# provider failures do not bypass the outcome-learning layer.
_ORIGINAL_LOCAL_FALLBACK_MUTATIONS = v219231.v21923._local_fallback_mutations

_ADAPTIVE_FALLBACK_SUFFIXES = (
    "Also explicitly satisfy this requirement: {requirement}",
    "Before reporting completion, explicitly satisfy: {requirement}",
    "Verification must explicitly cover this requirement: {requirement}",
    "Use current evidence to demonstrate: {requirement}",
    "Treat this as a required acceptance check: {requirement}",
    "Include a concrete verification step for: {requirement}",
    "Do not claim success until evidence confirms: {requirement}",
    "Make the final result auditable against: {requirement}",
    "Record the evidence used to establish: {requirement}",
    "If evidence is incomplete, say so instead of assuming: {requirement}",
    "Cross-check the completed work against: {requirement}",
    "The completion summary must state how it satisfied: {requirement}",
)


def _fit_adaptive_fallback_replacement(old_value, weakness, variant):
    """Return a bounded useful edit from a wider deterministic template bank."""
    old = _norm(old_value)
    requirement = v219231.v21923._trim_requirement(weakness, 120)
    if not old or not requirement:
        return None
    template = _ADAPTIVE_FALLBACK_SUFFIXES[
        int(variant) % len(_ADAPTIVE_FALLBACK_SUFFIXES)
    ]
    suffix = template.format(requirement=requirement)
    limits = v219231.v21923.v21922.v21921.v2192
    max_chars = min(
        int(limits.MAX_REPLACEMENT_CHARS),
        max(180, int(max(1, len(old)) * float(limits.MAX_REPLACEMENT_RATIO))),
    )
    available = max_chars - len(old) - 1
    if available < 36:
        return None
    if len(suffix) > available:
        suffix = suffix[:available].rsplit(" ", 1)[0].rstrip(" ,;:")
    if len(suffix) < 24:
        return None
    return f"{old} {suffix}".strip()


def _adaptive_local_fallback_mutations(parent, focus, limit=MAX_LOCAL_FALLBACK_OPTIONS):
    """Generate diverse bounded edits before outcome-history safety ranking.

    The old fallback exposed three phrasings per field. Once those keys had been
    attempted, retrying could never escape duplicate recovery. This generator
    keeps deterministic behavior but searches twelve phrasings across every
    mutable field. Downstream novelty, profile, structural, outcome-learning,
    benchmark, champion-confirmation, and human-promotion gates remain intact.
    """
    weakness = _norm((focus or {}).get("weakness")) or (
        "Improve the weakest benchmark behavior."
    )
    out = []
    seen = set()
    requested_limit = max(1, min(int(limit), MAX_LOCAL_FALLBACK_OPTIONS))
    for kind, index, old_value in v219231.v21923._rank_parent_targets(
        parent, weakness
    ):
        for variant in range(len(_ADAPTIVE_FALLBACK_SUFFIXES)):
            replacement = _fit_adaptive_fallback_replacement(
                old_value, weakness, variant
            )
            if not replacement:
                continue
            key = v219231.v21923.v21922._mutation_key(
                kind, index, replacement
            )
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "target_kind": kind,
                "target_index": index,
                "replacement": replacement,
                "rationale": (
                    "Adaptive deterministic fallback targeting the weakest "
                    "verified benchmark evidence."
                ),
            })
            if len(out) >= requested_limit:
                return out
    return out


def _outcome_ranked_local_fallback(parent, focus, limit=MAX_LOCAL_FALLBACK_OPTIONS):
    options = list(_adaptive_local_fallback_mutations(
        parent, focus, max(int(limit), MAX_LOCAL_FALLBACK_OPTIONS)
    ))
    context = _LEARNING_CONTEXT.get()
    if not context or not context.get("outcomes"):
        return options[:max(1, int(limit))]
    ranked = []
    for order, mutation in enumerate(options):
        info = _mutation_learning_rank(mutation, context)
        if info.get("hard_block"):
            continue
        ranked.append((float(info.get("score") or 0), -order, mutation))
    ranked.sort(reverse=True, key=lambda item: (item[0], item[1]))
    return [item[2] for item in ranked[:max(1, int(limit))]]


v219231.v21923._local_fallback_mutations = _outcome_ranked_local_fallback


_PREVIOUS_PROPOSE = SKILL_LAB.propose_candidate


def _outcome_learning_propose_candidate(self, skill_name):
    active = self.engine.get_skill(skill_name)
    if not active:
        raise ValueError(f"Skill {skill_name!r} was not found.")
    context = _build_learning_context(self, active)
    token = _LEARNING_CONTEXT.set(context)
    try:
        candidate = _PREVIOUS_PROPOSE(skill_name)
    finally:
        _LEARNING_CONTEXT.reset(token)
    if isinstance(candidate, dict):
        candidate = dict(candidate)
        rank = _mutation_learning_rank({
            "target_kind": (candidate.get("mutation_diff") or {}).get("kind"),
            "target_index": (candidate.get("mutation_diff") or {}).get("resolved_index")
                or (candidate.get("mutation_diff") or {}).get("index"),
            "replacement": (candidate.get("mutation_diff") or {}).get("after"),
        }, context)
        candidate["mutation_outcome_learning"] = True
        candidate["mutation_learning_mode"] = OUTCOME_LEARNING_MODE
        candidate["mutation_learning_history_count"] = context.get("outcome_count", 0)
        candidate["mutation_learning_rank"] = rank
    return candidate


SKILL_LAB.propose_candidate = types.MethodType(_outcome_learning_propose_candidate, SKILL_LAB)


def _case_delta_summary(candidate_run, reference_run):
    reference = {
        str(item.get("case_id")): item
        for item in (reference_run or {}).get("case_results") or []
        if item.get("case_id")
    }
    out = []
    for item in (candidate_run or {}).get("case_results") or []:
        case_id = item.get("case_id")
        if not case_id:
            continue
        prior = reference.get(str(case_id)) or {}
        score = float(item.get("score") or 0)
        previous_score = float(prior.get("score") or 0)
        delta = round(score - previous_score, 1)
        out.append({
            "case_id": case_id,
            "reference_score": previous_score,
            "candidate_score": score,
            "score_delta": delta,
            "damaged": delta < 0,
            "improved": delta > 0,
            "weaknesses": [
                _norm(x) for x in item.get("weaknesses") or [] if _norm(x)
            ][:8],
        })
    return out


def _reference_run_for_candidate(trainer, lab, active, candidate):
    parent_id = candidate.get("parent_candidate_id")
    if parent_id:
        try:
            parent = trainer._candidate_by_id(active["skill_id"], parent_id)
            runs = trainer._valid_candidate_runs(active, parent) if parent else []
            if runs:
                return runs[0]
        except Exception:
            pass
    try:
        return lab._valid_eval(active, "active")
    except Exception:
        return None


def _record_candidate_outcome(lab, trainer, result, phase="initial"):
    candidate = dict((result or {}).get("candidate") or {})
    run = dict((result or {}).get("evaluation") or {})
    if not candidate or not run:
        return None
    diff = dict(candidate.get("mutation_diff") or {})
    direction = _direction_from_diff(diff)
    replacement = _replacement_from_diff(diff)
    if not direction or not replacement:
        return None

    active = lab.engine.get_skill(candidate.get("skill_id"))
    if not active:
        return None
    evaluation_id = run.get("run_id")
    candidate_id = candidate.get("candidate_id")
    for existing in _persisted_outcomes(lab, active):
        if (
            existing.get("candidate_id") == candidate_id
            and existing.get("evaluation_id") == evaluation_id
        ):
            return existing

    parent_score = float(candidate.get("parent_verified_score") or 0)
    parent_pass = float(candidate.get("parent_verified_pass_rate") or 0)
    candidate_score = float(run.get("average_score") or 0)
    candidate_pass = float(run.get("pass_rate") or 0)
    score_delta = round(candidate_score - parent_score, 1)
    pass_delta = round(candidate_pass - parent_pass, 1)
    reference_run = _reference_run_for_candidate(trainer, lab, active, candidate)
    case_deltas = _case_delta_summary(run, reference_run)
    damaged = [item.get("case_id") for item in case_deltas if item.get("damaged")]
    improved = [item.get("case_id") for item in case_deltas if item.get("improved")]
    confirmation = dict((result or {}).get("champion_check") or {})
    created = lab._now().isoformat()
    payload = {
        "kind": "skill_mutation_outcome",
        "outcome_id": "MTO-" + labmod._hash([
            active.get("skill_id"), candidate_id, evaluation_id, phase, created,
        ])[:10].upper(),
        "skill_id": active.get("skill_id"),
        "base_version": int(active.get("version") or 1),
        "session_id": ((result or {}).get("session") or {}).get("session_id"),
        "round_number": ((result or {}).get("round") or {}).get("round_number"),
        "phase": phase,
        "candidate_id": candidate_id,
        "evaluation_id": evaluation_id,
        "parent_candidate_id": candidate.get("parent_candidate_id"),
        "mutation_attempt_id": candidate.get("mutation_attempt_id"),
        "mutation_key": candidate.get("mutation_key"),
        "mutation_diff": diff,
        "direction": direction,
        "replacement": replacement[:700],
        "target_case_id": candidate.get("mutation_target_case_id"),
        "target_weakness": candidate.get("mutation_target_weakness"),
        "parent_score": parent_score,
        "parent_pass_rate": parent_pass,
        "candidate_score": candidate_score,
        "candidate_pass_rate": candidate_pass,
        "score_delta": score_delta,
        "pass_rate_delta": pass_delta,
        "outcome": _classify_delta(score_delta, pass_delta),
        "catastrophic": bool(
            score_delta <= CATASTROPHIC_SCORE_DELTA
            or pass_delta <= CATASTROPHIC_PASS_RATE_DELTA
        ),
        "affected_case_ids": [item.get("case_id") for item in case_deltas],
        "damaged_case_ids": damaged,
        "improved_case_ids": improved,
        "case_deltas": case_deltas[:20],
        "champion_confirmation": bool(confirmation),
        "champion_confirmed": confirmation.get("confirmed") if confirmation else None,
        "created_at": created,
    }
    return lab._save(MUTATION_OUTCOME_CATEGORY, payload, 8)


_PREVIOUS_ADVANCE = TRAINER.advance


def _advance_with_outcome_learning(self, skill_name):
    result = _PREVIOUS_ADVANCE(skill_name)
    if not isinstance(result, dict):
        return result
    mode = result.get("mode")
    if mode in {"candidate_round", "champion_confirmation"}:
        try:
            outcome = _record_candidate_outcome(
                SKILL_LAB, self, result,
                phase="confirmation" if mode == "champion_confirmation" else "initial",
            )
            if outcome:
                result["mutation_outcome"] = outcome
        except Exception as exc:
            # Outcome bookkeeping must never alter the already-completed benchmark or
            # weaken champion safety. Surface the issue for diagnostics instead.
            result["mutation_outcome_learning_warning"] = _norm(exc)[:500]
    return result


TRAINER.advance = types.MethodType(_advance_with_outcome_learning, TRAINER)


def _learning_status():
    try:
        records = SKILL_LAB._records(MUTATION_OUTCOME_CATEGORY, OUTCOME_HISTORY_LIMIT)
    except Exception:
        records = []
    harmful = sum(1 for item in records if item.get("outcome") == "harmful")
    beneficial = sum(1 for item in records if item.get("outcome") == "beneficial")
    return {
        "persistent_outcomes": len(records),
        "harmful_outcomes": harmful,
        "beneficial_outcomes": beneficial,
        "semantic_harm_block_threshold": HARMFUL_SEMANTIC_BLOCK_THRESHOLD,
        "outcome_learning_mode": OUTCOME_LEARNING_MODE,
    }


_PREVIOUS_HANDLE = base.handle_message


def handle_message_v2193(message):
    text = _norm(message).lower()
    if text in {
        "show mutation learning", "mutation learning status",
        "show mutation outcome learning", "show training learning",
    }:
        learning = _learning_status()
        reply = "\n".join([
            "Tyler Mutation Outcome Learning v2.19.3",
            f"Persistent evaluated outcomes: {learning['persistent_outcomes']}",
            f"Harmful outcomes remembered: {learning['harmful_outcomes']}",
            f"Beneficial outcomes remembered: {learning['beneficial_outcomes']}",
            "Historical constrained candidates used as learning evidence: enabled",
            "Direction-level score/pass-rate learning: enabled",
            "Semantic harmful-edit avoidance: enabled",
            "Beneficial-direction preference: enabled",
            "Per-case damage/improvement tracking: enabled",
            "Cross-session learning: enabled",
            "Verified champion protection: enabled",
            "Two-run champion confirmation: required",
            "Automatic activation: disabled",
            "Human promotion approval: required",
        ])
        return base.base_payload(
            "mutation_outcome_learning_status", reply,
            used_tools=[
                "skill_lab", "champion_training", "mutation_novelty",
                "mutation_transport", "mutation_outcome_learning",
            ],
            success=True,
        ) | {"mutation_outcome_learning": learning}, 200
    return _PREVIOUS_HANDLE(message)


base.handle_message = handle_message_v2193

_PREVIOUS_STATUS = app.view_functions.get("status")


def status_v2193():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["mutation_outcome_learning_enabled"] = True
    data["mutation_outcome_category"] = MUTATION_OUTCOME_CATEGORY
    data["mutation_outcome_learning_mode"] = OUTCOME_LEARNING_MODE
    data["mutation_harmful_semantic_block_threshold"] = HARMFUL_SEMANTIC_BLOCK_THRESHOLD
    data["mutation_cross_session_learning_enabled"] = True
    data["mutation_case_delta_tracking_enabled"] = True
    data["automatic_skill_activation_enabled"] = False
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "persistent_mutation_outcome_learning",
        "cross_session_mutation_learning",
        "mutation_direction_ranking",
        "semantic_harmful_edit_avoidance",
        "beneficial_mutation_preference",
        "per_case_mutation_delta_tracking",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v2193

_ORIGINAL_SAFE_SOURCE_FILES = v219231._safe_source_files_v219231


def _safe_source_files_v2193():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_3.py"]))


v219231.v21923.v21922.v21921.v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v2193
EXECUTOR.safe_source_files_fn = _safe_source_files_v2193


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "MAX_MUTATED_FIELDS", "MUTATION_ATTEMPT_CATEGORY", "MAX_NOVELTY_OPTIONS",
    "MUTATION_TRANSPORT", "MAX_LOCAL_FALLBACK_OPTIONS",
    "MUTATION_OUTCOME_CATEGORY", "OUTCOME_LEARNING_MODE",
    "HARMFUL_SEMANTIC_BLOCK_THRESHOLD", "CATASTROPHIC_SCORE_DELTA",
    "CATASTROPHIC_PASS_RATE_DELTA", "_semantic_similarity",
    "_historical_outcomes", "_direction_stats", "_build_learning_context",
    "_mutation_learning_rank", "_outcome_sorted_parse",
    "_outcome_ranked_local_fallback", "_record_candidate_outcome",
]
