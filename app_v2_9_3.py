import json
import os
import re

import app_v2_9_2 as v292


# v2.9.3 fixes evaluator scale ambiguity. Some graders may return 10 to mean
# 10/10 even when the UI expects a 0-100 score. This layer requires score_100
# and safely normalizes explicit 10-point results.
v292.base.VERSION = '2.9.3-evaluator-score-normalization'
v292.base.VERSION_SHORT = 'v2.9.3'


def _norm(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [_norm(item) for item in value if _norm(item)]
    text = _norm(value)
    return [text] if text else []


def _truthy(value):
    if isinstance(value, bool):
        return value
    return str(value or '').strip().lower() in {'true', 'yes', 'pass', 'passed', '1'}


def _none_like_list(value):
    items = _list(value)
    if not items:
        return True
    none_like = {
        'none', 'none recorded', 'no weaknesses', 'no weakness',
        'n/a', 'na', 'not applicable',
    }
    return all(item.strip().lower().rstrip('.') in none_like for item in items)


def _none_like_text(value):
    text = _norm(value).lower().rstrip('.')
    if not text:
        return True
    return text in {
        'none', 'none needed', 'no improvement needed', 'no changes needed',
        'not needed', 'n/a', 'na',
    } or text.startswith('none needed')


def normalize_evaluator_score(parsed):
    """Return an integer 0-100 score plus normalization metadata."""
    parsed = parsed if isinstance(parsed, dict) else {}
    raw = parsed.get('score_100', parsed.get('score'))
    scale = parsed.get('score_scale')
    normalized_from = '0-100'

    if isinstance(raw, str):
        match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*', raw)
        if match:
            numerator = float(match.group(1))
            denominator = float(match.group(2))
            if denominator > 0:
                score = round((numerator / denominator) * 100)
                return max(0, min(100, int(score))), {
                    'raw_score': raw,
                    'normalized_from': f'explicit-{denominator:g}-point-scale',
                }

    try:
        score = float(raw)
    except Exception:
        return 0, {'raw_score': raw, 'normalized_from': 'invalid'}

    try:
        numeric_scale = float(scale)
    except Exception:
        numeric_scale = None

    if numeric_scale and numeric_scale > 0 and numeric_scale != 100:
        score = (score / numeric_scale) * 100
        normalized_from = f'declared-{numeric_scale:g}-point-scale'
    elif 0 <= score <= 10:
        # Only infer a hidden 10-point scale when the rest of the evaluator is
        # internally consistent with a passing/perfect judgment. This avoids
        # blindly turning a genuine 10/100 failure into 100/100.
        passed = _truthy(parsed.get('passed'))
        no_weaknesses = _none_like_list(parsed.get('weaknesses'))
        no_improvement = _none_like_text(parsed.get('improvement'))
        if passed and no_weaknesses and no_improvement:
            score *= 10
            normalized_from = 'inferred-10-point-scale'

    return max(0, min(100, int(round(score)))), {
        'raw_score': raw,
        'normalized_from': normalized_from,
    }


def _evaluate_skill_v293(skill_name, test_input, expected='', criteria=None):
    skill = v292.v291.ENGINE.get_skill(skill_name)
    if not skill:
        raise ValueError(f'Skill {skill_name!r} was not found.')

    output = v292.v291.ENGINE.run_skill(skill['skill_id'], test_input)
    rubric = _list(criteria) or _list(skill.get('success_criteria'))
    examples = v292._reference_examples(skill['skill_id'], 8)
    invariants = (
        v292.TYLER_DEVELOPER_INVARIANTS
        if v292._developer_skill(skill)
        else []
    )
    checks = v292._architecture_checks(skill, test_input, output)

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
        'evaluation_rules': [
            'Score only against the supplied skill purpose, criteria, training examples, project invariants, and the user test request.',
            'Do not invent additional systems, dependencies, tables, code paths, requirements, or best practices and then penalize the candidate for omitting them.',
            'Do not require discussion of components unrelated to the user test request.',
            'Treat authoritative project invariants as facts even if generic software advice would differ.',
            'For side effects, never reward advice to automatically retry when the real-world outcome may be unknown.',
            'If a deterministic architecture check is false, explain that specific failure. Do not fabricate a different failure.',
            'Return JSON only.',
            'score_100 MUST be an integer from 0 to 100 where 100 means fully satisfies the criteria and 0 means complete failure.',
            'score_scale MUST be 100.',
            'Return exactly these fields: score_100, score_scale, passed, strengths, weaknesses, improvement.',
        ],
    }

    raw = v292.v291.ENGINE.complete(
        [
            {
                'role': 'system',
                'content': (
                    'You are a strict but grounded evaluator for Tyler AI skill training. '
                    'The supplied training examples and project invariants are authoritative. '
                    'Never invent evaluation requirements. Use a 0-100 scoring scale only. '
                    'Return JSON only.'
                ),
            },
            {
                'role': 'user',
                'content': json.dumps(evaluator_payload, ensure_ascii=False),
            },
        ],
        tokens=850,
        temperature=0,
        json_mode=True,
    )

    parsed = v292.v291.base.parse_json_object(raw) or {}
    score, score_meta = normalize_evaluator_score(parsed)

    failed_checks = [name for name, passed in checks.items() if passed is False]
    if 'avoids_invented_supabase_email_path' in failed_checks:
        score = min(score, 60)
    if 'avoids_unsafe_automatic_retry' in failed_checks:
        score = min(score, 65)
    if 'mentions_actual_email_path' in failed_checks:
        score = min(score, 78)
    if 'mentions_auth_configuration' in failed_checks:
        score = min(score, 82)

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
        'weaknesses': _list(parsed.get('weaknesses'))[:10],
        'improvement': _norm(parsed.get('improvement'))[:2000],
        'grounded_evaluation': True,
        'reference_example_count': len(examples),
        'architecture_checks': checks,
        'evaluator_score_metadata': score_meta,
        'created_at': v292.v291.base.now_iso(),
    }
    return v292.v291.ENGINE._save('skill_score', record, importance=5)


v292.v291.ENGINE.evaluate_skill = _evaluate_skill_v293

app = v292.app
base = v292.base
ENGINE = v292.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
