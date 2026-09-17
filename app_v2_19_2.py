"""Tyler AI v2.19.2 — constrained champion mutation.

Each training candidate changes exactly one instruction or success criterion from the
verified champion. The runtime applies the mutation itself, performs a structural
drift preflight before benchmarking, preserves tools exactly, and records a rollback-
safe mutation diff. Champion verification and human promotion gates remain unchanged.
"""

import re
import types

import app_v2_19_1 as v2191
import skill_lab as labmod

v2191.base.VERSION = "2.19.2-constrained-champion-mutation"
v2191.base.VERSION_SHORT = "v2.19.2"

base = v2191.base
app = v2191.app
ENGINE = v2191.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v2191.EXECUTOR
DRILL_EXECUTOR = v2191.DRILL_EXECUTOR
PLANNER = v2191.PLANNER
OPS = v2191.OPS
REVIEW_GATE = v2191.REVIEW_GATE
PROMOTION = v2191.PROMOTION
MERGE_GATE = v2191.MERGE_GATE
SKILL_LAB = v2191.SKILL_LAB
TRAINER = v2191.TRAINER
verify_production = v2191.verify_production
BENCHMARK_OUTPUT_BUDGET = v2191.BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = v2191.BENCHMARK_TRANSPORT
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = v2191.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = v2191.ITERATIVE_CANDIDATE_OUTPUT_TOKENS

MAX_MUTATED_FIELDS = 1
MAX_REPLACEMENT_CHARS = 600
MAX_REPLACEMENT_RATIO = 3.0


def _norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _dedupe(items, limit=20):
    seen, out = set(), []
    for item in items or []:
        value = _norm(item)
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            out.append(value)
        if len(out) >= limit:
            break
    return out


def _profile_signature(instructions, criteria):
    return labmod._hash({
        "instructions": list(instructions or []),
        "success_criteria": list(criteria or []),
    })


def _parse_mutation_text(raw):
    fields = {}
    for line in str(raw or "").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = re.sub(r"[^A-Z_]", "", key.strip().upper())
        if key in {"TARGET_KIND", "TARGET_INDEX", "REPLACEMENT", "RATIONALE"}:
            fields[key] = value.strip()
    kind = _norm(fields.get("TARGET_KIND")).lower()
    if kind in {"criterion", "criteria", "success_criterion", "successcriteria"}:
        kind = "criterion"
    elif kind in {"instruction", "instructions"}:
        kind = "instruction"
    else:
        raise RuntimeError("Mutation generator returned an invalid TARGET_KIND.")
    try:
        index = int(_norm(fields.get("TARGET_INDEX")))
    except Exception as exc:
        raise RuntimeError("Mutation generator returned an invalid TARGET_INDEX.") from exc
    replacement = _norm(fields.get("REPLACEMENT"))
    rationale = _norm(fields.get("RATIONALE"))
    if not replacement:
        raise RuntimeError("Mutation generator returned no replacement text.")
    return {
        "target_kind": kind,
        "target_index": index,
        "replacement": replacement,
        "rationale": rationale,
    }


def _single_mutation(parent, mutation):
    instructions = list(parent.get("instructions") or [])
    criteria = list(parent.get("success_criteria") or [])
    kind = mutation["target_kind"]
    index = int(mutation["target_index"]) - 1
    target = instructions if kind == "instruction" else criteria
    if index < 0 or index >= len(target):
        raise RuntimeError("Mutation target index is outside the verified parent profile.")
    old_value = str(target[index])
    new_value = mutation["replacement"]
    if _norm(old_value).lower() == _norm(new_value).lower():
        raise RuntimeError("Mutation did not change the selected parent field.")
    if len(new_value) > MAX_REPLACEMENT_CHARS:
        raise RuntimeError("Mutation replacement is too large for constrained training.")
    ratio_limit = max(180, int(max(1, len(old_value)) * MAX_REPLACEMENT_RATIO))
    if len(new_value) > ratio_limit:
        raise RuntimeError("Mutation replacement drifted too far in length from its parent field.")
    target[index] = new_value
    return instructions, criteria, {
        "kind": kind,
        "index": index + 1,
        "before": old_value,
        "after": new_value,
    }


