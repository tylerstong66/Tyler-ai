"""Tyler AI v2.19.2.3 — resilient mutation transport and local fallback.

v2.19.2.2 added persistent novelty tracking and single-call mutation slates. In
production, the constrained provider can still return a truncated or differently
formatted slate. This patch accepts common tagged/Markdown/JSON variants and, if
no provider option survives parsing/preflight, derives a bounded one-field fallback
locally from the weakest benchmark evidence. The fallback does not make another
provider call and remains subject to novelty checks, structural preflight, champion
protection, benchmark evaluation, and human-only promotion.
"""

import json
import re
import types

import app_v2_19_2_2 as v21922
import skill_lab as labmod

v21922.base.VERSION = "2.19.2.3-resilient-mutation-transport"
v21922.base.VERSION_SHORT = "v2.19.2.3"

base = v21922.base
app = v21922.app
ENGINE = v21922.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21922.EXECUTOR
DRILL_EXECUTOR = v21922.DRILL_EXECUTOR
PLANNER = v21922.PLANNER
OPS = v21922.OPS
REVIEW_GATE = v21922.REVIEW_GATE
PROMOTION = v21922.PROMOTION
MERGE_GATE = v21922.MERGE_GATE
SKILL_LAB = v21922.SKILL_LAB
TRAINER = v21922.TRAINER
verify_production = v21922.verify_production
BENCHMARK_OUTPUT_BUDGET = v21922.BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = v21922.BENCHMARK_TRANSPORT
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = v21922.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = v21922.ITERATIVE_CANDIDATE_OUTPUT_TOKENS
MAX_MUTATED_FIELDS = v21922.MAX_MUTATED_FIELDS
MUTATION_ATTEMPT_CATEGORY = v21922.MUTATION_ATTEMPT_CATEGORY
MAX_NOVELTY_OPTIONS = v21922.MAX_NOVELTY_OPTIONS

MUTATION_TRANSPORT = "resilient-tags-json-markdown-with-local-fallback"
MAX_LOCAL_FALLBACK_OPTIONS = 12


def _norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_kind(value):
    kind = re.sub(r"[^a-z_]", "", _norm(value).lower().replace(" ", "_"))
    if kind in {"criterion", "criteria", "success_criterion", "successcriteria"}:
        return "criterion"
    if kind in {"instruction", "instructions"}:
        return "instruction"
    raise RuntimeError("Mutation generator returned an invalid TARGET_KIND.")


def _normalize_index(value):
    match = re.search(r"-?\d+", str(value or ""))
    if not match:
        raise RuntimeError("Mutation generator returned an invalid TARGET_INDEX.")
    return int(match.group(0))


def _coerce_mutation(item):
    if not isinstance(item, dict):
        raise RuntimeError("Mutation option was not an object.")
    lower = {re.sub(r"[^a-z]", "", str(k).lower()): v for k, v in item.items()}
    kind = lower.get("targetkind") or lower.get("kind")
    index = lower.get("targetindex") or lower.get("index")
    replacement = lower.get("replacement") or lower.get("replacewith") or lower.get("text")
    rationale = lower.get("rationale") or lower.get("reason") or ""
    mutation = {
        "target_kind": _normalize_kind(kind),
        "target_index": _normalize_index(index),
        "replacement": _norm(replacement),
        "rationale": _norm(rationale),
    }
    if not mutation["replacement"]:
        raise RuntimeError("Mutation generator returned no replacement text.")
    return mutation


