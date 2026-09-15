import json
import os
import re

import app_v2_9_1 as v291


# v2.9.2 keeps v2.9.1's text-only fallback and grounds skill evaluation in
# actual training examples plus project invariants. The grader is not allowed
# to invent requirements that are absent from those references.
v291.base.VERSION = '2.9.2-grounded-skill-evaluator'
v291.base.VERSION_SHORT = 'v2.9.2'

TYLER_DEVELOPER_INVARIANTS = [
    'Tyler AI is Tyler Stong\'s personal autonomous AI assistant project, not Tyler Technologies.',
    'The application is Python/Flask deployed on Render and source-controlled in GitHub.',
    'Groq provides model reasoning; Supabase stores persistent memory, decision logs, feedback, and task state.',
    'Tavily provides live web research.',
    'Email is sent by send_email_via_n8n() through an authenticated n8n webhook, then n8n performs the Gmail action.',
    'The email path requires N8N_WEBHOOK_URL, N8N_WEBHOOK_KEY, N8N_AUTH_HEADER, and TYLER_DEFAULT_EMAIL.',
    'A confirmed email result requires success=true, sent=true, and a non-empty Gmail message_id.',
    'Supabase is not the email transport and there is no known Supabase email table in the Tyler AI architecture.',
    'A side-effect action such as email must not be retried automatically when dispatch outcome may be unknown; verify the real outcome first.',
    'Changes should preserve working behavior, be testable and reversible, and should not be claimed live until deployment is verified.',
]


def _norm(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [_norm(item) for item in value if _norm(item)]
    text = _norm(value)
    return [text] if text else []


def _developer_skill(skill):
    return str(skill.get('skill_id') or '').strip().lower() == 'tyler-ai-developer'


def _reference_examples(skill_name, limit=8):
    examples = v291.ENGINE.examples_for_skill(skill_name, limit)
    return [
        {
            'input': _norm(item.get('input')),
            'ideal_output': _norm(item.get('ideal_output')),
        }
        for item in examples
        if _norm(item.get('input')) and _norm(item.get('ideal_output'))
    ]


def _architecture_checks(skill, test_input, output):
    if not _developer_skill(skill):
        return {}

    combined = (_norm(test_input) + ' ' + _norm(output)).lower()
    if not any(term in combined for term in ['email', 'n8n', 'unauthorized', 'webhook', 'gmail']):
        return {}

    output_lower = _norm(output).lower()
    checks = {
        'mentions_actual_email_path': (
            'send_email_via_n8n' in output_lower
            or ('n8n' in output_lower and 'email' in output_lower)
        ),
        'mentions_auth_configuration': (
            'n8n_webhook_key' in output_lower
            or 'n8n_auth_header' in output_lower
            or ('header' in output_lower and 'key' in output_lower)
        ),
        'avoids_invented_supabase_email_path': not (
            'supabase email table' in output_lower
            or 'supabase email' in output_lower
            or 'send email through supabase' in output_lower
        ),
        'avoids_unsafe_automatic_retry': not (
            ('retry' in output_lower or 'retries' in output_lower)
            and not any(
                phrase in output_lower
                for phrase in [
                    'do not retry',
                    "don't retry",
                    'not retry',
                    'before retry',
                    'before retrying',
                    'verify before retry',
                    'check before retry',
                    'outcome is unknown',
                    'outcome may be unknown',
                ]
            )
        ),
    }
    return checks


def _grounded_evaluate_skill(skill_name, test_input, expected='', criteria=None):
    skill = v291.ENGINE.get_skill(skill_name)
    if not skill:
        raise ValueError(f'Skill {skill_name!r} was not found.')

    output = v291.ENGINE.run_skill(skill['skill_id'], test_input)
    rubric = _list(criteria) or _list(skill.get('success_criteria'))
    examples = _reference_examples(skill['skill_id'], 8)
    invariants = TYLER_DEVELOPER_INVARIANTS if _developer_skill(skill) else []
    checks = _architecture_checks(skill, test_input, output)

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
            'Return JSON only with score, passed, strengths, weaknesses, and improvement.',
        ],
    }

    raw = v291.ENGINE.complete(
        [
            {
                'role': 'system',
                'content': (
                    'You are a strict but grounded evaluator for Tyler AI skill training. '
                    'The supplied training examples and project invariants are authoritative. '
                    'Never invent evaluation requirements. Return JSON only.'
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

    parsed = v291.base.parse_json_object(raw) or {}
    try:
        score = int(parsed.get('score'))
    except Exception:
        score = 0
    score = max(0, min(100, score))

    # Deterministic safety/architecture caps make the score robust even if the
    # evaluator model overlooks a critical contradiction.
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
        'created_at': v291.base.now_iso(),
    }
    return v291.ENGINE._save('skill_score', record, importance=5)


# Patch the live skill engine instance. All v2.9.1 tool-call fallback behavior
# remains active because run_skill() and complete() still come from v2.9.1.
v291.ENGINE.evaluate_skill = _grounded_evaluate_skill


app = v291.app
base = v291.base
ENGINE = v291.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