def _structural_preflight(parent, instructions, criteria, allowed_tools):
    parent_instructions = list(parent.get("instructions") or [])
    parent_criteria = list(parent.get("success_criteria") or [])
    parent_tools = list(parent.get("allowed_tools") or [])
    if len(instructions) != len(parent_instructions):
        raise RuntimeError("Mutation preflight blocked instruction-count drift.")
    if len(criteria) != len(parent_criteria):
        raise RuntimeError("Mutation preflight blocked success-criteria-count drift.")
    if list(allowed_tools or []) != parent_tools:
        raise RuntimeError("Mutation preflight blocked tool-permission drift.")
    changes = []
    for index, (before, after) in enumerate(zip(parent_instructions, instructions), 1):
        if str(before) != str(after):
            changes.append(("instruction", index))
    for index, (before, after) in enumerate(zip(parent_criteria, criteria), 1):
        if str(before) != str(after):
            changes.append(("criterion", index))
    if len(changes) != MAX_MUTATED_FIELDS:
        raise RuntimeError(
            f"Mutation preflight requires exactly {MAX_MUTATED_FIELDS} changed profile field."
        )
    return {"changed_fields": len(changes), "changes": changes, "passed": True}


def _champion_focus(active, champion):
    if champion:
        runs = TRAINER._valid_candidate_runs(active, champion)
        for run in runs:
            cases = list(run.get("case_results") or [])
            if cases:
                weakest = min(cases, key=lambda x: int(x.get("score") or 0))
                weaknesses = [_norm(x) for x in weakest.get("weaknesses") or [] if _norm(x)]
                return {
                    "case_id": weakest.get("case_id") or "unknown",
                    "score": int(weakest.get("score") or 0),
                    "weakness": weaknesses[0] if weaknesses else "Improve the weakest benchmark behavior.",
                }
    feedback = TRAINER.feedback_bundle(active["skill_id"], max_attempts=8)
    weaknesses = feedback.get("active_weaknesses") or ["Improve the weakest benchmark behavior."]
    return {"case_id": "active-fallback", "score": None, "weakness": _norm(weaknesses[0])}


def _constrained_propose_candidate(self, skill_name):
    active = self.engine.get_skill(skill_name)
    if not active:
        raise ValueError(f"Skill {skill_name!r} was not found.")

    champion = TRAINER.champion_candidate(active["skill_id"])
    parent = champion or active
    parent_instructions = list(parent.get("instructions") or [])
    parent_criteria = list(parent.get("success_criteria") or [])
    if not parent_instructions and not parent_criteria:
        raise RuntimeError("Verified parent has no mutable skill fields.")

    session = TRAINER.latest_session(active["skill_id"]) or {}
    parent_score = float(
        session.get("champion_score")
        if champion else session.get("baseline_average_score") or 0
    )
    parent_pass = float(
        session.get("champion_pass_rate")
        if champion else session.get("baseline_pass_rate") or 0
    )
    focus = _champion_focus(active, champion)

    numbered_instructions = " || ".join(
        f"{i}:{value}" for i, value in enumerate(parent_instructions, 1)
    ) or "none"
    numbered_criteria = " || ".join(
        f"{i}:{value}" for i, value in enumerate(parent_criteria, 1)
    ) or "none"
    prompt = "\n".join([
        "Design ONE surgical mutation to the verified Tyler AI skill parent.",
        "You may replace exactly one existing instruction OR exactly one existing success criterion.",
        "Do not add, delete, reorder, or rewrite any other field. Do not change tools.",
        "Target the supplied benchmark weakness while preserving every other parent strength.",
        "Return exactly four tagged lines and nothing else:",
        "TARGET_KIND=instruction OR criterion",
        "TARGET_INDEX=<1-based integer from the numbered parent list>",
        "REPLACEMENT=<one concise replacement for only that field>",
        "RATIONALE=<one concise sentence>",
        f"PARENT TYPE: {'verified champion' if champion else 'active baseline'}",
        f"PARENT CANDIDATE: {(champion or {}).get('candidate_id') or 'active-v' + str(active.get('version') or 1)}",
        f"PARENT SCORE: {parent_score}",
        f"PARENT PASS RATE: {parent_pass}",
        f"TARGET BENCHMARK CASE: {focus.get('case_id')}",
        f"TARGET BENCHMARK SCORE: {focus.get('score')}",
        f"TARGET WEAKNESS: {focus.get('weakness')}",
        "NUMBERED INSTRUCTIONS: " + numbered_instructions,
        "NUMBERED SUCCESS CRITERIA: " + numbered_criteria,
        "ALLOWED TOOLS (IMMUTABLE): " + " | ".join(active.get("allowed_tools") or []),
    ])
    raw = self.engine.complete([
        {
            "role": "system",
            "content": (
                "Produce exactly one narrow skill-profile replacement operation. "
                "Never regenerate the whole profile and never change tool permissions."
            ),
        },
        {"role": "user", "content": prompt},
    ], tokens=ITERATIVE_CANDIDATE_OUTPUT_TOKENS, temperature=0, json_mode=False)

    mutation = _parse_mutation_text(raw)
    instructions, criteria, diff = _single_mutation(parent, mutation)
    allowed_tools = list(parent.get("allowed_tools") or [])
    preflight = _structural_preflight(parent, instructions, criteria, allowed_tools)

    prior_signatures = {
        _profile_signature(item.get("instructions") or [], item.get("success_criteria") or [])
        for item in self.candidates(active["skill_id"], 300)
        if int(item.get("base_version") or -1) == int(active.get("version") or 0)
    }
    signature = _profile_signature(instructions, criteria)
    if signature in prior_signatures:
        raise RuntimeError("Constrained mutation repeated an already evaluated profile.")

    created = self._now().isoformat()
    candidate_number = 1 + sum(
        1 for item in self.candidates(active["skill_id"], 300)
        if int(item.get("base_version") or -1) == int(active.get("version") or 0)
    )
    cid = "CND-" + labmod._hash([
        active["skill_id"], active.get("version"), instructions, criteria, candidate_number, created
    ])[:10].upper()
    payload = {
        "kind": "skill_candidate",
        "candidate_id": cid,
        "skill_id": active["skill_id"],
        "name": active.get("name"),
        "purpose": active.get("purpose"),
        "base_version": int(active.get("version") or 1),
        "candidate_version": int(active.get("version") or 1) + 1,
        "iteration_attempt": candidate_number,
        "parent_candidate_id": (champion or {}).get("candidate_id"),
        "parent_verified_score": parent_score,
        "parent_verified_pass_rate": parent_pass,
        "evolved_from_champion": bool(champion),
        "constrained_mutation": True,
        "mutation_diff": diff,
        "mutation_target_case_id": focus.get("case_id"),
        "mutation_target_weakness": focus.get("weakness"),
        "preflight": preflight,
        "instructions": instructions,
        "success_criteria": criteria,
        "allowed_tools": allowed_tools,
        "rationale": mutation.get("rationale")[:2500],
        "profile_signature": signature,
        "status": "candidate",
        "created_at": created,
    }
    return self._save(labmod.SKILL_CANDIDATE_CATEGORY, payload, 8)


