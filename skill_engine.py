import json
import re
from datetime import datetime, timezone


SKILL_PROFILE_CATEGORY = 'skill_profile'
SKILL_EXAMPLE_CATEGORY = 'skill_example'
SKILL_EVAL_CATEGORY = 'skill_eval'
SKILL_SCORE_CATEGORY = 'skill_score'
TRAINING_CATEGORIES = {
    SKILL_PROFILE_CATEGORY,
    SKILL_EXAMPLE_CATEGORY,
    SKILL_EVAL_CATEGORY,
    SKILL_SCORE_CATEGORY,
}


def _norm(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _slug(value):
    value = _norm(value).lower()
    value = re.sub(r'[^a-z0-9]+', '-', value).strip('-')
    return value[:80]


def _list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [_norm(item) for item in value if _norm(item)]
    text = _norm(value)
    return [text] if text else []


def _parse_row(row):
    if not isinstance(row, dict):
        return None
    raw = row.get('memories', '')
    try:
        data = json.loads(str(raw or ''))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    data = dict(data)
    data['_row_id'] = row.get('id')
    data['_created_at'] = row.get('created_at')
    return data


def _parse_json_object(text):
    text = str(text or '').strip()
    if not text:
        return None
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.I).strip()
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except Exception:
        pass
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start >= 0 and end > start:
        try:
            data = json.loads(cleaned[start:end + 1])
            return data if isinstance(data, dict) else None
        except Exception:
            return None
    return None


