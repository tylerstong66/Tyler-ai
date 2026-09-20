"""Tyler AI v2.19.3.8: evidence-only iterative training diagnostics."""

import re

import app_v2_19_3_7 as v21937


v21937.base.VERSION = "2.19.3.8-grounded-training-diagnostics"
v21937.base.VERSION_SHORT = "v2.19.3.8"

base = v21937.base
app = v21937.app
ENGINE = v21937.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v21937.EXECUTOR
SKILL_LAB = v21937.v21936.v21935.v21933.SKILL_LAB
TRAINER = v21937.v21936.v21935.v21933.TRAINER


def _norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _short(value, limit=260):
    value = _norm(value)
    return value if len(value) <= limit else value[: max(0, limit - 1)].rstrip() + "…"


def _result_summary(result):
    if not result:
        return "No persisted result"
    score = float(result.get("score") or 0)
    score_text = str(int(score)) if score.is_integer() else str(round(score, 1))
    passed = "PASS" if result.get("passed") else "FAIL"
    weaknesses = [_short(x, 180) for x in result.get("weaknesses") or [] if _norm(x)]
    improvement = _short(result.get("improvement"), 220)
    parts = [f"{score_text}/100 · {passed}"]
    if weaknesses:
        parts.append("Weaknesses: " + "; ".join(weaknesses[:3]))
    if improvement:
        parts.append("Recorded improvement: " + improvement)
    return " · ".join(parts)


def _training_diagnostics(skill_name):
    active = ENGINE.get_skill(skill_name)
    if not active:
        raise ValueError(f"Skill {skill_name!r} was not found.")

    skill_id = active.get("skill_id")
    session = TRAINER.latest_session(skill_id)
    if not session:
        raise ValueError(f"No iterative training session exists for {skill_name}.")

    cases = SKILL_LAB.benchmark_cases(skill_id, 20)
    rounds = sorted(
        TRAINER.rounds(session.get("session_id"), 30),
        key=lambda item: int(item.get("round_number") or 0),
    )
    evaluations = SKILL_LAB.evaluations(skill_id, None, 500)
    runs_by_id = {
        str(item.get("run_id")): item
        for item in evaluations
        if item.get("run_id")
    }
    candidates = {}
    for item in SKILL_LAB.candidates(skill_id, 500):
        candidate_id = str(item.get("candidate_id") or "")
        if candidate_id and candidate_id not in candidates:
            candidates[candidate_id] = item

    outcomes = {}
    for item in SKILL_LAB._records("skill_mutation_outcome", 500):
        if _norm(item.get("skill_id")).lower() != _norm(skill_id).lower():
            continue
        candidate_id = str(item.get("candidate_id") or "")
        if candidate_id and candidate_id not in outcomes:
            outcomes[candidate_id] = item

    baseline = runs_by_id.get(str(session.get("baseline_evaluation_id")))
    if not baseline:
        baseline = next(
            (item for item in evaluations if item.get("target_kind") == "active"),
            None,
        )

    lines = [
        f"## Iterative training diagnostics — {active.get('name') or skill_id}",
        "Evidence mode: persisted records only",
        "Model calls used for this diagnostic: 0",
        "No new candidate, benchmark, promotion, or external action was executed.",
        "",
        "### Session",
        f"Session: {session.get('session_id') or 'unknown'}",
        f"Active version protected: v{session.get('active_version') or '?'}",
        f"Status: {str(session.get('status') or 'unknown').upper()}",
        f"Rounds completed: {session.get('rounds_completed') or 0}/{session.get('max_rounds') or '?'}",
        f"Baseline: {session.get('baseline_average_score')} · {session.get('baseline_pass_rate')}% pass rate",
        f"Verified champion: {session.get('champion_candidate_id') or 'active baseline'}",
        f"Champion: {session.get('champion_score')} · {session.get('champion_pass_rate')}% pass rate",
        "",
        f"### Saved benchmark suite ({len(cases)} cases)",
    ]

    for index, case in enumerate(cases, 1):
        lines.extend([
            f"{index}. {case.get('case_id') or 'unknown-case'}",
            "Input: " + _short(case.get("input"), 420),
            "Expected: " + _short(case.get("expected_behavior"), 420),
        ])

    lines.extend(["", "### Persisted per-case results"])
    baseline_results = {
        str(item.get("case_id")): item for item in (baseline or {}).get("case_results") or []
    }
    round_runs = []
    for record in rounds:
        run = runs_by_id.get(str(record.get("candidate_evaluation_id")))
        round_runs.append((record, run))

    for case in cases:
        case_id = str(case.get("case_id") or "unknown-case")
        lines.append(f"#### {case_id}")
        lines.append("Baseline: " + _result_summary(baseline_results.get(case_id)))
        for record, run in round_runs:
            results = {
                str(item.get("case_id")): item
                for item in (run or {}).get("case_results") or []
            }
            lines.append(
                f"Round {record.get('round_number')}: "
                + _result_summary(results.get(case_id))
            )

    lines.extend(["", "### Persisted mutation evidence"])
    if not rounds:
        lines.append("No saved training rounds were found for this session.")
    for record in rounds:
        candidate_id = str(record.get("candidate_id") or "")
        candidate = candidates.get(candidate_id) or {}
        outcome = outcomes.get(candidate_id) or {}
        diff = candidate.get("mutation_diff") or outcome.get("mutation_diff") or {}
        direction = outcome.get("direction") or candidate.get("mutation_key") or "not recorded"
        before = _short(diff.get("before"), 220) or "not recorded"
        after = _short(diff.get("after") or outcome.get("replacement"), 300) or "not recorded"
        weaknesses = [
            _short(x, 180) for x in record.get("weaknesses") or [] if _norm(x)
        ]
        lines.extend([
            f"#### Round {record.get('round_number')} — {candidate_id or 'unknown candidate'}",
            f"Score: {record.get('candidate_average_score')} · {record.get('candidate_pass_rate')}% pass rate",
            f"Mutation direction: {direction}",
            f"Before: {before}",
            f"After: {after}",
        ])
        if candidate.get("mutation_target_case_id") or outcome.get("target_case_id"):
            lines.append(
                "Target case: "
                + str(candidate.get("mutation_target_case_id") or outcome.get("target_case_id"))
            )
        if candidate.get("mutation_target_weakness") or outcome.get("target_weakness"):
            lines.append(
                "Target weakness: "
                + _short(candidate.get("mutation_target_weakness") or outcome.get("target_weakness"), 260)
            )
        if outcome:
            lines.extend([
                f"Recorded outcome: {outcome.get('outcome') or 'unknown'}",
                f"Score delta: {outcome.get('score_delta')} · Pass-rate delta: {outcome.get('pass_rate_delta')}",
                "Improved cases: " + (", ".join(outcome.get("improved_case_ids") or []) or "none recorded"),
                "Damaged cases: " + (", ".join(outcome.get("damaged_case_ids") or []) or "none recorded"),
            ])
        if weaknesses:
            lines.append("Recorded weaknesses: " + "; ".join(weaknesses[:5]))

    lowest = []
    for case in cases:
        case_id = str(case.get("case_id") or "")
        observed = []
        if baseline_results.get(case_id):
            observed.append(float(baseline_results[case_id].get("score") or 0))
        for _, run in round_runs:
            for item in (run or {}).get("case_results") or []:
                if str(item.get("case_id") or "") == case_id:
                    observed.append(float(item.get("score") or 0))
        if observed:
            lowest.append((min(observed), case_id))
    lowest.sort()

    lines.extend([
        "",
        "### Evidence-based next action",
        "Do not continue automatically. Review the lowest-scoring saved case and its exact recorded weakness, then constrain the next mutation to that requirement.",
    ])
    if lowest:
        lines.append("Lowest-scoring persisted cases: " + ", ".join(case_id for _, case_id in lowest[:3]))
    lines.append("This diagnostic does not infer missing causes. Missing evidence is labeled as not recorded.")

    return {
        "reply": "\n".join(lines),
        "session": session,
        "case_count": len(cases),
        "round_count": len(rounds),
        "model_calls": 0,
        "evidence_only": True,
    }