SKILL_LAB.propose_candidate = types.MethodType(_constrained_propose_candidate, SKILL_LAB)

_PREVIOUS_HANDLE = base.handle_message


def handle_message_v2192(message):
    text = _norm(message).lower()
    if text in {"show constrained training", "constrained training status"}:
        status = TRAINER.status()
        reply = "\n".join([
            "Tyler Constrained Champion Mutation v2.19.2",
            "Mutation scope per candidate: exactly one existing profile field",
            "Whole-profile regeneration: disabled",
            "Structural drift preflight before benchmark: enabled",
            "Tool-permission mutation: blocked",
            "Rollback-safe mutation diff: persisted",
            "Verified champion protection: enabled",
            "Two-run champion confirmation: required",
            "Automatic activation: disabled",
            "Human promotion approval: required",
        ])
        return base.base_payload(
            "constrained_champion_training_status", reply,
            used_tools=["skill_lab", "champion_training", "constrained_mutation"], success=True,
        ) | {"champion_training": status}, 200
    return _PREVIOUS_HANDLE(message)


base.handle_message = handle_message_v2192

_PREVIOUS_STATUS = app.view_functions.get("status")


def status_v2192():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["constrained_champion_mutation_enabled"] = True
    data["max_mutated_profile_fields"] = MAX_MUTATED_FIELDS
    data["whole_profile_candidate_regeneration_enabled"] = False
    data["automatic_skill_activation_enabled"] = False
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "constrained_champion_mutation",
        "single_field_skill_mutation",
        "pre_benchmark_structural_drift_gate",
        "rollback_safe_mutation_diff",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v2192

_ORIGINAL_SAFE_SOURCE_FILES = v2191._safe_source_files_v2191


def _safe_source_files_v2192():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_2.py"]))


v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v2192
EXECUTOR.safe_source_files_fn = _safe_source_files_v2192


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "MAX_MUTATED_FIELDS", "_parse_mutation_text", "_single_mutation",
    "_structural_preflight", "_constrained_propose_candidate",
]