def _json_mutation_options(raw, limit):
    cleaned = str(raw or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        data = json.loads(cleaned)
    except Exception:
        return []
    if isinstance(data, dict):
        for key in ("options", "mutations", "candidates"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            data = [data]
    if not isinstance(data, list):
        return []
    out = []
    for item in data[:max(1, int(limit))]:
        try:
            out.append(_coerce_mutation(item))
        except Exception:
            continue
    return out


def _canonical_field_line(line):
    line = str(line or "").strip()
    line = re.sub(r"^\s*(?:[-*•]+|\d+[.)])\s*", "", line)
    line = line.replace("**", "").replace("__", "").replace("`", "").strip()
    match = re.match(
        r"^(TARGET[ _-]?KIND|TARGET[ _-]?INDEX|REPLACEMENT|RATIONALE)\s*(?:=|:|->|—|-)\s*(.+?)\s*$",
        line,
        flags=re.I,
    )
    if not match:
        return None
    raw_key = re.sub(r"[^A-Z]", "", match.group(1).upper())
    key_map = {
        "TARGETKIND": "TARGET_KIND",
        "TARGETINDEX": "TARGET_INDEX",
        "REPLACEMENT": "REPLACEMENT",
        "RATIONALE": "RATIONALE",
    }
    key = key_map.get(raw_key)
    return (key, match.group(2).strip()) if key else None


def _tagged_mutation_options(raw, limit):
    text = str(raw or "")
    text = re.sub(r"```(?:text|yaml|markdown)?", "", text, flags=re.I).replace("```", "")
    blocks = []
    current = {}
    for original in text.splitlines():
        line = original.strip()
        if not line:
            continue
        cleaned = line.replace("**", "").replace("__", "").replace("`", "").strip()
        if re.match(r"^(?:[-*•]\s*)?(?:OPTION|MUTATION)\s*(?:[=#:\-]?\s*\d+)?\s*:??\s*$", cleaned, flags=re.I):
            if current:
                blocks.append(current)
                current = {}
            continue
        parsed = _canonical_field_line(line)
        if not parsed:
            continue
        key, value = parsed
        if key == "TARGET_KIND" and "TARGET_KIND" in current:
            blocks.append(current)
            current = {}
        current[key] = value
    if current:
        blocks.append(current)

    # Some providers collapse all tags onto one line. Recover those segments too.
    if not blocks:
        compact = text.replace("**", "").replace("__", "").replace("`", "")
        field_pattern = re.compile(
            r"(TARGET[ _-]?KIND|TARGET[ _-]?INDEX|REPLACEMENT|RATIONALE)\s*(?:=|:|->)\s*",
            flags=re.I,
        )
        matches = list(field_pattern.finditer(compact))
        if matches:
            current = {}
            for idx, match in enumerate(matches):
                raw_key = re.sub(r"[^A-Z]", "", match.group(1).upper())
                key = {
                    "TARGETKIND": "TARGET_KIND",
                    "TARGETINDEX": "TARGET_INDEX",
                    "REPLACEMENT": "REPLACEMENT",
                    "RATIONALE": "RATIONALE",
                }.get(raw_key)
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(compact)
                value = compact[match.end():end].strip(" \t\r\n,;|-")
                if key == "TARGET_KIND" and "TARGET_KIND" in current:
                    blocks.append(current)
                    current = {}
                if key:
                    current[key] = value
            if current:
                blocks.append(current)

    out = []
    for block in blocks[:max(1, int(limit))]:
        try:
            out.append(_coerce_mutation(block))
        except Exception:
            continue
    return out


def _parse_mutation_slate_resilient(raw, limit=MAX_NOVELTY_OPTIONS):
    """Accept strict tags plus common JSON/Markdown/provider formatting variants."""
    out = _json_mutation_options(raw, limit)
    if not out:
        out = _tagged_mutation_options(raw, limit)
    if not out:
        # Preserve the original strict parser as a final compatibility attempt.
        try:
            out = v21922._ORIGINAL_PARSE_MUTATION_SLATE(raw, limit)
        except Exception:
            out = []
    if not out:
        raise RuntimeError(
            "Mutation generator returned no valid novelty options after resilient parsing."
        )
    return out[:max(1, int(limit))]


# Preserve the v2.19.2.2 implementation and replace only its parser dependency.
if not hasattr(v21922, "_ORIGINAL_PARSE_MUTATION_SLATE"):
    v21922._ORIGINAL_PARSE_MUTATION_SLATE = v21922._parse_mutation_slate
v21922._parse_mutation_slate = _parse_mutation_slate_resilient


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "the", "to", "with", "only", "this",
}


def _word_set(value):
    return {
        token for token in re.findall(r"[a-z0-9]+", _norm(value).lower())
        if len(token) > 2 and token not in _STOPWORDS
    }


def _rank_parent_targets(parent, weakness):
    weak_words = _word_set(weakness)
    targets = []
    for kind, values in (
        ("instruction", list(parent.get("instructions") or [])),
        ("criterion", list(parent.get("success_criteria") or [])),
    ):
        for index, value in enumerate(values, 1):
            overlap = len(weak_words.intersection(_word_set(value)))
            # Prefer semantically overlapping fields, then instructions, then stable order.
            targets.append((-overlap, 0 if kind == "instruction" else 1, index, kind, str(value)))
    targets.sort()
    return [(kind, index, value) for _, _, index, kind, value in targets]


def _trim_requirement(value, limit=120):
    text = _norm(value)
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:")
    return (clipped or text[:limit]).rstrip() + "…"


def _fit_fallback_replacement(old_value, weakness, variant):
    old = _norm(old_value)
    requirement = _trim_requirement(weakness, 120)
    if not old or not requirement:
        return None
    suffixes = [
        f"Also explicitly satisfy this requirement: {requirement}",
        f"Before reporting completion, explicitly satisfy: {requirement}",
        f"Verification must explicitly cover this requirement: {requirement}",
    ]
    suffix = suffixes[int(variant) % len(suffixes)]
    max_chars = min(
        int(v21922.v21921.v2192.MAX_REPLACEMENT_CHARS),
        max(180, int(max(1, len(old)) * float(v21922.v21921.v2192.MAX_REPLACEMENT_RATIO))),
    )
    available = max_chars - len(old) - 1
    if available < 36:
        return None
    if len(suffix) > available:
        suffix = suffix[:available].rsplit(" ", 1)[0].rstrip(" ,;:")
    if len(suffix) < 24:
        return None
    return f"{old} {suffix}".strip()


def _local_fallback_mutations(parent, focus, limit=MAX_LOCAL_FALLBACK_OPTIONS):
    weakness = _norm((focus or {}).get("weakness")) or "Improve the weakest benchmark behavior."
    out = []
    seen = set()
    for kind, index, old_value in _rank_parent_targets(parent, weakness):
        for variant in range(3):
            replacement = _fit_fallback_replacement(old_value, weakness, variant)
            if not replacement:
                continue
            key = v21922._mutation_key(kind, index, replacement)
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "target_kind": kind,
                "target_index": index,
                "replacement": replacement,
                "rationale": "Deterministic fallback targeting the weakest verified benchmark evidence.",
            })
            if len(out) >= max(1, int(limit)):
                return out
    return out


