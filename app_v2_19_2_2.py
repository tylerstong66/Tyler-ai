"""Tyler AI v2.19.2.2 — persistent mutation novelty tracking.

v2.19.2 constrained champion mutation correctly rejected duplicate candidate
profiles, but repeated model generations could rediscover the same mutation and
stall a training round. This patch persists mutation attempts, feeds recent
attempts back into the generation prompt, asks for a small slate of alternatives
in one provider call, and selects the first locally verified novel profile.

The provider budget remains one candidate-generation call plus one benchmark per
round. Champion protection, one-field mutation, structural preflight, two-run
champion confirmation, and human-only skill activation remain unchanged.
"""

import re
import types

import app_v2_19_2_1 as v21921
import skill_lab as labmod

v21921.base.VERSION = "2.19.2.2-mutation-novelty-tracking"
v21921.base.VERSION_SHORT = "v2.19.2.2"

base = v21921.base
app = v21921.app
ENGINE = v21921.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21921.EXECUTOR
DRILL_EXECUTOR = v21921.DRILL_EXECUTOR
PLANNER = v21921.PLANNER
OPS = v21921.OPS
REVIEW_GATE = v21921.REVIEW_GATE
PROMOTION = v21921.PROMOTION
MERGE_GATE = v21921.MERGE_GATE
SKILL_LAB = v21921.SKILL_LAB
TRAINER = v21921.TRAINER
verify_production = v21921.verify_production
BENCHMARK_OUTPUT_BUDGET = v21921.BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = v21921.BENCHMARK_TRANSPORT
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = v21921.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = v21921.ITERATIVE_CANDIDATE_OUTPUT_TOKENS
MAX_MUTATED_FIELDS = v21921.MAX_MUTATED_FIELDS

MUTATION_ATTEMPT_CATEGORY = "skill_mutation_attempt"
MAX_NOVELTY_OPTIONS = 3
MAX_EXCLUDED_MUTATIONS_IN_PROMPT = 24
base.SPECIAL_MEMORY_CATEGORIES.add(MUTATION_ATTEMPT_CATEGORY)


def _norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _mutation_key(kind, index, replacement):
    return labmod._hash([
        _norm(kind).lower(),
        int(index or 0),
        _norm(replacement).lower(),
    ])


def _parse_mutation_slate(raw, limit=MAX_NOVELTY_OPTIONS):
    """Parse one or more compact mutation options from one provider response."""
    blocks = []
    current = []
    for raw_line in str(raw or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("OPTION="):
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        if upper.startswith("TARGET_KIND=") and any(
            item.upper().startswith("TARGET_KIND=") for item in current
        ):
            blocks.append("\n".join(current))
            current = []
        if any(upper.startswith(prefix) for prefix in (
            "TARGET_KIND=", "TARGET_INDEX=", "REPLACEMENT=", "RATIONALE="
        )):
            current.append(line)
    if current:
        blocks.append("\n".join(current))

    out = []
    errors = []
    for block in blocks[:max(1, int(limit))]:
        try:
            out.append(v21921.v2192._parse_mutation_text(block))
        except Exception as exc:
            errors.append(str(exc))
    if not out:
        detail = errors[0] if errors else "no mutation options were returned"
        raise RuntimeError(f"Mutation generator returned no valid novelty options: {detail}.")
    return out


def _attempt_records(lab, skill_id, limit=500):
    sid = labmod._slug(skill_id)
    return [
        item for item in lab._records(MUTATION_ATTEMPT_CATEGORY, limit)
        if labmod._slug(item.get("skill_id")) == sid
    ]


def _candidate_mutation_descriptors(lab, active):
    descriptors = []
    for item in lab.candidates(active["skill_id"], 300):
        if int(item.get("base_version") or -1) != int(active.get("version") or 0):
            continue
        diff = dict(item.get("mutation_diff") or {})
        kind = diff.get("kind")
        index = diff.get("resolved_index") or diff.get("index")
        replacement = diff.get("after")
        if kind and index and replacement:
            descriptors.append({
                "kind": _norm(kind).lower(),
                "index": int(index),
                "replacement": _norm(replacement),
                "mutation_key": _mutation_key(kind, index, replacement),
                "profile_signature": item.get("profile_signature"),
                "source": "candidate",
            })
    return descriptors


def _known_mutations(lab, active):
    """Return persisted and historical mutation descriptors, newest first."""
    out = []
    seen = set()
    for item in _attempt_records(lab, active["skill_id"], 500):
        kind = _norm(item.get("target_kind")).lower()
        index = int(item.get("resolved_target_index") or item.get("target_index") or 0)
        replacement = _norm(item.get("replacement"))
        if not kind or index < 1 or not replacement:
            continue
        key = item.get("mutation_key") or _mutation_key(kind, index, replacement)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "kind": kind,
            "index": index,
            "replacement": replacement,
            "mutation_key": key,
            "profile_signature": item.get("profile_signature"),
            "source": "attempt",
        })
    for item in _candidate_mutation_descriptors(lab, active):
        key = item["mutation_key"]
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _excluded_prompt_lines(known, limit=MAX_EXCLUDED_MUTATIONS_IN_PROMPT):
    lines = []
    for item in list(known or [])[:max(1, int(limit))]:
        replacement = _norm(item.get("replacement"))[:180]
        lines.append(f"{item.get('kind')}#{item.get('index')} => {replacement}")
    return lines


