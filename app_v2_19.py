"""Tyler AI v2.19 — persistent iterative Skill Lab training.

v2.18 proved candidate generation, benchmarking, and regression blocking. v2.19
turns those pieces into a persistent learning loop: failed candidate evidence is
fed into the next draft, every round is benchmarked against the same active
baseline, regressions remain inactive, and only an existing human-gated Skill Lab
promotion can activate a quality-passing candidate.

Because the configured Groq tier has a low output-token-per-minute ceiling, Tyler
runs one bounded candidate+benchmark round per command and persists the session
between rounds. This is deliberate provider-aware pacing, not automatic activation.
"""

import re
import types

import app_v2_18_2 as v2182
import skill_lab as labmod
from skill_iteration import SKILL_ITERATION_CATEGORIES, IterativeSkillTrainer


v2182.base.VERSION = "2.19.0-iterative-skill-training"
v2182.base.VERSION_SHORT = "v2.19.0"

base = v2182.base
app = v2182.app
ENGINE = v2182.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v2182.EXECUTOR
DRILL_EXECUTOR = v2182.DRILL_EXECUTOR
PLANNER = v2182.PLANNER
OPS = v2182.OPS
REVIEW_GATE = v2182.REVIEW_GATE
PROMOTION = v2182.PROMOTION
MERGE_GATE = v2182.MERGE_GATE
SKILL_LAB = v2182.SKILL_LAB
verify_production = v2182.verify_production

base.SPECIAL_MEMORY_CATEGORIES.update(SKILL_ITERATION_CATEGORIES)

# Keep one complete iterative round below the observed 1,000 Groq OTPM ceiling:
# 800 requested benchmark output tokens + 150 candidate-draft tokens = 950.
ITERATIVE_BENCHMARK_OUTPUT_BUDGET = 800
ITERATIVE_CANDIDATE_OUTPUT_TOKENS = 150
v2182.v2181.BENCHMARK_OUTPUT_BUDGET = ITERATIVE_BENCHMARK_OUTPUT_BUDGET
v2182.BENCHMARK_OUTPUT_BUDGET = ITERATIVE_BENCHMARK_OUTPUT_BUDGET
BENCHMARK_OUTPUT_BUDGET = ITERATIVE_BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = v2182.BENCHMARK_TRANSPORT


def _get_rows(category, limit):
    return base.get_memories(limit, category=category)


def _save_row(text, category, importance):
    return base.save_memory(text, category=category, importance=importance)


TRAINER = IterativeSkillTrainer(
    SKILL_LAB,
    _get_rows,
    _save_row,
    now_fn=base.now_iso,
    max_rounds=6,
)


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


