import json
import os
import re

import app as base
from skill_engine import SkillEngine, TRAINING_CATEGORIES


# v2.9 is intentionally layered over the proven v2.8.3.1 core so the
# reliability build remains easy to roll back while purpose training is tested.
base.VERSION = '2.9.0-skill-training'
base.VERSION_SHORT = 'v2.9.0'
base.SPECIAL_MEMORY_CATEGORIES.update(TRAINING_CATEGORIES)


def _get_training_rows(category, limit):
    return base.get_memories(limit, category=category)


def _save_training_row(text, category, importance):
    return base.save_memory(text, category=category, importance=importance)


ENGINE = SkillEngine(
    _get_training_rows,
    _save_training_row,
    base.groq,
    now_fn=base.now_iso,
)


def _skill_payload(payload_type, reply, success=True, used_tools=None, **extra):
    payload = base.base_payload(
        payload_type,
        reply,
        used_tools=used_tools or [],
        success=success,
    )
    payload.update(extra)
    return payload


def _log_skill_decision(message, payload, status_code):
    try:
        payload['decision_log_result'] = base.log_decision(
            message,
            payload,
            status_code,
        )
    except Exception as exc:
        payload['decision_log_result'] = {
            'logged': False,
            'error': str(exc)[:250],
        }
    return payload, status_code


def _safe_training_text(*values):
    return not any(base.sensitive(value) for value in values if value)


def _auto_profile(name, purpose):
    default_tools = ['read_memory', 'research_web', 'reason']
    request = {
        'skill_name': name,
        'purpose': purpose,
        'available_tools': default_tools,
        'instructions': (
            'Design a compact operating profile for this Tyler AI skill. '
            'Return JSON only with instructions, success_criteria, and allowed_tools. '
            'Use 3-7 practical instructions, 3-6 measurable success criteria, and only '
            'tools from available_tools.'
        ),
    }
    try:
        raw = base.groq(
            [
                {
                    'role': 'system',
                    'content': (
                        'You design reliable, testable AI skill profiles. '
                        'Return JSON only.'
                    ),
                },
                {
                    'role': 'user',
                    'content': json.dumps(request, ensure_ascii=False),
                },
            ],
            tokens=650,
            temperature=0,
            json_mode=True,
        )
        parsed = base.parse_json_object(raw) or {}
    except Exception:
        parsed = {}

    instructions = parsed.get('instructions') or [
        'Follow the stated purpose closely.',
        'Prefer accurate, practical answers over speculation.',
        'Use saved context and current research when they materially improve the result.',
    ]
    criteria = parsed.get('success_criteria') or [
        'The result directly addresses the request.',
        'Important factual claims are accurate or uncertainty is stated.',
        'The output is useful and actionable.',
    ]
    allowed = [
        tool
        for tool in (parsed.get('allowed_tools') or default_tools)
        if tool in default_tools
    ] or default_tools
    return instructions, criteria, allowed


def _create_skill(name, purpose):
    if not _safe_training_text(name, purpose):
        return _skill_payload(
            'skill_create',
            'I will not store credentials or other sensitive secrets as skill-training data.',
            success=False,
            used_tools=['skill_training'],
        ), 400

    instructions, criteria, allowed = _auto_profile(name, purpose)
    skill = ENGINE.create_or_update_skill(
        name,
        purpose,
        instructions=instructions,
        success_criteria=criteria,
        allowed_tools=allowed,
    )
    reply = (
        f"Skill created: {skill.get('name')}\n"
        f"Version: {skill.get('version')}\n"
        f"Purpose: {skill.get('purpose')}\n\n"
        'Next, teach it with examples using:\n'
        f"Train skill {skill.get('name')}: <input> => <ideal output>"
    )
    return _skill_payload(
        'skill_create',
        reply,
        used_tools=['design_skill_profile', 'save_skill_profile'],
        skill_result={'skill': skill},
    ), 200


def _train_skill(name, user_input, ideal_output):
    if not _safe_training_text(name, user_input, ideal_output):
        return _skill_payload(
            'skill_train',
            'I will not store credentials or other sensitive secrets as training examples.',
            success=False,
            used_tools=['skill_training'],
        ), 400

    try:
        example = ENGINE.add_example(name, user_input, ideal_output)
    except ValueError as exc:
        return _skill_payload(
            'skill_train',
            str(exc),
            success=False,
            used_tools=['skill_training'],
        ), 404

    summary = ENGINE.skill_summary(name) or {}
    reply = (
        f"Training example saved for {name}.\n"
        f"Examples: {summary.get('training_examples', 0)}\n\n"
        f"Input: {example.get('input')}\n"
        f"Ideal output: {example.get('ideal_output')}"
    )
    return _skill_payload(
        'skill_train',
        reply,
        used_tools=['save_training_example'],
        skill_result={
            'example': example,
            'summary': summary,
        },
    ), 200