def _save_mutation_attempt(lab, active, parent, mutation, *, outcome,
                           requested_index=None, resolved_index=None,
                           profile_signature=None, error=None, option_number=None,
                           session_id=None):
    kind = _norm((mutation or {}).get("target_kind")).lower()
    replacement = _norm((mutation or {}).get("replacement"))
    requested = int(
        requested_index
        if requested_index is not None
        else (mutation or {}).get("target_index") or 0
    )
    resolved = int(resolved_index if resolved_index is not None else requested)
    key = _mutation_key(kind, resolved, replacement) if kind and resolved and replacement else None
    payload = {
        "kind": "skill_mutation_attempt",
        "attempt_id": "MTA-" + labmod._hash([
            active.get("skill_id"), active.get("version"), kind, requested,
            resolved, replacement, outcome, lab._now().isoformat(), option_number,
        ])[:10].upper(),
        "skill_id": active.get("skill_id"),
        "base_version": int(active.get("version") or 1),
        "parent_candidate_id": (parent or {}).get("candidate_id"),
        "session_id": session_id,
        "option_number": option_number,
        "target_kind": kind,
        "target_index": requested,
        "resolved_target_index": resolved,
        "replacement": replacement[:700],
        "replacement_hash": labmod._hash(replacement) if replacement else None,
        "mutation_key": key,
        "profile_signature": profile_signature,
        "outcome": _norm(outcome).lower(),
        "error": _norm(error)[:1000] if error else None,
        "created_at": lab._now().isoformat(),
    }
    return lab._save(MUTATION_ATTEMPT_CATEGORY, payload, 6)