def _iterative_propose_candidate(self, skill_name):
    """Draft from active failures plus evaluated failed-candidate history."""
    active = self.engine.get_skill(skill_name)
    if not active:
        raise ValueError(f"Skill {skill_name!r} was not found.")

    feedback = TRAINER.feedback_bundle(active["skill_id"], max_attempts=6)
    attempts = feedback.get("failed_attempts") or []
    history_lines = []
    for index, attempt in enumerate(attempts[:4], 1):
        history_lines.append(
            "ATTEMPT %d score=%.1f pass=%.1f weaknesses=%s instructions=%s" % (
                index,
                float(attempt.get("average_score") or 0),
                float(attempt.get("pass_rate") or 0),
                " | ".join(attempt.get("weaknesses") or [])[:700],
                " || ".join(attempt.get("instructions") or [])[:900],
            )
        )

    prompt = "\n".join([
        "Create the next conservative Tyler AI skill candidate.",
        "Learn from BOTH the active weaknesses and failed candidate attempts below.",
        "Do not broaden tools or permissions. Do not repeat a failed profile.",
        "Preserve truthful reporting of writes, merges, deployments, and tool state.",
        "Return exactly three tagged lines; no JSON, Markdown, or commentary.",
        "INSTRUCTIONS=<up to 8 concise instructions separated by ||>",
        "CRITERIA=<up to 8 concise success criteria separated by ||>",
        "RATIONALE=<one concise sentence explaining what changed from failed attempts>",
        f"PURPOSE: {active.get('purpose') or ''}",
        "CURRENT INSTRUCTIONS: " + " || ".join(labmod._as_list(active.get("instructions"))),
        "CURRENT CRITERIA: " + " || ".join(labmod._as_list(active.get("success_criteria"))),
        "ALLOWED TOOLS (MUST NOT CHANGE): " + " | ".join(labmod._as_list(active.get("allowed_tools"))),
        "ACTIVE WEAKNESSES: " + " | ".join(feedback.get("active_weaknesses") or [])[:1200],
        "FAILED CANDIDATE HISTORY:",
        *(history_lines or ["none"]),
    ])
    raw = self.engine.complete([
        {
            "role": "system",
            "content": (
                "Improve Tyler AI skill profiles through conservative iteration. "
                "Use only the requested tagged text format and never add permissions."
            ),
        },
        {"role": "user", "content": prompt},
    ], tokens=ITERATIVE_CANDIDATE_OUTPUT_TOKENS, temperature=0, json_mode=False)

    parsed = v2182._parse_candidate_text(raw)
    instructions = _dedupe(parsed.get("instructions") or labmod._as_list(active.get("instructions")), 20)
    criteria = _dedupe(parsed.get("success_criteria") or labmod._as_list(active.get("success_criteria")), 20)
    if not instructions:
        raise RuntimeError("Candidate generation returned no usable instructions.")

    # Fail-safe against the model returning a byte-for-byte repeat of a prior
    # profile. Add a narrow benchmark-grounded instruction instead of wasting a
    # benchmark round on an already failed candidate.
    prior_signatures = {
        _profile_signature(item.get("instructions") or [], item.get("success_criteria") or [])
        for item in self.candidates(active["skill_id"], 100)
        if int(item.get("base_version") or -1) == int(active.get("version") or 0)
    }
    signature = _profile_signature(instructions, criteria)
    if signature in prior_signatures:
        newest_weaknesses = []
        if attempts:
            newest_weaknesses = attempts[0].get("weaknesses") or []
        focus = labmod._norm((newest_weaknesses or feedback.get("active_weaknesses") or [
            "benchmark failures"
        ])[0])
        instructions = _dedupe(
            instructions + [f"Explicitly correct the observed benchmark failure: {focus}"], 20
        )
        signature = _profile_signature(instructions, criteria)
        if signature in prior_signatures:
            raise RuntimeError("Candidate generator repeated an already evaluated profile.")

    created = self._now().isoformat()
    candidate_number = 1 + sum(
        1 for item in self.candidates(active["skill_id"], 100)
        if int(item.get("base_version") or -1) == int(active.get("version") or 0)
    )
    cid = "CND-" + labmod._hash([
        active["skill_id"], active.get("version"), instructions, criteria, candidate_number, created
    ])[:10].upper()
    parent = attempts[0].get("candidate_id") if attempts else None
    payload = {
        "kind": "skill_candidate",
        "candidate_id": cid,
        "skill_id": active["skill_id"],
        "name": active.get("name"),
        "purpose": active.get("purpose"),
        "base_version": int(active.get("version") or 1),
        "candidate_version": int(active.get("version") or 1) + 1,
        "iteration_attempt": candidate_number,
        "parent_candidate_id": parent,
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


# Manual "Improve skill" commands also gain failure-aware drafting in v2.19.
SKILL_LAB.propose_candidate = types.MethodType(_iterative_propose_candidate, SKILL_LAB)


def _norm(message):
    return re.sub(r"\s+", " ", str(message or "")).strip()


def _training_name(pattern, message):
    match = re.fullmatch(pattern, _norm(message), flags=re.I | re.S)
    return match.group(1).strip() if match else None


def _render_session(session, heading="Iterative skill training"):
    session = dict(session or {})
    return "\n".join([
        heading,
        f"Session: {session.get('session_id') or 'unknown'}",
        f"Skill: {session.get('skill_name') or session.get('skill_id') or 'unknown'}",
        f"Active version protected: v{session.get('active_version') or '?'}",
        f"Status: {str(session.get('status') or 'unknown').upper()}",
        f"Rounds completed: {session.get('rounds_completed') or 0}/{session.get('max_rounds') or TRAINER.max_rounds}",
        f"Baseline score: {session.get('baseline_average_score')}",
        f"Baseline pass rate: {session.get('baseline_pass_rate')}%",
        f"Prior failed attempts available: {session.get('prior_failed_attempts') or 0}",
        f"Best candidate score: {session.get('best_candidate_score') if session.get('best_candidate_score') is not None else 'none'}",
        "Automatic activation: disabled",
        "Human promotion approval: required",
    ])


def _render_round(result):
    session = result.get("session") or {}
    round_record = result.get("round") or {}
    candidate = result.get("candidate") or {}
    metrics = result.get("metrics") or {}
    lines = [
        "Iterative training round complete",
        f"Session: {session.get('session_id')}",
        f"Round: {round_record.get('round_number')}/{session.get('max_rounds')}",
        f"Skill: {session.get('skill_name') or session.get('skill_id')}",
        f"Active version remains: v{session.get('active_version')}",
        f"Candidate: {candidate.get('candidate_id')}",
        f"Candidate attempt: {candidate.get('iteration_attempt') or round_record.get('round_number')}",
        f"Learned from failed attempts: {candidate.get('learned_from_failed_attempts') or 0}",
        f"Baseline score: {metrics.get('active_average_score')}",
        f"Candidate score: {metrics.get('candidate_average_score')}",
        f"Baseline pass rate: {metrics.get('active_pass_rate')}%",
        f"Candidate pass rate: {metrics.get('candidate_pass_rate')}%",
        f"Candidate weaknesses: {metrics.get('candidate_weakness_count')}",
        f"Candidate not worse: {'yes' if metrics.get('candidate_not_worse') else 'no'}",
        f"Measurable improvement: {'yes' if metrics.get('measurable_improvement') else 'no'}",
        f"Minimum score met: {'yes' if metrics.get('minimum_score_met') else 'no'}",
        f"Quality gate passed: {'yes' if metrics.get('gate_passed') else 'no'}",
        f"Session status: {str(session.get('status') or '').upper()}",
        "Automatic activation: no",
    ]
    if metrics.get("gate_passed"):
        lines.extend([
            "",
            "The candidate passed the automated quality gate but is still NOT active.",
            f"Next: Prepare skill promotion {session.get('skill_id')}",
        ])
    elif session.get("status") == "exhausted":
        lines.extend([
            "",
            "Training stopped at the configured round limit. Active skill is unchanged.",
        ])
    else:
        lines.extend([
            "",
            "Candidate rejected; its failures are now training evidence for the next round.",
            f"Next: Continue iterative training {session.get('skill_id')}",
        ])
    return "\n".join(lines)


_PREVIOUS_HANDLE = base.handle_message


def handle_message_v219(message):
    text = _norm(message)
    lower = text.lower()

    if lower in {"show iterative training", "iterative training status", "show training loops"}:
        status = TRAINER.status()
        sessions = status.get("sessions") or []
        lines = [
            "Tyler Iterative Skill Training v2.19",
            f"Stored/current sessions: {len(sessions)}",
            f"Maximum rounds per session: {status.get('max_rounds')}",
            "One bounded candidate+benchmark round per command: yes",
            "Failed candidates become future training evidence: yes",
            "Active skill protected during training: yes",
            "Automatic activation: disabled",
            "Human promotion approval: required",
        ]
        if sessions:
            lines.append("")
            lines.append("Sessions:")
            for item in sessions[:8]:
                lines.append(
                    f"- {item.get('skill_name') or item.get('skill_id')} · {item.get('session_id')} · "
                    f"{str(item.get('status') or '').upper()} · {item.get('rounds_completed') or 0} rounds"
                )
        return base.base_payload(
            "iterative_skill_training_status", "\n".join(lines),
            used_tools=["skill_lab", "iterative_training"], success=True
        ) | {"iterative_training": status}, 200

    name = _training_name(r"show\s+iterative\s+training\s+(.+)", text)
    if name:
        session = TRAINER.latest_session(name)
        if not session:
            return base.base_payload(
                "iterative_skill_training_status",
                f"No iterative training session exists for {name}.",
                used_tools=["iterative_training"], success=False,
            ), 404
        return base.base_payload(
            "iterative_skill_training_status", _render_session(session),
            used_tools=["iterative_training"], success=True
        ) | {"iterative_training": session}, 200

    name = _training_name(r"(?:start|begin)\s+(?:iterative\s+)?(?:skill\s+)?training\s+(.+)", text)
    if name:
        try:
            session = TRAINER.start(name)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload(
                "iterative_skill_training", f"Iterative training was not started. Reason: {exc}",
                used_tools=["skill_lab", "iterative_training"], success=False,
            ), 409
        reply = _render_session(session, "Iterative skill training session ready") + (
            f"\n\nNext: Continue iterative training {session.get('skill_id')}"
        )
        return base.base_payload(
            "iterative_skill_training", reply,
            used_tools=["skill_lab", "iterative_training"], success=True
        ) | {"iterative_training": session}, 200

    name = _training_name(r"restart\s+(?:iterative\s+)?(?:skill\s+)?training\s+(.+)", text)
    if name:
        try:
            session = TRAINER.start(name, restart=True)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload(
                "iterative_skill_training", f"Iterative training was not restarted. Reason: {exc}",
                used_tools=["skill_lab", "iterative_training"], success=False,
            ), 409
        return base.base_payload(
            "iterative_skill_training",
            _render_session(session, "Fresh iterative skill training session ready") +
            f"\n\nNext: Continue iterative training {session.get('skill_id')}",
            used_tools=["skill_lab", "iterative_training"], success=True
        ) | {"iterative_training": session}, 200

    name = _training_name(
        r"(?:(?:continue|advance)\s+iterative\s+training|run\s+iterative\s+training\s+round)\s+(.+)",
        text,
    )
    if name:
        try:
            result = TRAINER.advance(name)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload(
                "iterative_skill_training_round",
                f"Iterative training round did not run. Reason: {exc}",
                used_tools=["skill_lab", "iterative_training", "reason"], success=False,
            ), 409
        return base.base_payload(
            "iterative_skill_training_round", _render_round(result),
            used_tools=["skill_lab", "iterative_training", "reason", "evaluate_skill"], success=True
        ) | {"iterative_training": result}, 200

    name = _training_name(r"cancel\s+iterative\s+training\s+(.+)", text)
    if name:
        try:
            session = TRAINER.cancel(name)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload(
                "iterative_skill_training", f"Training cancellation failed. Reason: {exc}",
                used_tools=["iterative_training"], success=False,
            ), 409
        return base.base_payload(
            "iterative_skill_training", _render_session(session, "Iterative skill training cancelled"),
            used_tools=["iterative_training"], success=True
        ) | {"iterative_training": session}, 200

    return _PREVIOUS_HANDLE(message)


base.handle_message = handle_message_v219


_PREVIOUS_STATUS = app.view_functions.get("status")


def status_v219():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    data["iterative_skill_training_enabled"] = True
    data["automatic_skill_activation_enabled"] = False
    data["iterative_training_round_output_budget"] = (
        ITERATIVE_BENCHMARK_OUTPUT_BUDGET + ITERATIVE_CANDIDATE_OUTPUT_TOKENS
    )
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "iterative_skill_training",
        "failed_candidate_learning",
        "persistent_training_sessions",
        "provider_aware_training_rounds",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v219


_ORIGINAL_SAFE_SOURCE_FILES = v2182._safe_source_files_v2182


def _safe_source_files_v219():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + [
        "skill_iteration.py",
        "app_v2_19.py",
    ]))


v2182.v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v219
EXECUTOR.safe_source_files_fn = _safe_source_files_v219


__all__ = [
    "app", "base", "ENGINE", "VERSION", "VERSION_SHORT", "EXECUTOR",
    "DRILL_EXECUTOR", "PLANNER", "OPS", "REVIEW_GATE", "PROMOTION",
    "MERGE_GATE", "SKILL_LAB", "TRAINER", "verify_production",
    "BENCHMARK_OUTPUT_BUDGET", "BENCHMARK_TRANSPORT",
    "ITERATIVE_BENCHMARK_OUTPUT_BUDGET", "ITERATIVE_CANDIDATE_OUTPUT_TOKENS",
    "_iterative_propose_candidate",
]