class SkillEngine:
    """Purpose-training layer for Tyler AI.

    This layer does not fine-tune model weights. It stores versioned skill
    profiles, examples, and evaluations, then turns them into prompt context.
    The same examples can later be exported for a true fine-tuning pipeline.
    """

    def __init__(self, get_rows, save_row, complete, now_fn=None):
        self.get_rows = get_rows
        self.save_row = save_row
        self.complete = complete
        self.now_fn = now_fn or _now_iso

    def _records(self, category, limit=200):
        rows = self.get_rows(category, limit) or []
        output = []
        for row in rows:
            item = _parse_row(row)
            if item:
                output.append(item)
        return output

    def _save(self, category, payload, importance=4):
        text = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        rows = self.save_row(text, category, importance) or []
        row_id = rows[0].get('id') if rows and isinstance(rows[0], dict) else None
        result = dict(payload)
        result['_row_id'] = row_id
        return result

    def list_skills(self):
        latest = {}
        for item in self._records(SKILL_PROFILE_CATEGORY, 300):
            skill_id = _slug(item.get('skill_id') or item.get('name'))
            if not skill_id:
                continue
            version = int(item.get('version') or 1)
            current = latest.get(skill_id)
            if current is None or version > int(current.get('version') or 1):
                latest[skill_id] = item
        return sorted(latest.values(), key=lambda item: _norm(item.get('name')).lower())

    def get_skill(self, name_or_id):
        needle = _slug(name_or_id)
        if not needle:
            return None
        matches = []
        for item in self._records(SKILL_PROFILE_CATEGORY, 300):
            skill_id = _slug(item.get('skill_id') or item.get('name'))
            if skill_id == needle:
                matches.append(item)
        if not matches:
            return None
        return max(matches, key=lambda item: int(item.get('version') or 1))

    def create_or_update_skill(
        self,
        name,
        purpose,
        instructions=None,
        success_criteria=None,
        allowed_tools=None,
    ):
        name = _norm(name)
        purpose = _norm(purpose)
        if not name:
            raise ValueError('Skill name is required.')
        if not purpose:
            raise ValueError('Skill purpose is required.')

        skill_id = _slug(name)
        current = self.get_skill(skill_id)
        version = int(current.get('version') or 0) + 1 if current else 1
        created_at = current.get('created_at') if current else self.now_fn()

        payload = {
            'kind': 'skill_profile',
            'skill_id': skill_id,
            'name': name[:120],
            'purpose': purpose[:1200],
            'instructions': _list(instructions)[:20],
            'success_criteria': _list(success_criteria)[:20],
            'allowed_tools': _list(allowed_tools)[:20],
            'version': version,
            'status': 'active',
            'created_at': created_at,
            'updated_at': self.now_fn(),
        }
        return self._save(SKILL_PROFILE_CATEGORY, payload, importance=8)

    def add_example(self, skill_name, user_input, ideal_output, notes='', tags=None):
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f'Skill {skill_name!r} was not found.')

        user_input = _norm(user_input)
        ideal_output = _norm(ideal_output)
        if not user_input or not ideal_output:
            raise ValueError('Both training input and ideal output are required.')

        payload = {
            'kind': 'skill_example',
            'skill_id': skill['skill_id'],
            'skill_version': int(skill.get('version') or 1),
            'input': user_input[:4000],
            'ideal_output': ideal_output[:8000],
            'notes': _norm(notes)[:1200],
            'tags': _list(tags)[:20],
            'created_at': self.now_fn(),
        }
        return self._save(SKILL_EXAMPLE_CATEGORY, payload, importance=6)

    def examples_for_skill(self, skill_name, limit=12):
        skill = self.get_skill(skill_name)
        if not skill:
            return []
        skill_id = skill['skill_id']
        output = [
            item
            for item in self._records(SKILL_EXAMPLE_CATEGORY, max(100, limit * 8))
            if _slug(item.get('skill_id')) == skill_id
        ]
        return output[:max(0, min(int(limit), 500))]

    def evaluations_for_skill(self, skill_name, limit=30):
        skill = self.get_skill(skill_name)
        if not skill:
            return []
        skill_id = skill['skill_id']
        output = [
            item
            for item in self._records(SKILL_SCORE_CATEGORY, max(100, limit * 8))
            if _slug(item.get('skill_id')) == skill_id
        ]
        return output[:max(1, min(int(limit), 100))]

    def build_context(self, skill_name, example_limit=8, max_chars=7000):
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f'Skill {skill_name!r} was not found.')

        lines = [
            f"ACTIVE SKILL: {skill.get('name')}",
            f"PURPOSE: {skill.get('purpose')}",
        ]

        instructions = _list(skill.get('instructions'))
        if instructions:
            lines.append('INSTRUCTIONS:')
            lines.extend(f'- {item}' for item in instructions)

        criteria = _list(skill.get('success_criteria'))
        if criteria:
            lines.append('SUCCESS CRITERIA:')
            lines.extend(f'- {item}' for item in criteria)

        tools = _list(skill.get('allowed_tools'))
        if tools:
            lines.append('ALLOWED TOOLS: ' + ', '.join(tools))

        examples = (
            self.examples_for_skill(skill['skill_id'], example_limit)
            if int(example_limit) > 0
            else []
        )
        if examples:
            lines.append('TRAINING EXAMPLES:')
            for index, item in enumerate(examples, start=1):
                lines.append(f"Example {index} input: {item.get('input', '')}")
                lines.append(f"Example {index} ideal output: {item.get('ideal_output', '')}")

        return '\n'.join(lines)[:max_chars]

    def run_skill(self, skill_name, request_text):
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f'Skill {skill_name!r} was not found.')

        context = self.build_context(skill['skill_id'])
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are Tyler AI running a purpose-trained skill. '
                    'Follow the active skill profile and examples. '
                    'Do not claim tools or side effects were used unless the caller actually used them.\n\n'
                    + context
                ),
            },
            {'role': 'user', 'content': _norm(request_text)},
        ]
        return self.complete(messages, tokens=1400, temperature=0.15, json_mode=False)

    def evaluate_skill(self, skill_name, test_input, expected='', criteria=None):
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f'Skill {skill_name!r} was not found.')

        output = self.run_skill(skill['skill_id'], test_input)
        rubric = _list(criteria) or _list(skill.get('success_criteria'))
        evaluator_payload = {
            'skill': skill.get('name'),
            'purpose': skill.get('purpose'),
            'input': _norm(test_input),
            'candidate_output': str(output or ''),
            'expected_output_or_behavior': _norm(expected),
            'criteria': rubric,
            'instructions': (
                'Score the candidate from 0 to 100. '
                'Return JSON only with score, passed, strengths, weaknesses, and improvement.'
            ),
        }
        raw = self.complete(
            [
                {
                    'role': 'system',
                    'content': 'You are a strict evaluator for Tyler AI skill training. Return JSON only.',
                },
                {
                    'role': 'user',
                    'content': json.dumps(evaluator_payload, ensure_ascii=False),
                },
            ],
            tokens=700,
            temperature=0,
            json_mode=True,
        )
        parsed = _parse_json_object(raw) or {}
        try:
            score = int(parsed.get('score'))
        except Exception:
            score = 0
        score = max(0, min(100, score))
        passed = bool(parsed.get('passed')) if 'passed' in parsed else score >= 80

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
            'created_at': self.now_fn(),
        }
        saved = self._save(SKILL_SCORE_CATEGORY, record, importance=5)
        return saved

    def skill_summary(self, skill_name):
        skill = self.get_skill(skill_name)
        if not skill:
            return None
        examples = self.examples_for_skill(skill['skill_id'], 100)
        scores = self.evaluations_for_skill(skill['skill_id'], 100)
        numeric = [int(item.get('score') or 0) for item in scores]
        average = round(sum(numeric) / len(numeric), 1) if numeric else None
        pass_rate = (
            round(100 * sum(1 for item in scores if item.get('passed')) / len(scores), 1)
            if scores else None
        )
        return {
            'skill': skill,
            'training_examples': len(examples),
            'evaluations': len(scores),
            'average_score': average,
            'pass_rate': pass_rate,
            'fine_tuned_model': False,
            'training_mode': 'prompt_examples_and_evaluation',
        }

    def export_training_examples(self, skill_name, limit=500):
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f'Skill {skill_name!r} was not found.')
        system = self.build_context(skill['skill_id'], example_limit=0, max_chars=5000)
        rows = self.examples_for_skill(skill['skill_id'], max(1, min(int(limit), 500)))
        return [
            {
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': item.get('input', '')},
                    {'role': 'assistant', 'content': item.get('ideal_output', '')},
                ]
            }
            for item in rows
        ]