def _use_skill(name, request_text):
    if not _safe_training_text(request_text):
        return _skill_payload(
            'skill_run',
            'That request appears to contain sensitive credentials or secrets, so I did not run it through stored skill context.',
            success=False,
            used_tools=['run_skill'],
        ), 400
    try:
        answer = ENGINE.run_skill(name, request_text)
    except ValueError as exc:
        return _skill_payload(
            'skill_run',
            str(exc),
            success=False,
            used_tools=['run_skill'],
        ), 404

    payload = _skill_payload(
        'skill_run',
        answer,
        used_tools=['read_skill_profile', 'read_training_examples', 'reason'],
        skill_result={'skill_name': name, 'mode': 'purpose-trained'},
    )
    payload['reasoning_calls'] = 1
    payload['total_groq_calls'] = 1
    return payload, 200


def _test_skill(name, request_text):
    if not _safe_training_text(request_text):
        return _skill_payload(
            'skill_test',
            'That test appears to contain sensitive credentials or secrets, so it was not stored or evaluated.',
            success=False,
            used_tools=['evaluate_skill'],
        ), 400
    try:
        score = ENGINE.evaluate_skill(name, request_text)
    except ValueError as exc:
        return _skill_payload(
            'skill_test',
            str(exc),
            success=False,
            used_tools=['evaluate_skill'],
        ), 404

    strengths = ', '.join(score.get('strengths') or []) or 'None recorded'
    weaknesses = ', '.join(score.get('weaknesses') or []) or 'None recorded'
    reply = (
        f"Skill test complete: {name}\n"
        f"Score: {score.get('score')}/100\n"
        f"Passed: {'yes' if score.get('passed') else 'no'}\n"
        f"Strengths: {strengths}\n"
        f"Weaknesses: {weaknesses}"
    )
    if score.get('improvement'):
        reply += '\nImprovement: ' + str(score.get('improvement'))

    payload = _skill_payload(
        'skill_test',
        reply,
        used_tools=['read_skill_profile', 'read_training_examples', 'reason', 'evaluate_skill', 'save_skill_score'],
        skill_result={'evaluation': score},
    )
    payload['reasoning_calls'] = 2
    payload['total_groq_calls'] = 2
    return payload, 200


def _show_skill(name):
    summary = ENGINE.skill_summary(name)
    if not summary:
        return _skill_payload(
            'skill_status',
            f"Skill {name!r} was not found.",
            success=False,
            used_tools=['read_skill_profile'],
        ), 404

    skill = summary['skill']
    average = summary.get('average_score')
    pass_rate = summary.get('pass_rate')
    reply = (
        f"Skill: {skill.get('name')}\n"
        f"Version: {skill.get('version')}\n"
        f"Purpose: {skill.get('purpose')}\n"
        f"Training examples: {summary.get('training_examples')}\n"
        f"Evaluations: {summary.get('evaluations')}\n"
        f"Average score: {average if average is not None else 'not tested yet'}\n"
        f"Pass rate: {str(pass_rate) + '%' if pass_rate is not None else 'not tested yet'}\n"
        'Model weight fine-tuning: not enabled'
    )
    return _skill_payload(
        'skill_status',
        reply,
        used_tools=['read_skill_profile', 'read_training_examples', 'read_skill_scores'],
        skill_result=summary,
    ), 200


def _list_skills():
    skills = ENGINE.list_skills()
    if not skills:
        return _skill_payload(
            'skill_list',
            'No purpose-trained skills have been created yet.',
            used_tools=['read_skill_profile'],
            skill_result={'skills': []},
        ), 200

    lines = ['Tyler AI skills:']
    output = []
    for skill in skills:
        summary = ENGINE.skill_summary(skill['skill_id']) or {}
        output.append(summary)
        score = summary.get('average_score')
        score_text = f'{score}/100' if score is not None else 'untested'
        lines.append(
            f"- {skill.get('name')} · v{skill.get('version')} · "
            f"{summary.get('training_examples', 0)} examples · {score_text}"
        )
    return _skill_payload(
        'skill_list',
        '\n'.join(lines),
        used_tools=['read_skill_profile', 'read_training_examples', 'read_skill_scores'],
        skill_result={'skills': output},
    ), 200


def _export_skill(name):
    try:
        exported = ENGINE.export_training_examples(name)
    except ValueError as exc:
        return _skill_payload(
            'skill_export',
            str(exc),
            success=False,
            used_tools=['export_training_data'],
        ), 404

    reply = (
        f"Prepared {len(exported)} training example(s) for {name}.\n"
        'The dataset is structured as system/user/assistant messages and is ready for a future fine-tuning pipeline. '
        'No model weights were changed.'
    )
    return _skill_payload(
        'skill_export',
        reply,
        used_tools=['export_training_data'],
        skill_result={
            'skill_name': name,
            'example_count': len(exported),
            'training_data': exported,
            'fine_tuned_model': False,
        },
    ), 200