_PREVIOUS_HANDLE = base.handle_message


def handle_message_v21938(message):
    text = _norm(message)
    match = re.fullmatch(
        r"diagnose\s+(?:champion|iterative)\s+training\s+(.+)",
        text,
        flags=re.I | re.S,
    )
    if not match:
        return _PREVIOUS_HANDLE(message)
    skill_name = match.group(1).strip()
    try:
        report = _training_diagnostics(skill_name)
    except (ValueError, RuntimeError) as exc:
        return base.base_payload(
            "iterative_training_diagnostics",
            f"Training diagnostics could not be produced. Reason: {exc}",
            used_tools=["read_training_records"],
            success=False,
        ), 404
    return base.base_payload(
        "iterative_training_diagnostics",
        report["reply"],
        used_tools=["read_training_records", "skill_lab"],
        success=True,
    ) | {"training_diagnostics": report}, 200


base.handle_message = handle_message_v21938


_PREVIOUS_STATUS = app.view_functions["status"]


def status_v21938():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data["version"] = base.VERSION
    data["version_short"] = base.VERSION_SHORT
    capabilities = data.setdefault("capabilities", [])
    for item in [
        "grounded_iterative_training_diagnostics",
        "zero_model_call_training_diagnostics",
        "persisted_per_case_training_evidence",
    ]:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions["status"] = status_v21938


_ORIGINAL_SAFE_SOURCE_FILES = v21937._safe_source_files_v21937


def _safe_source_files_v21938():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_19_3_8.py"]))


EXECUTOR.safe_source_files_fn = _safe_source_files_v21938


__all__ = list(v21937.__all__) + [
    "_training_diagnostics",
    "handle_message_v21938",
    "_safe_source_files_v21938",
    "status_v21938",
]
