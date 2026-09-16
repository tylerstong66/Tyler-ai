"""Tyler AI v2.18.2 — provider-safe Skill Lab structured-output hotfix.

v2.18.1 bounded benchmark output below the configured Groq OTPM ceiling, but
benchmark judges still relied on provider-enforced ``response_format=json_object``.
Some reasoning models can return Groq ``failed_generation`` before Tyler receives
content when that transport cannot be satisfied. This layer removes provider JSON
mode from Skill Lab judging and candidate drafting, uses compact tagged text, and
parses it locally. Skill scoring thresholds and human promotion gates are unchanged.
"""

import re
import types

import app_v2_18_1 as v2181
import skill_lab as labmod


v2181.base.VERSION = "2.18.2-skill-lab-provider-safe-transport"
v2181.base.VERSION_SHORT = "v2.18.2"

base = v2181.base
app = v2181.app
ENGINE = v2181.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v2181.EXECUTOR
DRILL_EXECUTOR = v2181.DRILL_EXECUTOR
PLANNER = v2181.PLANNER
OPS = v2181.OPS
REVIEW_GATE = v2181.REVIEW_GATE
PROMOTION = v2181.PROMOTION
MERGE_GATE = v2181.MERGE_GATE
SKILL_LAB = v2181.SKILL_LAB
verify_production = v2181.verify_production

BENCHMARK_OUTPUT_BUDGET = v2181.BENCHMARK_OUTPUT_BUDGET
BENCHMARK_TRANSPORT = "plain_tagged_v1"
CANDIDATE_OUTPUT_TOKENS = 320


def _parse_tagged_judge(text):
    """Parse compact judge output without requiring provider JSON mode.

    Accepted form is intentionally forgiving, e.g.::

        SCORE=91
        WEAKNESSES=missing rollback detail || none

    Missing/unparseable scores fail closed at zero instead of crashing the run.
    Pass/fail is deterministic from the existing 80-point benchmark threshold.
    """
    raw = str(text or "")
    match = re.search(r"(?im)\bSCORE\s*[:=]\s*(-?\d+(?:\.\d+)?)", raw)
    score = labmod._score(match.group(1)) if match else 0

    weak_match = re.search(r"(?im)^\s*WEAKNESSES?\s*[:=]\s*(.+?)\s*$", raw)
    weakness_text = weak_match.group(1).strip() if weak_match else ""
    if weakness_text.lower() in {"", "none", "n/a", "na", "no weaknesses"}:
        weaknesses = []
    else:
        weaknesses = [
            labmod._norm(item)
            for item in re.split(r"\s*\|\|\s*|\s*;\s*", weakness_text)
            if labmod._norm(item)
        ][:2]

    if not match:
        weaknesses = ["evaluator_format_unparseable"] + weaknesses
        weaknesses = weaknesses[:2]

    return {
        "score": score,
        "passed": score >= 80,
        "weaknesses": weaknesses,
    }


def _provider_safe_judge(self, profile, case, output):
    tokens = int(getattr(self, "_benchmark_judge_tokens", v2181.BENCHMARK_MAX_JUDGE_TOKENS))
    criteria = case.get("criteria") or profile.get("success_criteria") or []
    prompt = "\n".join([
        "Evaluate the candidate answer against the expected behavior and criteria.",
        "Return exactly two compact lines. Do not use JSON, Markdown, or commentary.",
        "SCORE=<integer 0-100>",
        "WEAKNESSES=<none OR up to two short items separated by ||>",
        f"EXPECTED: {case.get('expected_behavior') or ''}",
        "CRITERIA: " + " | ".join(str(x) for x in criteria),
        f"CANDIDATE: {str(output or '')}",
    ])
    raw = self.engine.complete([
        {
            "role": "system",
            "content": (
                "You are a strict auditable evaluator. Score only the supplied answer. "
                "Use the requested tagged text format exactly."
            ),
        },
        {"role": "user", "content": prompt},
    ], tokens=tokens, temperature=0, json_mode=False)
    parsed = _parse_tagged_judge(raw)
    return {
        "case_id": case.get("case_id"),
        "input": case.get("input"),
        "output": str(output or "")[:8000],
        "expected_behavior": case.get("expected_behavior"),
        "score": parsed["score"],
        "passed": parsed["passed"],
        "strengths": [],
        "weaknesses": parsed["weaknesses"],
        "improvement": parsed["weaknesses"][0] if parsed["weaknesses"] else "",
    }


