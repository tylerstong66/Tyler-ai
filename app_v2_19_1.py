"""Tyler AI v2.19.1 — champion-based iterative Skill Lab training.

v2.19.1 preserves the best consistently verified candidate as a training champion.
A new candidate must beat the champion, then survive a second benchmark before it
can replace that champion as the parent for later drafts. No candidate becomes the
active skill without the existing human promotion approval and execute flow.
"""

import re
import types

import app_v2_19 as v219
import skill_lab as labmod
from champion_training import (
    ChampionSkillTrainer,
    SKILL_CHAMPION_CATEGORIES,
)

v219.base.VERSION = "2.19.1-champion-based-skill-training"
v219.base.VERSION_SHORT = "v2.19.1"

base = v219.base
app = v219.app
ENGINE = v219.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v219.EXECUTOR
DRILL_EXECUTOR = v219.DRILL_EXECUTOR
PLANNER = v219.PLANNER
OPS = v219.OPS
REVIEW_GATE = v219.REVIEW_GATE
PROMOTION = v219.PROMOTION
MERGE_GATE = v219.MERGE_GATE
SKILL_LAB = v219.SKILL_LAB
verify_production = v219.verify_production
BENCHMARK_OUTPUT_BUDGET = v219.BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = v219.BENCHMARK_TRANSPORT
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = v219.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = v219.ITERATIVE_CANDIDATE_OUTPUT_TOKENS

base.SPECIAL_MEMORY_CATEGORIES.update(SKILL_CHAMPION_CATEGORIES)


def _get_rows(category, limit):
    return base.get_memories(limit, category=category)


def _save_row(text, category, importance):
    return base.save_memory(text, category=category, importance=importance)


TRAINER = ChampionSkillTrainer(
    SKILL_LAB,
    _get_rows,
    _save_row,
    now_fn=base.now_iso,
    max_rounds=6,
    consistency_tolerance=10.0,
)
# app_v2_19's fallback handler resolves this global dynamically.
v219.TRAINER = TRAINER


def _dedupe(items, limit=20):
    seen, out = set(), []
    for item in items or []:
        value = labmod._norm(item)
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            out.append(value)
        if len(out) >= limit:
            break
    return out


def _profile_signature(instructions, criteria):
    return labmod._hash({
        "instructions": _dedupe(instructions, 20),
        "success_criteria": _dedupe(criteria, 20),
    })