def _deterministic_fallback_candidate(self, skill_name, trigger_error):
    active = self.engine.get_skill(skill_name)
    if not active:
        raise ValueError(f"Skill {skill_name!r} was not found.")
    champion = TRAINER.champion_candidate(active["skill_id"])
    parent = champion or active
    if not (parent.get("instructions") or parent.get("success_criteria")):
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
    focus = v21922.v21921.v2192._champion_focus(active, champion)
    known = v21922._known_mutations(self, active)
    known_keys = {item.get("mutation_key") for item in known if item.get("mutation_key")}
    prior_signatures = {
        v21922.v21921.v2192._profile_signature(
            item.get("instructions") or [], item.get("success_criteria") or []
        )
        for item in self.candidates(active["skill_id"], 300)
        if int(item.get("base_version") or -1) == int(active.get("version") or 0)
    }
    session_id = session.get("session_id")
    selected = None
    rejected = []
    options = _local_fallback_mutations(parent, focus, MAX_LOCAL_FALLBACK_OPTIONS)

    for local_number, mutation in enumerate(options, 1):
        requested = int(mutation.get("target_index") or 0)
        resolved = requested
        try:
            fixed = v21922.v21921._repair_target_index(parent, mutation)
            resolved = int(fixed.get("target_index") or requested)
            key = v21922._mutation_key(
                fixed.get("target_kind"), resolved, fixed.get("replacement")
            )
            if key in known_keys:
                v21922._save_mutation_attempt(
                    self, active, parent, mutation,
                    outcome="fallback_duplicate_mutation",
                    requested_index=requested, resolved_index=resolved,
                    option_number=1000 + local_number, session_id=session_id,
                    error=trigger_error,
                )
                rejected.append(f"fallback {local_number}: duplicate mutation")
                continue

            instructions, criteria, diff = v21922.v21921._single_mutation_with_index_repair(
                parent, mutation
            )
            allowed_tools = list(parent.get("allowed_tools") or [])
            preflight = v21922.v21921.v2192._structural_preflight(
                parent, instructions, criteria, allowed_tools
            )
            signature = v21922.v21921.v2192._profile_signature(instructions, criteria)
            if signature in prior_signatures:
                v21922._save_mutation_attempt(
                    self, active, parent, mutation,
                    outcome="fallback_duplicate_profile",
                    requested_index=requested, resolved_index=resolved,
                    profile_signature=signature,
                    option_number=1000 + local_number, session_id=session_id,
                    error=trigger_error,
                )
                rejected.append(f"fallback {local_number}: duplicate profile")
                continue

            attempt = v21922._save_mutation_attempt(
                self, active, parent, mutation,
                outcome="fallback_selected_novel_candidate",
                requested_index=requested, resolved_index=resolved,
                profile_signature=signature,
                option_number=1000 + local_number, session_id=session_id,
                error=trigger_error,
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
                "mutation_key": key,
                "local_number": local_number,
            }
            break
        except Exception as exc:
            v21922._save_mutation_attempt(
                self, active, parent, mutation,
                outcome="fallback_invalid_mutation",
                requested_index=requested, resolved_index=resolved,
                error=f"{trigger_error} | fallback: {exc}",
                option_number=1000 + local_number, session_id=session_id,
            )
            rejected.append(f"fallback {local_number}: {exc}")

    if not selected:
        detail = "; ".join(rejected[:5]) or "no bounded local fallback could be created"
        raise RuntimeError(
            "Mutation transport recovery exhausted without a new valid profile. "
            f"Provider issue: {trigger_error}. Local recovery: {detail}."
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
        "mutation_resilient_transport": True,
        "mutation_generation_source": "deterministic_fallback",
        "mutation_transport": MUTATION_TRANSPORT,
        "mutation_novelty_option": 1000 + selected["local_number"],
        "mutation_attempt_id": selected["attempt"].get("attempt_id"),
        "mutation_key": selected["mutation_key"],
        "mutation_diff": selected["diff"],
        "mutation_target_case_id": focus.get("case_id"),
        "mutation_target_weakness": focus.get("weakness"),
        "mutation_fallback_trigger": _norm(trigger_error)[:1000],
        "preflight": selected["preflight"],
        "instructions": selected["instructions"],
        "success_criteria": selected["criteria"],
        "allowed_tools": selected["allowed_tools"],
        "rationale": selected["mutation"].get("rationale"),
        "profile_signature": selected["signature"],
        "status": "candidate",
        "created_at": created,
    }
    return self._save(labmod.SKILL_CANDIDATE_CATEGORY, payload, 8)


