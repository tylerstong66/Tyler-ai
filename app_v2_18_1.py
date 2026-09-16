"""Tyler AI v2.18.1 — Skill Lab Groq output-budget hotfix.

v2.18.0 correctly created benchmark suites, but its per-case generation budget
could exceed low-tier Groq output-tokens-per-minute limits. This version keeps
the Skill Lab behavior and human promotion gate unchanged while allocating a
bounded output budget across the entire benchmark run.
"""

import json
import types

import app_v2_18 as v218
import skill_lab as labmod


v218.base.VERSION = "2.18.1-skill-lab-budget-hotfix"
v218.base.VERSION_SHORT = "v2.18.1"

base = v218.base
app = v218.app
ENGINE = v218.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v218.EXECUTOR
DRILL_EXECUTOR = v218.DRILL_EXECUTOR
PLANNER = v218.PLANNER
OPS = v218.OPS
REVIEW_GATE = v218.REVIEW_GATE
PROMOTION = v218.PROMOTION
MERGE_GATE = v218.MERGE_GATE
SKILL_LAB = v218.SKILL_LAB
verify_production = v218.verify_production

# Leave headroom below the observed 1,000 OTPM ceiling so provider accounting,
# rounding, or a short unrelated completion cannot make a benchmark fail.
BENCHMARK_OUTPUT_BUDGET = 850
BENCHMARK_MIN_RUN_TOKENS = 60
BENCHMARK_MIN_JUDGE_TOKENS = 45
BENCHMARK_MAX_RUN_TOKENS = 120
BENCHMARK_MAX_JUDGE_TOKENS = 70

_ORIGINAL_EVALUATE = SKILL_LAB.evaluate


def _allocate_benchmark_budget(case_count):
    """Return conservative per-case run/judge token caps.

    The allocation is deterministic and keeps the configured maximum requested
    output for a complete suite at or below BENCHMARK_OUTPUT_BUDGET whenever the
    suite has enough budget to satisfy the minimum caps. Developer bootstrap has
    five cases, which receives 100 run tokens + 70 judge tokens per case = 850.
    """
    count = max(1, int(case_count or 1))
    per_case = max(1, BENCHMARK_OUTPUT_BUDGET // count)

    judge = min(BENCHMARK_MAX_JUDGE_TOKENS, max(BENCHMARK_MIN_JUDGE_TOKENS, per_case * 2 // 5))
    run = min(BENCHMARK_MAX_RUN_TOKENS, max(BENCHMARK_MIN_RUN_TOKENS, per_case - judge))

    # If a very large custom suite cannot fit both minimums under the budget,
    # favor the judge just enough to preserve valid JSON and use the remainder
    # for a concise candidate answer.
    if (run + judge) * count > BENCHMARK_OUTPUT_BUDGET:
        judge = max(30, min(BENCHMARK_MAX_JUDGE_TOKENS, BENCHMARK_OUTPUT_BUDGET // count // 3))
        run = max(30, BENCHMARK_OUTPUT_BUDGET // count - judge)

    return int(run), int(judge)


def _budgeted_run(self, profile, request_text):
    tokens = int(getattr(self, "_benchmark_run_tokens", BENCHMARK_MAX_RUN_TOKENS))
    return self.engine.complete([
        {
            "role": "system",
            "content": (
                "You are Tyler AI running a benchmarked skill. Follow the profile. "
                "Never claim writes, merges, deployments, or side effects occurred unless verified. "
                "Answer concisely while preserving the required safety and technical reasoning.\n\n"
                + self._context(profile)
            ),
        },
        {"role": "user", "content": labmod._norm(request_text)},
    ], tokens=tokens, temperature=0.1, json_mode=False)


def _budgeted_judge(self, profile, case, output):
    tokens = int(getattr(self, "_benchmark_judge_tokens", BENCHMARK_MAX_JUDGE_TOKENS))
    rubric = {
        "skill": profile.get("name"),
        "test_input": case.get("input"),
        "expected_behavior": case.get("expected_behavior"),
        "criteria": case.get("criteria") or profile.get("success_criteria") or [],
        "candidate_output": str(output or ""),
        "instructions": (
            "Score 0-100. Return compact JSON only with score, passed, weaknesses. "
            "Use at most two short weakness strings."
        ),
    }
    raw = self.engine.complete([
        {"role": "system", "content": "You are a strict auditable evaluator. Return compact JSON only."},
        {"role": "user", "content": json.dumps(rubric, ensure_ascii=False)},
    ], tokens=tokens, temperature=0, json_mode=True)
    parsed = labmod._parse_json(raw)
    score = labmod._score(parsed.get("score"))
    return {
        "case_id": case.get("case_id"),
        "input": case.get("input"),
        "output": str(output or "")[:8000],
        "expected_behavior": case.get("expected_behavior"),
        "score": score,
        "passed": bool(parsed.get("passed")) if "passed" in parsed else score >= 80,
        "strengths": labmod._as_list(parsed.get("strengths"))[:10],
        "weaknesses": labmod._as_list(parsed.get("weaknesses"))[:10],
        "improvement": labmod._norm(parsed.get("improvement"))[:2000],
    }


def _budgeted_evaluate(self, skill_name, target_kind="active"):
    active = self.engine.get_skill(skill_name)
    if not active:
        raise ValueError(f"Skill {skill_name!r} was not found.")
    case_count = len(self.benchmark_cases(active["skill_id"], 20))
    run_tokens, judge_tokens = _allocate_benchmark_budget(case_count)
    self._benchmark_run_tokens = run_tokens
    self._benchmark_judge_tokens = judge_tokens
    try:
        return _ORIGINAL_EVALUATE(skill_name, target_kind)
    finally:
        self.__dict__.pop("_benchmark_run_tokens", None)
        self.__dict__.pop("_benchmark_judge_tokens", None)


SKILL_LAB._run = types.MethodType(_budgeted_run, SKILL_LAB)
SKILL_LAB._judge = types.MethodType(_budgeted_judge, SKILL_LAB)
SKILL_LAB.evaluate = types.MethodType(_budgeted_evaluate, SKILL_LAB)


# Keep maintenance source inventory aware of this hotfix layer.
_ORIGINAL_SAFE_SOURCE_FILES = v218._safe_source_files_v218


def _safe_source_files_v2181():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_18_1.py"]))


v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v2181
EXECUTOR.safe_source_files_fn = _safe_source_files_v2181


__all__ = [
    "app",
    "base",
    "ENGINE",
    "VERSION",
    "VERSION_SHORT",
    "EXECUTOR",
    "DRILL_EXECUTOR",
    "PLANNER",
    "OPS",
    "REVIEW_GATE",
    "PROMOTION",
    "MERGE_GATE",
    "SKILL_LAB",
    "verify_production",
    "BENCHMARK_OUTPUT_BUDGET",
    "_allocate_benchmark_budget",
]
