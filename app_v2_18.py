"""Tyler AI v2.18 — Skill Lab with benchmarked, human-gated skill promotion.

v2.9 already introduced active purpose-specific skills, training examples, single
skill evaluations, and fine-tuning-ready exports. v2.18 adds the missing
controlled-improvement loop: separate candidate profiles, reusable benchmark
suites, side-by-side active/candidate scorecards, and a human approval gate
before a candidate can become the active skill version.
"""

import os
import re

import app_v2_17_2 as v2172
from skill_lab import SKILL_LAB_CATEGORIES, SkillPromotionLab


v2172.base.VERSION = '2.18.0-skill-lab'
v2172.base.VERSION_SHORT = 'v2.18.0'

base = v2172.base
app = v2172.app
ENGINE = v2172.ENGINE
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT
EXECUTOR = v2172.EXECUTOR
DRILL_EXECUTOR = v2172.DRILL_EXECUTOR
PLANNER = v2172.PLANNER
OPS = v2172.OPS
REVIEW_GATE = v2172.REVIEW_GATE
PROMOTION = v2172.PROMOTION
MERGE_GATE = v2172.MERGE_GATE
verify_production = v2172.verify_production

base.SPECIAL_MEMORY_CATEGORIES.update(SKILL_LAB_CATEGORIES)


def _get_rows(category, limit):
    return base.get_memories(limit, category=category)


def _save_row(text, category, importance):
    return base.save_memory(text, category=category, importance=importance)


SKILL_LAB = SkillPromotionLab(
    ENGINE,
    _get_rows,
    _save_row,
    sensitive_fn=base.sensitive,
    now_fn=base.now_iso,
    approval_ttl_minutes=int(os.environ.get('SKILL_PROMOTION_APPROVAL_TTL_MINUTES', '30')),
    minimum_candidate_score=int(os.environ.get('SKILL_PROMOTION_MIN_SCORE', '80')),
    minimum_improvement=float(os.environ.get('SKILL_PROMOTION_MIN_IMPROVEMENT', '1')),
)


_ORIGINAL_SAFE_SOURCE_FILES = v2172._safe_source_files_v2172


def _safe_source_files_v218():
    names = list(_ORIGINAL_SAFE_SOURCE_FILES())
    for name in ['skill_lab.py', 'app_v2_18.py']:
        if name not in names:
            names.append(name)
    return sorted(set(names))


v2172.v2171.v217.v216.v210.v297._safe_source_files = _safe_source_files_v218
EXECUTOR.safe_source_files_fn = _safe_source_files_v218


def _norm(message):
    return re.sub(r'\s+', ' ', str(message or '')).strip()


def _promotion_id(message):
    match = re.search(r'\b(SKP-[A-Fa-f0-9]{10})\b', str(message or ''), flags=re.I)
    return match.group(1).upper() if match else None


def _approval_code(message):
    match = re.search(r'\bcode\s+([A-Fa-f0-9]{6})\b', str(message or ''), flags=re.I)
    return match.group(1).upper() if match else None


def _render_benchmark(run, heading):
    run = dict(run or {})
    lines = [
        heading,
        f"Evaluation: {run.get('run_id') or 'unknown'}",
        f"Skill: {run.get('skill_name') or run.get('skill_id') or 'unknown'}",
        f"Target: {str(run.get('target_kind') or 'unknown').upper()} v{run.get('target_version') or '?'}",
        f"Cases: {run.get('case_count') or 0}",
        f"Average score: {run.get('average_score')}",
        f"Pass rate: {run.get('pass_rate')}%",
        f"Weakness count: {run.get('weakness_count')}",
        'Evaluator: strict rubric using the configured reasoning model',
    ]
    if run.get('candidate_id'):
        lines.insert(4, f"Candidate: {run.get('candidate_id')}")
    return '\n'.join(lines)


def _render_promotion(record, heading):
    record = dict(record or {})
    metrics = record.get('metrics') or {}
    return '\n'.join([
        f"{heading}: {str(record.get('status') or 'unknown').upper()}",
        f"Promotion: {record.get('promotion_id') or 'unknown'}",
        f"Skill: {record.get('skill_name') or record.get('skill_id') or 'unknown'}",
        f"Base version: {record.get('base_version') or 'unknown'}",
        f"Candidate version: {record.get('candidate_version') or 'unknown'}",
        f"Candidate: {record.get('candidate_id') or 'unknown'}",
        '',
        f"Active average score: {metrics.get('active_average_score', 'unknown')}",
        f"Candidate average score: {metrics.get('candidate_average_score', 'unknown')}",
        f"Active pass rate: {metrics.get('active_pass_rate', 'unknown')}%",
        f"Candidate pass rate: {metrics.get('candidate_pass_rate', 'unknown')}%",
        f"Candidate not worse: {'yes' if metrics.get('candidate_not_worse') else 'no'}",
        f"Measurable improvement: {'yes' if metrics.get('measurable_improvement') else 'no'}",
        f"Minimum score met: {'yes' if metrics.get('minimum_score_met') else 'no'}",
        f"Improvement gate passed: {'yes' if metrics.get('gate_passed') else 'no'}",
        '',
        'Automatic skill promotion: disabled',
        'Human approval required: yes',
    ])