def _parse_candidate_text(text):
    """Parse compact candidate-profile text into conservative list fields."""
    raw = str(text or "").replace("\r\n", "\n")

    def line_value(tag):
        match = re.search(rf"(?im)^\s*{tag}\s*[:=]\s*(.+?)\s*$", raw)
        return match.group(1).strip() if match else ""

    instructions_raw = line_value("INSTRUCTIONS")
    criteria_raw = line_value("CRITERIA|SUCCESS_CRITERIA|SUCCESS CRITERIA")
    rationale = line_value("RATIONALE")

    def split_items(value):
        return [
            labmod._norm(item)
            for item in re.split(r"\s*\|\|\s*", value)
            if labmod._norm(item)
        ]

    return {
        "instructions": split_items(instructions_raw)[:20],
        "success_criteria": split_items(criteria_raw)[:20],
        "rationale": labmod._norm(rationale)[:2500],
    }


def _provider_safe_propose_candidate(self, skill_name):
    active = self.engine.get_skill(skill_name)
    if not active:
        raise ValueError(f"Skill {skill_name!r} was not found.")

    weaknesses = []
    for run in self.evaluations(active["skill_id"], "active", 5):
        for case in run.get("case_results") or []:
            weaknesses.extend(labmod._as_list(case.get("weaknesses")))

    prompt = "\n".join([
        "Conservatively improve this Tyler AI skill profile.",
        "Do not broaden tools or permissions. Preserve truthful state reporting.",
        "Return exactly three tagged lines; do not use JSON or Markdown.",
        "INSTRUCTIONS=<up to 8 concise instructions separated by ||>",
        "CRITERIA=<up to 8 concise success criteria separated by ||>",
        "RATIONALE=<one concise sentence>",
        f"PURPOSE: {active.get('purpose') or ''}",
        "CURRENT INSTRUCTIONS: " + " || ".join(labmod._as_list(active.get("instructions"))),
        "CURRENT CRITERIA: " + " || ".join(labmod._as_list(active.get("success_criteria"))),
        "ALLOWED TOOLS (MUST NOT CHANGE): " + " | ".join(labmod._as_list(active.get("allowed_tools"))),
        "OBSERVED WEAKNESSES: " + " | ".join(weaknesses[:20]),
    ])
    raw = self.engine.complete([
        {
            "role": "system",
            "content": (
                "Improve Tyler AI skill profiles conservatively. Use only the requested "
                "tagged text format; never add permissions or tools."
            ),
        },
        {"role": "user", "content": prompt},
    ], tokens=CANDIDATE_OUTPUT_TOKENS, temperature=0, json_mode=False)

    parsed = _parse_candidate_text(raw)
    instructions = parsed["instructions"] or labmod._as_list(active.get("instructions"))
    criteria = parsed["success_criteria"] or labmod._as_list(active.get("success_criteria"))
    if not instructions:
        raise RuntimeError("Candidate generation returned no usable instructions.")

    created = self._now().isoformat()
    version = int(active.get("version") or 1) + 1
    cid = "CND-" + labmod._hash([
        active["skill_id"], active.get("version"), instructions, criteria, created
    ])[:10].upper()
    payload = {
        "kind": "skill_candidate",
        "candidate_id": cid,
        "skill_id": active["skill_id"],
        "name": active.get("name"),
        "purpose": active.get("purpose"),
        "base_version": int(active.get("version") or 1),
        "candidate_version": version,
        "instructions": instructions[:20],
        "success_criteria": criteria[:20],
        "allowed_tools": labmod._as_list(active.get("allowed_tools"))[:20],
        "rationale": parsed["rationale"],
        "status": "candidate",
        "created_at": created,
    }
    return self._save(labmod.SKILL_CANDIDATE_CATEGORY, payload, 8)


# Replace only Skill Lab's model-output transports. v2.18.1's suite-wide output
# budget, evaluation storage, comparison math, approval expiry, and promotion gate
# remain intact.
SKILL_LAB._judge = types.MethodType(_provider_safe_judge, SKILL_LAB)
SKILL_LAB.propose_candidate = types.MethodType(_provider_safe_propose_candidate, SKILL_LAB)


_ORIGINAL_SAFE_SOURCE_FILES = v2181._safe_source_files_v2181


def _safe_source_files_v2182():
    return sorted(set(list(_ORIGINAL_SAFE_SOURCE_FILES()) + ["app_v2_18_2.py"]))


v2181.v218.v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v2182
EXECUTOR.safe_source_files_fn = _safe_source_files_v2182


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
    "BENCHMARK_TRANSPORT",
    "CANDIDATE_OUTPUT_TOKENS",
    "_parse_tagged_judge",
    "_provider_safe_judge",
    "_parse_candidate_text",
    "_provider_safe_propose_candidate",
]