def _resilient_propose_candidate(self, skill_name):
    try:
        candidate = v21922._novelty_propose_candidate(self, skill_name)
        if isinstance(candidate, dict):
            candidate.setdefault("mutation_resilient_transport", True)
            candidate.setdefault("mutation_generation_source", "provider")
            candidate.setdefault("mutation_transport", MUTATION_TRANSPORT)
        return candidate
    except RuntimeError as exc:
        message = str(exc)
        recoverable = (
            "no valid novelty options" in message.lower()
            or "novelty slate exhausted" in message.lower()
            or "no valid novelty options after resilient parsing" in message.lower()
        )
        if not recoverable:
            raise
        return _deterministic_fallback_candidate(self, skill_name, message)


SKILL_LAB.propose_candidate = types.MethodType(_resilient_propose_candidate, SKILL_LAB)

_PREVIOUS_HANDLE = base.handle_message


def handle_message_v21923(message):
    text = _norm(message).lower()
    if text in {"show mutation novelty", "mutation novelty status", "show mutation transport"}:
        status = TRAINER.status()
        reply = "\n".join([
            "Tyler Mutation Transport v2.19.2.3",
            "Strict tagged mutation parsing: enabled",
            "Markdown/colon/bullet parsing: enabled",
            "JSON mutation parsing: enabled",
            "Single-line tag recovery: enabled",
            f"Provider alternatives per call: up to {MAX_NOVELTY_OPTIONS}",
            f"Bounded local fallback options: up to {MAX_LOCAL_FALLBACK_OPTIONS}",
            "Additional provider calls for format recovery: 0",
            "Persistent duplicate exclusion: enabled",
            "Verified champion protection: enabled",
            "Automatic activation: disabled",
            "Human promotion approval: required",
        ])
        return base.base_payload(
            "mutation_transport_status", reply,
            used_tools=["skill_lab", "champion_training", "mutation_novelty", "mutation_transport"],
            success=True,
        ) | {"champion_training": status}, 200
    return _PREVIOUS_HANDLE(message)


base.handle_message = handle_message_v21923

_PREVIOUS_STATUS = app.view_functions.get("status")


def status_v21923():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["mutation_resilient_transport_enabled"] = True
    data["mutation_transport"] = MUTATION_TRANSPORT
    data["mutation_json_parsing_enabled"] = True
    data["mutation_markdown_parsing_enabled"] = True
    data["mutation_local_fallback_enabled"] = True
    data["mutation_local_fallback_max_options"] = MAX_LOCAL_FALLBACK_OPTIONS
    data["additional_provider_calls_for_format_recovery"] = 0
    data["automatic_skill_activation_enabled"] = False
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "resilient_mutation_transport",
        "mutation_json_markdown_parsing",
        "deterministic_local_mutation_fallback",
        "zero_extra_provider_call_format_recovery",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v21923

_ORIGINAL_SAFE_SOURCE_FILES = v21922._safe_source_files_v21922


def _safe_source_files_v21923():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_2_3.py"]))


v21922.v21921.v2192.v2191.v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v21923
EXECUTOR.safe_source_files_fn = _safe_source_files_v21923


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "MAX_MUTATED_FIELDS", "MUTATION_ATTEMPT_CATEGORY", "MAX_NOVELTY_OPTIONS",
    "MUTATION_TRANSPORT", "MAX_LOCAL_FALLBACK_OPTIONS",
    "_parse_mutation_slate_resilient", "_local_fallback_mutations",
    "_deterministic_fallback_candidate", "_resilient_propose_candidate",
]