def _champion_propose_candidate(self, skill_name):
    """Draft from the verified champion when one exists; otherwise from active."""
    active = self.engine.get_skill(skill_name)
    if not active:
        raise ValueError(f"Skill {skill_name!r} was not found.")

    champion = TRAINER.champion_candidate(active["skill_id"])
    parent = champion or active
    feedback = TRAINER.feedback_bundle(active["skill_id"], max_attempts=8)
    attempts = feedback.get("failed_attempts") or []
    history_lines = []
    for index, attempt in enumerate(attempts[:5], 1):
        history_lines.append(
            "ATTEMPT %d score=%.1f pass=%.1f weaknesses=%s" % (
                index,
                float(attempt.get("average_score") or 0),
                float(attempt.get("pass_rate") or 0),
                " | ".join(attempt.get("weaknesses") or [])[:700],
            )
        )

    session = TRAINER.latest_session(active["skill_id"]) or {}
    parent_score = (
        float(session.get("champion_score") or 0)
        if champion else float(session.get("baseline_average_score") or feedback.get("active_average_score") or 0)
    )
    parent_pass = (
        float(session.get("champion_pass_rate") or 0)
        if champion else float(session.get("baseline_pass_rate") or feedback.get("active_pass_rate") or 0)
    )

    prompt = "\n".join([
        "Create one conservative Tyler AI skill mutation from the VERIFIED PARENT profile.",
        "Preserve the parent's proven strengths; change only what targets observed failures.",
        "Do not broaden tools or permissions. Do not repeat an already evaluated profile.",
        "The new profile should beat the parent, not merely beat the active baseline.",
        "Preserve truthful reporting of writes, merges, deployments, and tool state.",
        "Return exactly three tagged lines; no JSON, Markdown, or commentary.",
        "INSTRUCTIONS=<up to 8 concise instructions separated by ||>",
        "CRITERIA=<up to 8 concise success criteria separated by ||>",
        "RATIONALE=<one concise sentence explaining the mutation>",
        f"PURPOSE: {active.get('purpose') or ''}",
        f"PARENT TYPE: {'verified champion' if champion else 'active baseline'}",
        f"PARENT CANDIDATE: {(champion or {}).get('candidate_id') or 'active-v' + str(active.get('version') or 1)}",
        f"PARENT VERIFIED SCORE: {parent_score}",
        f"PARENT VERIFIED PASS RATE: {parent_pass}",
        "PARENT INSTRUCTIONS: " + " || ".join(labmod._as_list(parent.get("instructions"))),
        "PARENT CRITERIA: " + " || ".join(labmod._as_list(parent.get("success_criteria"))),
        "ALLOWED TOOLS (MUST NOT CHANGE): " + " | ".join(labmod._as_list(active.get("allowed_tools"))),
        "ACTIVE WEAKNESSES: " + " | ".join(feedback.get("active_weaknesses") or [])[:1000],
        "RECENT CANDIDATE EVIDENCE:",
        *(history_lines or ["none"]),
    ])
    raw = self.engine.complete([
        {
            "role": "system",
            "content": (
                "Evolve Tyler AI skill profiles conservatively from the verified parent. "
                "Use only the requested tagged text format and never add permissions."
            ),
        },
        {"role": "user", "content": prompt},
    ], tokens=ITERATIVE_CANDIDATE_OUTPUT_TOKENS, temperature=0, json_mode=False)

    parsed = v219.v2182._parse_candidate_text(raw)
    instructions = _dedupe(
        parsed.get("instructions") or labmod._as_list(parent.get("instructions")), 20
    )
    criteria = _dedupe(
        parsed.get("success_criteria") or labmod._as_list(parent.get("success_criteria")), 20
    )
    if not instructions:
        raise RuntimeError("Candidate generation returned no usable instructions.")

    prior_signatures = {
        _profile_signature(item.get("instructions") or [], item.get("success_criteria") or [])
        for item in self.candidates(active["skill_id"], 200)
        if int(item.get("base_version") or -1) == int(active.get("version") or 0)
    }
    signature = _profile_signature(instructions, criteria)
    if signature in prior_signatures:
        focus = labmod._norm((
            (attempts[0].get("weaknesses") if attempts else None)
            or feedback.get("active_weaknesses")
            or ["benchmark failures"]
        )[0])
        instructions = _dedupe(
            instructions + [f"Correct the unresolved benchmark failure without losing parent strengths: {focus}"],
            20,
        )
        signature = _profile_signature(instructions, criteria)
        if signature in prior_signatures:
            raise RuntimeError("Candidate generator repeated an already evaluated profile.")

    created = self._now().isoformat()
    candidate_number = 1 + sum(
        1 for item in self.candidates(active["skill_id"], 200)
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
        "instructions": instructions[:20],
        "success_criteria": criteria[:20],
        "allowed_tools": labmod._as_list(active.get("allowed_tools"))[:20],
        "rationale": labmod._norm(parsed.get("rationale"))[:2500],
        "learned_from_failed_attempts": len(attempts),
        "profile_signature": signature,
        "status": "candidate",
        "created_at": created,
    }
    return self._save(labmod.SKILL_CANDIDATE_CATEGORY, payload, 8)


SKILL_LAB.propose_candidate = types.MethodType(_champion_propose_candidate, SKILL_LAB)


def _norm(message):
    return re.sub(r"\s+", " ", str(message or "")).strip()


def _name(pattern, message):
    match = re.fullmatch(pattern, _norm(message), flags=re.I | re.S)
    return match.group(1).strip() if match else None