def _skill_name_after(pattern, message):
    match = re.fullmatch(pattern, _norm(message), flags=re.I | re.S)
    return match.group(1).strip() if match else None


_PREVIOUS_HANDLE = base.handle_message


def handle_message_v218(message):
    text = _norm(message)
    lower = text.lower()

    if lower in {'show skill lab', 'skill lab status', 'show skill lab status'}:
        status = SKILL_LAB.status()
        lines = [
            'Tyler Skill Lab v2.18',
            f"Active skills: {status['skill_count']}",
            f"Open candidate versions: {status['candidate_count']}",
            f"Minimum candidate score: {status['minimum_candidate_score']}",
            f"Minimum measurable improvement: {status['minimum_improvement']}",
            'Reusable benchmark suites: enabled',
            'Active-vs-candidate comparison: enabled',
            'Human approval before activation: required',
            'Automatic skill promotion: disabled',
            'Model-weight fine-tuning: not enabled',
        ]
        if status['skills']:
            lines.append('')
            lines.append('Skills:')
            for item in status['skills']:
                candidate = (
                    f" · candidate v{item.get('candidate_version')} {item.get('candidate_id')}"
                    if item.get('candidate_id') else ''
                )
                lines.append(
                    f"- {item.get('name')} · active v{item.get('active_version')} · "
                    f"{item.get('benchmark_cases')} benchmark cases{candidate}"
                )
        return base.base_payload(
            'skill_lab_status', '\n'.join(lines), used_tools=['skill_lab'], success=True
        ) | {'skill_lab_status': status}, 200

    if lower in {'initialize developer skill', 'initialize tyler ai developer skill',
                 'bootstrap developer skill', 'create tyler ai developer skill'}:
        try:
            result = SKILL_LAB.bootstrap_developer_skill()
        except Exception as exc:
            return base.base_payload('skill_lab_bootstrap', f'Developer skill initialization failed: {exc}',
                                     used_tools=['skill_lab'], success=False), 500
        skill = result['skill']
        reply = '\n'.join([
            'Tyler AI Developer skill is ready.',
            f"Skill: {skill.get('name')}",
            f"Active version: {skill.get('version')}",
            f"Benchmark cases: {result.get('benchmark_cases')}",
            f"New skill created: {'yes' if result.get('created') else 'no — existing skill preserved'}",
            '',
            'Next command:',
            f"Benchmark skill {skill.get('skill_id')}",
        ])
        return base.base_payload('skill_lab_bootstrap', reply,
                                 used_tools=['skill_lab', 'save_skill_profile', 'save_benchmark_cases'],
                                 success=True) | {'skill_lab_result': result}, 200

    match = re.fullmatch(r'(?is)add\s+benchmark\s+case\s+(.+?)\s*::\s*(.+?)\s*=>\s*(.+)', text)
    if match:
        try:
            case = SKILL_LAB.add_benchmark_case(
                match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
            )
        except (ValueError, RuntimeError) as exc:
            return base.base_payload('skill_benchmark_case', str(exc), used_tools=['skill_lab'], success=False), 400
        return base.base_payload(
            'skill_benchmark_case',
            f"Benchmark case saved for {match.group(1).strip()}.\nCase: {case.get('case_id')}",
            used_tools=['skill_lab', 'save_benchmark_case'], success=True
        ) | {'skill_lab_result': case}, 200

    name = _skill_name_after(r'benchmark\s+skill\s+(.+)', text)
    if name:
        try:
            run = SKILL_LAB.evaluate(name, 'active')
        except (ValueError, RuntimeError) as exc:
            return base.base_payload('skill_benchmark', f'Benchmark could not run: {exc}',
                                     used_tools=['skill_lab', 'reason'], success=False), 409
        return base.base_payload(
            'skill_benchmark', _render_benchmark(run, 'Active skill benchmark complete'),
            used_tools=['skill_lab', 'reason', 'evaluate_skill', 'save_benchmark_run'], success=True
        ) | {'skill_lab_result': run}, 200

    name = _skill_name_after(r'(?:benchmark|evaluate)\s+candidate\s+skill\s+(.+)', text)
    if name:
        try:
            run = SKILL_LAB.evaluate(name, 'candidate')
        except (ValueError, RuntimeError) as exc:
            return base.base_payload('skill_candidate_benchmark', f'Candidate benchmark could not run: {exc}',
                                     used_tools=['skill_lab', 'reason'], success=False), 409
        return base.base_payload(
            'skill_candidate_benchmark', _render_benchmark(run, 'Candidate skill benchmark complete'),
            used_tools=['skill_lab', 'reason', 'evaluate_skill', 'save_benchmark_run'], success=True
        ) | {'skill_lab_result': run}, 200

    name = _skill_name_after(r'(?:train|improve)\s+skill\s+([^:=>]+)', text)
    if name and ':' not in text and '=>' not in text:
        try:
            candidate = SKILL_LAB.propose_candidate(name)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload('skill_candidate', f'Candidate training failed: {exc}',
                                     used_tools=['skill_lab', 'reason'], success=False), 409
        reply = '\n'.join([
            'Skill candidate created — not active.',
            f"Skill: {candidate.get('name')}",
            f"Candidate: {candidate.get('candidate_id')}",
            f"Base version: {candidate.get('base_version')}",
            f"Candidate version: {candidate.get('candidate_version')}",
            'Tool permissions broadened: no',
            'Automatic activation: no',
            '',
            f"Next: Benchmark candidate skill {candidate.get('skill_id')}",
        ])
        return base.base_payload('skill_candidate', reply,
                                 used_tools=['skill_lab', 'reason', 'save_skill_candidate'], success=True) | {
            'skill_lab_result': candidate
        }, 200

    name = _skill_name_after(r'prepare\s+skill\s+promotion\s+(.+)', text)
    if name:
        try:
            record = SKILL_LAB.prepare_promotion(name)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload('skill_promotion', f'Skill promotion was not prepared. Reason: {exc}',
                                     used_tools=['skill_lab'], success=False), 409
        reply = _render_promotion(record, 'Skill promotion prepared') + (
            f"\n\nNo active skill changed during preparation."
            f"\nApproval code: {record.get('approval_code')}"
            f"\n\nApprove with:"
            f"\nApprove skill promotion {record.get('promotion_id')} code {record.get('approval_code')}"
        )
        return base.base_payload('skill_promotion', reply,
                                 used_tools=['skill_lab', 'benchmark_gate'], success=True) | {
            'skill_promotion': record
        }, 200

    pid = _promotion_id(message)
    code = _approval_code(message)
    if re.search(r'\bapprove\s+(?:the\s+)?skill\s+promotion\b', lower):
        if not pid or not code:
            return base.base_payload('skill_promotion', 'Approval requires an SKP- identifier and six-character code.',
                                     used_tools=['skill_lab'], success=False), 400
        try:
            record = SKILL_LAB.approve_promotion(pid, code)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload('skill_promotion', f'Skill promotion was not approved. Reason: {exc}',
                                     used_tools=['skill_lab'], success=False), 409
        reply = _render_promotion(record, 'Skill promotion approval') + (
            f"\n\nApproval expires: {record.get('approval_expires_at')}"
            f"\nActive skill changed during approval: no"
            f"\n\nTo activate the approved candidate, send:"
            f"\nExecute approved skill promotion {record.get('promotion_id')}"
        )
        return base.base_payload('skill_promotion', reply,
                                 used_tools=['skill_lab'], success=True) | {'skill_promotion': record}, 200

    if re.search(r'\bexecute\s+(?:the\s+)?(?:approved\s+)?skill\s+promotion\b', lower):
        if not pid:
            return base.base_payload('skill_promotion', 'Execution requires an SKP- identifier.',
                                     used_tools=['skill_lab'], success=False), 400
        try:
            record = SKILL_LAB.execute_promotion(pid)
        except (ValueError, RuntimeError) as exc:
            return base.base_payload('skill_promotion', f'Skill promotion was not executed. Reason: {exc}',
                                     used_tools=['skill_lab'], success=False), 409
        reply = _render_promotion(record, 'Skill promotion') + (
            f"\n\nPROMOTED — active skill version is now v{record.get('activated_skill_version')}."
            '\nNo code merge or production deployment was performed by skill promotion.'
        )
        return base.base_payload('skill_promotion', reply,
                                 used_tools=['skill_lab', 'save_skill_profile'], success=True) | {
            'skill_promotion': record
        }, 200

    return _PREVIOUS_HANDLE(message)


