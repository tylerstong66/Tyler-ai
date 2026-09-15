import json
import os
import re

import app_v2_9_3 as v293


# v2.9.4 replaces opaque model-generated totals with auditable deductions.
# The evaluator lists concrete point deductions; Tyler AI calculates the final
# score itself as 100 - deductions, then applies deterministic safety caps.
v293.base.VERSION = '2.9.4-auditable-skill-evaluator'
v293.base.VERSION_SHORT = 'v2.9.4'

MAX_DEDUCTION_PER_ITEM = 25
MAX_TOTAL_DEDUCTION = 100
ALLOWED_DIMENSIONS = {
    'factual_grounding',
    'task_relevance',
    'specificity_actionability',
    'safety_reversibility',
    'completeness',
}


def _norm(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [_norm(item) for item in value if _norm(item)]
    text = _norm(value)
    return [text] if text else []


def _parse_deductions(value):
    deductions = []
    if not isinstance(value, list):
        return deductions

    for item in value:
        if not isinstance(item, dict):
            continue
        dimension = _norm(item.get('dimension')).lower().replace(' ', '_')
        reason = _norm(item.get('reason'))
        try:
            points = int(round(float(item.get('points', 0))))
        except Exception:
            continue
        if dimension not in ALLOWED_DIMENSIONS or not reason or points <= 0:
            continue
        points = min(points, MAX_DEDUCTION_PER_ITEM)
        deductions.append({
            'dimension': dimension,
            'points': points,
            'reason': reason[:1200],
        })
    return deductions


def _score_from_deductions(deductions):
    total = min(
        MAX_TOTAL_DEDUCTION,
        sum(int(item.get('points') or 0) for item in deductions),
    )
    return max(0, 100 - total), total


def _weaknesses_from_deductions(deductions):
    return [
        f"{item['dimension']}: {item['reason']} (-{item['points']})"
        for item in deductions
    ]


def _evaluate_skill_v294(skill_name, test_input, expected='', criteria=None):
    skill = v293.v292.v291.ENGINE.get_skill(skill_name)
    if not skill:
        raise ValueError(f'Skill {skill_name!r} was not found.')

    output = v293.v292.v291.ENGINE.run_skill(skill['skill_id'], test_input)
    rubric = _list(criteria) or _list(skill.get('success_criteria'))
    examples = v293.v292._reference_examples(skill['skill_id'], 8)
    invariants = (
        v293.v292.TYLER_DEVELOPER_INVARIANTS
        if v293.v292._developer_skill(skill)
        else []
    )
    checks = v293.v292._architecture_checks(skill, test_input, output)

    evaluator_payload = {
        'skill': skill.get('name'),
        'purpose': skill.get('purpose'),
        'input': _norm(test_input),
        'candidate_output': str(output or ''),
        'expected_output_or_behavior': _norm(expected),
        'success_criteria': rubric,
        'authoritative_training_examples': examples,
        'authoritative_project_invariants': invariants,
        'deterministic_architecture_checks': checks,
        'evaluation_dimensions': {
            'factual_grounding': 'Accuracy relative to supplied authoritative facts and examples.',
            'task_relevance': 'Directly solves the user request without irrelevant requirements.',
            'specificity_actionability': 'Provides sufficiently concrete, usable steps for this request.',
            'safety_reversibility': 'Preserves working systems, avoids unsafe side effects, and supports rollback/testing.',
            'completeness': 'Covers the important parts of the request without requiring unrelated extras.',
        },
        'evaluation_rules': [
            'Start from 100 points. Return deductions only for concrete shortcomings in the candidate response.',
            'Every deduction MUST identify one allowed dimension, an integer point value from 1 to 25, and a specific reason grounded in the supplied references or user request.',
            'Do not deduct points for systems, dependencies, tables, code paths, or best practices that are not required by the supplied references or user request.',
            'Do not require discussion of unrelated components.',
            'Treat the supplied training examples and project invariants as authoritative.',
            'For side effects, never reward automatic retry when the real-world outcome may be unknown.',
            'If no concrete shortcoming exists, return an empty deductions array.',
            'Do NOT return a total score. Tyler AI calculates the score deterministically.',
            'Return JSON only with exactly these fields: deductions, strengths, improvement.',
        ],
    }

    raw = v293.v292.v291.ENGINE.complete(
        [
            {
                'role': 'system',
                'content': (
                    'You are a strict, grounded, auditable evaluator for Tyler AI skill training. '
                    'Do not invent requirements. Identify only evidence-based deductions. '
                    'Never provide a total score. Return JSON only.'
                ),
            },
            {
                'role': 'user',
                'content': json.dumps(evaluator_payload, ensure_ascii=False),
            },
        ],
        tokens=950,
        temperature=0,
        json_mode=True,
    )

    parsed = v293.v292.v291.base.parse_json_object(raw) or {}
    deductions = _parse_deductions(parsed.get('deductions'))
    score, deduction_total = _score_from_deductions(deductions)

    # Deterministic architecture/safety checks remain authoritative and can
    # cap the score even if the evaluator overlooks a critical contradiction.
    failed_checks = [name for name, passed in checks.items() if passed is False]
    deterministic_caps = []
    if 'avoids_invented_supabase_email_path' in failed_checks:
        deterministic_caps.append(('invented_supabase_email_path', 60))
    if 'avoids_unsafe_automatic_retry' in failed_checks:
        deterministic_caps.append(('unsafe_automatic_retry', 65))
    if 'mentions_actual_email_path' in failed_checks:
        deterministic_caps.append(('missing_actual_email_path', 78))
    if 'mentions_auth_configuration' in failed_checks:
        deterministic_caps.append(('missing_auth_configuration', 82))
    for _, cap in deterministic_caps:
        score = min(score, cap)

    weaknesses = _weaknesses_from_deductions(deductions)
    for name, cap in deterministic_caps:
        weaknesses.append(f'deterministic_check: {name} (score capped at {cap})')

    improvement = _norm(parsed.get('improvement'))
    if weaknesses and not improvement:
        improvement = 'Address the listed deductions and deterministic check failures.'
    if not weaknesses:
        improvement = ''

    passed = score >= 80 and not any(
        name in failed_checks
        for name in [
            'avoids_invented_supabase_email_path',
            'avoids_unsafe_automatic_retry',
        ]
    )

    record = {
        'kind': 'skill_score',
        'skill_id': skill['skill_id'],
        'skill_version': int(skill.get('version') or 1),
        'input': _norm(test_input)[:4000],
        'output': str(output or '')[:8000],
        'expected': _norm(expected)[:4000],
        'criteria': rubric[:20],
        'score': score,
        'passed': passed,
        'strengths': _list(parsed.get('strengths'))[:10],
        'weaknesses': weaknesses[:12],
        'improvement': improvement[:2000],
        'grounded_evaluation': True,
        'auditable_evaluation': True,
        'reference_example_count': len(examples),
        'architecture_checks': checks,
        'deductions': deductions,
        'deduction_total': deduction_total,
        'deterministic_caps': [
            {'reason': name, 'cap': cap}
            for name, cap in deterministic_caps
        ],
        'created_at': v293.v292.v291.base.now_iso(),
    }
    return v293.v292.v291.ENGINE._save('skill_score', record, importance=5)


v293.v292.v291.ENGINE.evaluate_skill = _evaluate_skill_v294

app = v293.app
base = v293.base
ENGINE = v293.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