def _render_session(session, heading="Champion-based skill training"):
    session = dict(session or {})
    champion_id = session.get("champion_candidate_id") or "active baseline"
    lines = [
        heading,
        f"Session: {session.get('session_id') or 'unknown'}",
        f"Skill: {session.get('skill_name') or session.get('skill_id') or 'unknown'}",
        f"Active version protected: v{session.get('active_version') or '?'}",
        f"Status: {str(session.get('status') or 'unknown').upper()}",
        f"Rounds completed: {session.get('rounds_completed') or 0}/{session.get('max_rounds') or TRAINER.max_rounds}",
        f"Active baseline: {session.get('baseline_average_score')} / {session.get('baseline_pass_rate')}%",
        f"Verified champion: {champion_id}",
        f"Champion score: {session.get('champion_score')}",
        f"Champion pass rate: {session.get('champion_pass_rate')}%",
        f"Champion verified: {'yes' if session.get('champion_verified') else 'no'}",
        "Two-run consistency confirmation for each new champion: required",
        "Automatic activation: disabled",
        "Human promotion approval: required",
    ]
    if session.get("pending_champion_candidate_id"):
        lines.extend([
            f"Pending champion: {session.get('pending_champion_candidate_id')}",
            f"Pending first score: {session.get('pending_champion_initial_score')}",
            f"Pending first pass rate: {session.get('pending_champion_initial_pass_rate')}%",
            "Next command will re-benchmark the same candidate for consistency.",
        ])
    return "\n".join(lines)


def _render_result(result):
    session = result.get("session") or {}
    candidate = result.get("candidate") or {}
    if result.get("mode") == "champion_confirmation":
        check = result.get("champion_check") or {}
        lines = [
            "Champion consistency check complete",
            f"Session: {session.get('session_id')}",
            f"Candidate: {candidate.get('candidate_id')}",
            f"First score: {check.get('initial_score')}",
            f"Confirmation score: {check.get('confirmation_score')}",
            f"Confirmed average score: {check.get('confirmed_average_score')}",
            f"First pass rate: {check.get('initial_pass_rate')}%",
            f"Confirmation pass rate: {check.get('confirmation_pass_rate')}%",
            f"Confirmed average pass rate: {check.get('confirmed_average_pass_rate')}%",
            f"Score spread: {check.get('score_spread')} (max {check.get('consistency_tolerance')})",
            f"Consistency check passed: {'yes' if check.get('confirmed') else 'no'}",
            f"Verified champion now: {session.get('champion_candidate_id') or 'active baseline'}",
            f"Verified champion score: {session.get('champion_score')}",
            f"Session status: {str(session.get('status') or '').upper()}",
            "Automatic activation: no",
        ]
        if session.get("status") == "quality_gate_passed":
            lines.extend([
                "",
                "The consistently verified champion also passed the Skill Lab quality gate.",
                f"Next: Prepare skill promotion {session.get('skill_id')}",
            ])
        elif session.get("status") == "exhausted":
            lines.extend(["", "Training round limit reached. Active skill remains unchanged."])
        else:
            lines.extend(["", f"Next: Continue iterative training {session.get('skill_id')}"])
        return "\n".join(lines)

    round_record = result.get("round") or {}
    champion = result.get("champion_metrics") or {}
    lines = [
        "Champion-based training round complete",
        f"Session: {session.get('session_id')}",
        f"Round: {round_record.get('round_number')}/{session.get('max_rounds')}",
        f"Skill: {session.get('skill_name') or session.get('skill_id')}",
        f"Active version remains: v{session.get('active_version')}",
        f"Candidate: {candidate.get('candidate_id')}",
        f"Parent champion: {candidate.get('parent_candidate_id') or 'active baseline'}",
        f"Reference champion score: {champion.get('reference_score')}",
        f"Candidate score: {champion.get('candidate_score')}",
        f"Reference champion pass rate: {champion.get('reference_pass_rate')}%",
        f"Candidate pass rate: {champion.get('candidate_pass_rate')}%",
        f"Candidate not worse than champion: {'yes' if champion.get('candidate_not_worse_than_champion') else 'no'}",
        f"Measurable champion improvement: {'yes' if champion.get('measurable_champion_improvement') else 'no'}",
        f"Beats champion on first run: {'yes' if champion.get('beats_champion') else 'no'}",
        f"Session status: {str(session.get('status') or '').upper()}",
        "Automatic activation: no",
    ]
    if session.get("status") == "champion_confirmation_required":
        lines.extend([
            "",
            "Candidate is provisional only. A second benchmark must confirm the improvement.",
            f"Next: Continue iterative training {session.get('skill_id')}",
        ])
    elif session.get("status") == "exhausted":
        lines.extend(["", "Training round limit reached. Active skill remains unchanged."])
    else:
        lines.extend([
            "",
            "Candidate did not replace the verified champion.",
            f"Next: Continue iterative training {session.get('skill_id')}",
        ])
    return "\n".join(lines)


_PREVIOUS_HANDLE = base.handle_message