base.handle_message = handle_message_v218


_PREVIOUS_STATUS = app.view_functions.get('status')


def status_v218():
    response = _PREVIOUS_STATUS()
    data = dict(response.get_json() or {})
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    data['skill_lab_enabled'] = True
    data['skill_candidate_promotion_human_gated'] = True
    data['automatic_skill_promotion_enabled'] = False
    capabilities = data.setdefault('capabilities', [])
    for item in ['skill_benchmark_suites', 'skill_candidate_versions',
                 'skill_active_candidate_comparison', 'human_gated_skill_promotion']:
        if item not in capabilities:
            capabilities.append(item)
    return base.jsonify(data)


app.view_functions['status'] = status_v218


if 'skill_lab_api' not in app.view_functions:
    @app.route('/skills/lab', methods=['GET'])
    def skill_lab_api():
        if not base.authorized():
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return base.jsonify({'success': True, 'version': base.VERSION, 'skill_lab': SKILL_LAB.status()})


__all__ = [
    'app', 'base', 'ENGINE', 'VERSION', 'VERSION_SHORT', 'EXECUTOR',
    'DRILL_EXECUTOR', 'PLANNER', 'OPS', 'REVIEW_GATE', 'PROMOTION',
    'MERGE_GATE', 'verify_production', 'SKILL_LAB', 'handle_message_v218',
]