def _novelty_propose_candidate(self, skill_name):
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
    focus = v21921.v2192._champion_focus(active, champion)
    known = _known_mutations(self, active)
    known_keys = {item.get("mutation_key") for item in known if item.get("mutation_key")}
    prior_signatures = {
        v21921.v2192._profile_signature(
            item.get("instructions") or [], item.get("success_criteria") or []
        )
        for item in self.candidates(active["skill_id"], 300)
        if int(item.get("base_version") or -1) == int(active.get("version") or 0)
    }

    numbered_instructions = " || ".join(
        f"{i}:{value}" for i, value in enumerate(parent_instructions, 1)
    ) or "none"
    numbered_criteria = " || ".join(
        f"{i}:{value}" for i, value in enumerate(parent_criteria, 1)
    ) or "none"
    exclusions = _excluded_prompt_lines(known)
    exclusion_text = " || ".join(exclusions) if exclusions else "none"

    prompt = "\n".join([
        "Design THREE distinct surgical mutations to the verified Tyler AI skill parent.",
        "Each option may replace exactly one existing instruction OR one existing success criterion.",
        "Do not add, delete, reorder, or rewrite any other field. Do not change tools.",
        "All three options must differ from each other and from every excluded mutation below.",
        "Target the supplied benchmark weakness while preserving every other parent strength.",
        "Return up to three options using exactly this compact format:",
        "OPTION=1",
        "TARGET_KIND=instruction OR criterion",
        "TARGET_INDEX=<1-based integer from the numbered parent list>",
        "REPLACEMENT=<one concise replacement for only that field>",
        "RATIONALE=<very short reason>",
        "Then OPTION=2 and OPTION=3 in the same format. No prose outside the options.",
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
        "EXCLUDED PRIOR MUTATIONS: " + exclusion_text,
    ])

    raw = self.engine.complete([
        {
            "role": "system",
            "content": (
                "Produce a compact slate of distinct one-field skill mutations. "
                "Never regenerate the whole profile, never change tools, and do not repeat excluded edits."
            ),
        },
        {"role": "user", "content": prompt},
    ], tokens=ITERATIVE_CANDIDATE_OUTPUT_TOKENS, temperature=0, json_mode=False)

    options = _parse_mutation_slate(raw, MAX_NOVELTY_OPTIONS)
    selected = None
    rejected_reasons = []
    session_id = session.get("session_id")

    for option_number, mutation in enumerate(options, 1):
        requested = int(mutation.get("target_index") or 0)
        try:
            fixed = v21921._repair_target_index(parent, mutation)
            resolved = int(fixed.get("target_index") or 0)
            key = _mutation_key(fixed.get("target_kind"), resolved, fixed.get("replacement"))
            if key in known_keys:
                _save_mutation_attempt(
                    self, active, parent, mutation,
                    outcome="duplicate_mutation", requested_index=requested,
                    resolved_index=resolved, option_number=option_number,
                    session_id=session_id,
                )
                rejected_reasons.append(f"option {option_number}: duplicate mutation")
                continue

            instructions, criteria, diff = v21921._single_mutation_with_index_repair(parent, mutation)
            allowed_tools = list(parent.get("allowed_tools") or [])
            preflight = v21921.v2192._structural_preflight(
                parent, instructions, criteria, allowed_tools
            )
            signature = v21921.v2192._profile_signature(instructions, criteria)
            if signature in prior_signatures:
                _save_mutation_attempt(
                    self, active, parent, mutation,
                    outcome="duplicate_profile", requested_index=requested,
                    resolved_index=resolved, profile_signature=signature,
                    option_number=option_number, session_id=session_id,
                )
                rejected_reasons.append(f"option {option_number}: duplicate profile")
                continue

            attempt = _save_mutation_attempt(
                self, active, parent, mutation,
                outcome="selected_novel_candidate", requested_index=requested,
                resolved_index=resolved, profile_signature=signature,
                option_number=option_number, session_id=session_id,
            )
            selected = {
                "mutation": mutation,
                "instructions": instructions,
                "criteria": criteria,
                "allowed_tools": allowed_tools,
                "diff": diff,
                "preflight": preflight,
                "signature": signature,
                "attempt": attempt,
                "resolved_index": resolved,
                "mutation_key": key,
                "option_number": option_number,
            }
            break
        except Exception as exc:
            _save_mutation_attempt(
                self, active, parent, mutation,
                outcome="invalid_mutation", requested_index=requested,
                resolved_index=(locals().get("resolved") if "resolved" in locals() else requested),
                error=str(exc), option_number=option_number, session_id=session_id,
            )
            rejected_reasons.append(f"option {option_number}: {str(exc)}")

    if not selected:
        detail = "; ".join(rejected_reasons[:MAX_NOVELTY_OPTIONS]) or "no novel option survived preflight"
        raise RuntimeError(
            "Mutation novelty slate exhausted without a new valid profile. "
            f"Tried {len(options)} option(s): {detail}."
        )

    created = self._now().isoformat()
    candidate_number = 1 + sum(
        1 for item in self.candidates(active["skill_id"], 300)
        if int(item.get("base_version") or -1) == int(active.get("version") or 0)
    )
    cid = "CND-" + labmod._hash([
        active["skill_id"], active.get("version"), selected["instructions"],
        selected["criteria"], candidate_number, created,
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
        "mutation_novelty_tracking": True,
        "mutation_novelty_option": selected["option_number"],
        "mutation_attempt_id": selected["attempt"].get("attempt_id"),
        "mutation_key": selected["mutation_key"],
        "mutation_diff": selected["diff"],
        "mutation_target_case_id": focus.get("case_id"),
        "mutation_target_weakness": focus.get("weakness"),
        "preflight": selected["preflight"],
        "instructions": selected["instructions"],
        "success_criteria": selected["criteria"],
        "allowed_tools": selected["allowed_tools"],
        "rationale": _norm(selected["mutation"].get("rationale"))[:2500],
        "profile_signature": selected["signature"],
        "status": "candidate",
        "created_at": created,
    }
    return self._save(labmod.SKILL_CANDIDATE_CATEGORY, payload, 8)


SKILL_LAB.propose_candidate = types.MethodType(_novelty_propose_candidate, SKILL_LAB)

_PREVIOUS_HANDLE = base.handle_message


def handle_message_v21922(message):
    text = _norm(message).lower()
    if text in {"show mutation novelty", "mutation novelty status"}:
        status = TRAINER.status()
        reply = "\n".join([
            "Tyler Mutation Novelty Tracking v2.19.2.2",
            f"Alternative mutations generated per provider call: up to {MAX_NOVELTY_OPTIONS}",
            "Persisted attempted-mutation memory: enabled",
            "Duplicate mutation exclusion in future prompts: enabled",
            "Duplicate profile preflight: enabled",
            "Additional provider calls for novelty retry: disabled",
            "Verified champion protection: enabled",
            "Automatic activation: disabled",
            "Human promotion approval: required",
        ])
        return base.base_payload(
            "mutation_novelty_status", reply,
            used_tools=["skill_lab", "champion_training", "mutation_novelty"], success=True,
        ) | {"champion_training": status}, 200
    return _PREVIOUS_HANDLE(message)


base.handle_message = handle_message_v21922

_PREVIOUS_STATUS = app.view_functions.get("status")


def status_v21922():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["mutation_novelty_tracking_enabled"] = True
    data["mutation_novelty_options_per_generation"] = MAX_NOVELTY_OPTIONS
    data["mutation_attempt_memory_category"] = MUTATION_ATTEMPT_CATEGORY
    data["additional_provider_calls_for_novelty_retry"] = 0
    data["automatic_skill_activation_enabled"] = False
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "persistent_mutation_novelty_tracking",
        "single_call_mutation_slate",
        "duplicate_mutation_prompt_exclusion",
        "local_novelty_preflight",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v21922

_ORIGINAL_SAFE_SOURCE_FILES = v21921._safe_source_files_v21921


def _safe_source_files_v21922():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_2_2.py"]))


v21921.v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v21922
EXECUTOR.safe_source_files_fn = _safe_source_files_v21922


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "MAX_MUTATED_FIELDS", "MUTATION_ATTEMPT_CATEGORY", "MAX_NOVELTY_OPTIONS",
    "_mutation_key", "_parse_mutation_slate", "_known_mutations",
    "_novelty_propose_candidate",
]