def handle_message_v2191(message):
    text = _norm(message)
    lower = text.lower()

    if lower in {
        "show champion training",
        "champion training status",
        "show iterative training",
        "iterative training status",
        "show training loops",
    }:
        status = TRAINER.status()
        sessions = status.get("sessions") or []
        lines = [
            "Tyler Champion-Based Skill Training v2.19.1",
            f"Stored/current sessions: {len(sessions)}",
            f"Maximum mutation rounds per session: {status.get('max_rounds')}",
            "Verified champion retained across rounds: yes",
            "Every new champion requires a second benchmark: yes",
            f"Consistency score-spread tolerance: {status.get('consistency_tolerance')}",
            "New candidates evolve from verified champion: yes",
            "Automatic activation: disabled",
            "Human promotion approval: required",
        ]
        return base.base_payload(
            "champion_skill_training_status", "\n".join(lines),
            used_tools=["skill_lab", "iterative_training", "champion_training"], success=True,
        ) | {"champion_training": status}, 200

    name = _name(r"show\s+(?:champion|iterative)\s+training\s+(.+)", text)
    if name:
        session = TRAINER.latest_session(name)
        if not session:
            return base.base_payload(
                "champion_skill_training_status",
                f"No champion training session exists for {name}.",
                used_tools=["champion_training"], success=False,
            ), 404
        return base.base_payload(
            "champion_skill_training_status", _render_session(session),
            used_tools=["champion_training"], success=True,
        ) | {"champion_training": session}, 200

    name = _name(
        r"(?:start|begin)\s+(?:(?:champion|iterative)\s+)?(?:skill\s+)?training\s+(.+)", text
    )
    if name:
        try:
            session = TRAINER.start(name)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload(
                "champion_skill_training",
                f"Champion training was not started. Reason: {exc}",
                used_tools=["skill_lab", "champion_training"], success=False,
            ), 409
        reply = _render_session(session, "Champion-based skill training session ready")
        reply += f"\n\nNext: Continue iterative training {session.get('skill_id')}"
        return base.base_payload(
            "champion_skill_training", reply,
            used_tools=["skill_lab", "champion_training"], success=True,
        ) | {"champion_training": session}, 200

    name = _name(
        r"restart\s+(?:(?:champion|iterative)\s+)?(?:skill\s+)?training\s+(.+)", text
    )
    if name:
        try:
            session = TRAINER.start(name, restart=True)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload(
                "champion_skill_training",
                f"Champion training was not restarted. Reason: {exc}",
                used_tools=["skill_lab", "champion_training"], success=False,
            ), 409
        return base.base_payload(
            "champion_skill_training",
            _render_session(session, "Fresh champion-based training session ready") +
            f"\n\nNext: Continue iterative training {session.get('skill_id')}",
            used_tools=["skill_lab", "champion_training"], success=True,
        ) | {"champion_training": session}, 200

    name = _name(
        r"(?:(?:continue|advance)\s+(?:champion|iterative)\s+training|run\s+(?:champion|iterative)\s+training\s+round)\s+(.+)",
        text,
    )
    if name:
        try:
            result = TRAINER.advance(name)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload(
                "champion_skill_training_round",
                f"Champion training step did not run. Reason: {exc}",
                used_tools=["skill_lab", "champion_training", "reason"], success=False,
            ), 409
        return base.base_payload(
            "champion_skill_training_round", _render_result(result),
            used_tools=["skill_lab", "champion_training", "reason", "evaluate_skill"], success=True,
        ) | {"champion_training": result}, 200

    return _PREVIOUS_HANDLE(message)


base.handle_message = handle_message_v2191

_PREVIOUS_STATUS = app.view_functions.get("status")


def status_v2191():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["champion_based_skill_training_enabled"] = True
    data["champion_confirmation_required"] = True
    data["automatic_skill_activation_enabled"] = False
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "champion_based_skill_training",
        "champion_parent_mutation",
        "two_run_champion_confirmation",
        "champion_regression_protection",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v2191

_ORIGINAL_SAFE_SOURCE_FILES = v219._safe_source_files_v219


def _safe_source_files_v2191():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + [
        "champion_training.py",
        "app_v2_19_1.py",
    ]))


v219.v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v2191
EXECUTOR.safe_source_files_fn = _safe_source_files_v2191


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "_champion_propose_candidate",
]