def skill_command(message):
    text = base.norm(message)

    if re.fullmatch(r'(?i)(?:show|list)\s+(?:my\s+)?skills', text):
        return _list_skills()

    match = re.fullmatch(r'(?is)show\s+skill\s+(.+)', text)
    if match:
        return _show_skill(match.group(1).strip())

    match = re.fullmatch(r'(?is)create\s+skill\s+(.+?):\s*(.+)', text)
    if match:
        return _create_skill(match.group(1).strip(), match.group(2).strip())

    match = re.fullmatch(r'(?is)train\s+skill\s+(.+?):\s*(.+?)\s*=>\s*(.+)', text)
    if match:
        return _train_skill(
            match.group(1).strip(),
            match.group(2).strip(),
            match.group(3).strip(),
        )

    match = re.fullmatch(r'(?is)use\s+skill\s+(.+?):\s*(.+)', text)
    if match:
        return _use_skill(match.group(1).strip(), match.group(2).strip())

    match = re.fullmatch(r'(?is)test\s+skill\s+(.+?):\s*(.+)', text)
    if match:
        return _test_skill(match.group(1).strip(), match.group(2).strip())

    match = re.fullmatch(r'(?is)export\s+skill\s+(.+)', text)
    if match:
        return _export_skill(match.group(1).strip())

    return None


_original_handle_message = base.handle_message


def handle_message_v29(message):
    skill_result = skill_command(message)
    if skill_result is not None:
        payload, status_code = skill_result
        return _log_skill_decision(message, payload, status_code)
    return _original_handle_message(message)


base.handle_message = handle_message_v29


_original_core_project_text = base.core_project_text


def core_project_text_v29():
    original = _original_core_project_text()
    return (
        original
        + ' Purpose-training is implemented through versioned skill profiles, '
        'training examples, evaluation scorecards, and fine-tuning-ready exports. '
        'This is prompt/example training and evaluation; model weight fine-tuning is not enabled yet.'
    )


base.core_project_text = core_project_text_v29


_original_project_reply = base.project_reply


def project_reply_v29():
    return (
        _original_project_reply()
        + '\n\nTraining readiness:'
        + '\n- Versioned purpose-specific skill profiles'
        + '\n- Saved input → ideal-output training examples'
        + '\n- Automated skill evaluations and scorecards'
        + '\n- Fine-tuning-ready dataset export'
        + '\n- Model weight fine-tuning is still intentionally disabled'
    )


base.project_reply = project_reply_v29


_original_status = base.status


def status_v29():
    response = _original_status()
    data = response.get_json()
    data['version'] = base.VERSION
    data['version_short'] = base.VERSION_SHORT
    data['mode'] = 'persistent-multistep-autonomy-plus-skill-training'
    capabilities = data.setdefault('capabilities', [])
    for capability in [
        'purpose_specific_skills',
        'training_examples',
        'skill_evaluation_scorecards',
        'fine_tuning_dataset_export',
    ]:
        if capability not in capabilities:
            capabilities.append(capability)
    tools = data.setdefault('tools', [])
    for tool in [
        'create_skill',
        'train_skill',
        'run_skill',
        'evaluate_skill',
        'export_training_data',
    ]:
        if tool not in tools:
            tools.append(tool)
    data['skills_connected'] = bool(base.SUPABASE_URL and base.SUPABASE_KEY)
    data['model_fine_tuning_enabled'] = False
    return base.jsonify(data)


base.app.view_functions['status'] = status_v29


if 'skills_api' not in base.app.view_functions:
    @base.app.route('/skills', methods=['GET'])
    def skills_api():
        if not base.authorized():
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        try:
            skills = [ENGINE.skill_summary(item['skill_id']) for item in ENGINE.list_skills()]
            return base.jsonify({
                'success': True,
                'version': base.VERSION,
                'skills': skills,
            })
        except Exception as exc:
            return base.jsonify({
                'success': False,
                'version': base.VERSION,
                'error': str(exc),
            }), 500


if 'skill_export_api' not in base.app.view_functions:
    @base.app.route('/skills/<skill_id>/export', methods=['GET'])
    def skill_export_api(skill_id):
        if not base.authorized():
            return base.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        try:
            data = ENGINE.export_training_examples(skill_id)
            return base.jsonify({
                'success': True,
                'version': base.VERSION,
                'skill_id': skill_id,
                'count': len(data),
                'training_data': data,
                'fine_tuned_model': False,
            })
        except ValueError as exc:
            return base.jsonify({
                'success': False,
                'version': base.VERSION,
                'error': str(exc),
            }), 404
        except Exception as exc:
            return base.jsonify({
                'success': False,
                'version': base.VERSION,
                'error': str(exc),
            }), 500


app = base.app
VERSION = base.VERSION
VERSION_SHORT = base.VERSION_SHORT


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
    )
