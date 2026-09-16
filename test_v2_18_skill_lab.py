import json
import re
import unittest

from skill_lab import (
    SKILL_BENCHMARK_RUN_CATEGORY,
    SKILL_CANDIDATE_CATEGORY,
    SKILL_PROMOTION_CATEGORY,
    SkillPromotionLab,
)


class MemoryStore:
    def __init__(self):
        self.rows = []
        self.next_id = 1

    def get_rows(self, category, limit):
        rows = [x for x in reversed(self.rows) if x['category'] == category]
        return rows[:limit]

    def save_row(self, text, category, importance):
        row = {
            'id': self.next_id,
            'created_at': f'2026-09-16T20:00:{self.next_id:02d}+00:00',
            'memories': text,
            'category': category,
            'importance': importance,
        }
        self.next_id += 1
        self.rows.append(row)
        return [row]


class FakeEngine:
    def __init__(self):
        self.skills = {}
        self.calls = []
        self.active_score = 82
        self.candidate_score = 91
        self.active_weaknesses = ['needs stronger verification']
        self.candidate_weaknesses = []

    @staticmethod
    def slug(value):
        return re.sub(r'[^a-z0-9]+', '-', str(value or '').lower()).strip('-')

    def get_skill(self, name):
        return self.skills.get(self.slug(name))

    def list_skills(self):
        return list(self.skills.values())

    def create_or_update_skill(self, name, purpose, instructions=None,
                               success_criteria=None, allowed_tools=None):
        sid = self.slug(name)
        current = self.skills.get(sid)
        version = int((current or {}).get('version') or 0) + 1
        profile = {
            'skill_id': sid,
            'name': name,
            'purpose': purpose,
            'instructions': list(instructions or []),
            'success_criteria': list(success_criteria or []),
            'allowed_tools': list(allowed_tools or []),
            'version': version,
            'status': 'active',
        }
        self.skills[sid] = profile
        return profile

    def examples_for_skill(self, skill_name, limit=8):
        return []

    def complete(self, messages, tokens=700, temperature=0.2, json_mode=False):
        self.calls.append((messages, json_mode))
        system = messages[0]['content']
        if json_mode and 'Improve Tyler AI skill profiles' in system:
            return json.dumps({
                'instructions': [
                    'Inspect current code before editing.',
                    'Verify deployment state before claiming live.',
                ],
                'success_criteria': ['Grounded', 'Verified'],
                'rationale': 'Adds explicit verification discipline.',
            })
        if json_mode and 'strict auditable evaluator' in system:
            payload = json.loads(messages[1]['content'])
            candidate = 'PROFILE VERSION: 2' in payload['candidate_output']
            score = self.candidate_score if candidate else self.active_score
            weaknesses = self.candidate_weaknesses if candidate else self.active_weaknesses
            return json.dumps({
                'score': score,
                'passed': score >= 80,
                'strengths': ['grounded'],
                'weaknesses': weaknesses,
                'improvement': 'Keep verification explicit.',
            })
        if not json_mode:
            return system + '\nANSWER'
        return '{}'


class SkillLabTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.engine = FakeEngine()
        self.clock = 0

        def now_fn():
            self.clock += 1
            return f'2026-09-16T20:{self.clock:02d}:00+00:00'

        self.lab = SkillPromotionLab(
            self.engine,
            self.store.get_rows,
            self.store.save_row,
            sensitive_fn=lambda value: 'SECRET_TOKEN' in str(value or ''),
            now_fn=now_fn,
            approval_ttl_minutes=30,
            minimum_candidate_score=80,
            minimum_improvement=1,
        )
        self.engine.create_or_update_skill(
            'Test Skill', 'Do the task safely.',
            instructions=['Be accurate'], success_criteria=['Correct'],
            allowed_tools=['reason'],
        )
        self.lab.add_benchmark_case(
            'Test Skill', 'Test request', 'Give a grounded safe answer',
            criteria=['grounded'], case_id='case-one',
        )

    def test_candidate_is_separate_from_active_skill(self):
        candidate = self.lab.propose_candidate('Test Skill')
        self.assertEqual(candidate['candidate_version'], 2)
        self.assertEqual(self.engine.get_skill('Test Skill')['version'], 1)
        self.assertEqual(candidate['allowed_tools'], ['reason'])
        rows = [x for x in self.store.rows if x['category'] == SKILL_CANDIDATE_CATEGORY]
        self.assertEqual(len(rows), 1)

    def test_benchmark_active_and_candidate_same_suite(self):
        active = self.lab.evaluate('Test Skill', 'active')
        candidate = self.lab.propose_candidate('Test Skill')
        cand = self.lab.evaluate('Test Skill', 'candidate')
        self.assertEqual(active['suite_hash'], cand['suite_hash'])
        self.assertEqual(active['average_score'], 82.0)
        self.assertEqual(cand['average_score'], 91.0)
        self.assertEqual(cand['candidate_id'], candidate['candidate_id'])
        runs = [x for x in self.store.rows if x['category'] == SKILL_BENCHMARK_RUN_CATEGORY]
        self.assertEqual(len(runs), 2)

    def test_promotion_requires_fresh_human_approval(self):
        self.lab.evaluate('Test Skill', 'active')
        self.lab.propose_candidate('Test Skill')
        self.lab.evaluate('Test Skill', 'candidate')
        prepared = self.lab.prepare_promotion('Test Skill')
        self.assertTrue(prepared['metrics']['gate_passed'])
        self.assertEqual(self.engine.get_skill('Test Skill')['version'], 1)
        approved = self.lab.approve_promotion(prepared['promotion_id'], prepared['approval_code'])
        self.assertEqual(approved['status'], 'approved')
        self.assertEqual(self.engine.get_skill('Test Skill')['version'], 1)
        promoted = self.lab.execute_promotion(prepared['promotion_id'])
        self.assertEqual(promoted['status'], 'promoted')
        self.assertEqual(promoted['activated_skill_version'], 2)
        self.assertEqual(self.engine.get_skill('Test Skill')['version'], 2)
        records = [x for x in self.store.rows if x['category'] == SKILL_PROMOTION_CATEGORY]
        self.assertGreaterEqual(len(records), 3)

    def test_worse_candidate_is_blocked(self):
        self.engine.candidate_score = 70
        self.lab.evaluate('Test Skill', 'active')
        self.lab.propose_candidate('Test Skill')
        self.lab.evaluate('Test Skill', 'candidate')
        with self.assertRaisesRegex(ValueError, 'did not pass'):
            self.lab.prepare_promotion('Test Skill')
        self.assertEqual(self.engine.get_skill('Test Skill')['version'], 1)

    def test_changed_benchmark_suite_invalidates_old_scores(self):
        self.lab.evaluate('Test Skill', 'active')
        self.lab.propose_candidate('Test Skill')
        self.lab.evaluate('Test Skill', 'candidate')
        self.lab.add_benchmark_case(
            'Test Skill', 'Second request', 'Second expected behavior',
            case_id='case-two',
        )
        with self.assertRaisesRegex(ValueError, 'Fresh benchmark evaluation'):
            self.lab.prepare_promotion('Test Skill')

    def test_sensitive_benchmark_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'sensitive'):
            self.lab.add_benchmark_case('Test Skill', 'SECRET_TOKEN=abc', 'Do not expose it')

    def test_credential_discussion_is_not_treated_as_a_secret_value(self):
        store = MemoryStore()
        engine = FakeEngine()
        lab = SkillPromotionLab(
            engine,
            store.get_rows,
            store.save_row,
            sensitive_fn=lambda value: 'token' in str(value or '').lower(),
            now_fn=lambda: '2026-09-16T20:30:00+00:00',
        )
        result = lab.bootstrap_developer_skill()
        self.assertEqual(result['benchmark_cases'], 5)
        self.assertEqual(engine.get_skill('Tyler AI Developer')['version'], 1)

    def test_developer_bootstrap_is_idempotent(self):
        first = self.lab.bootstrap_developer_skill()
        second = self.lab.bootstrap_developer_skill()
        self.assertTrue(first['created'])
        self.assertFalse(second['created'])
        self.assertEqual(first['benchmark_cases'], 5)
        self.assertEqual(second['benchmark_cases'], 5)
        self.assertEqual(self.engine.get_skill('Tyler AI Developer')['version'], 1)

    def test_status_never_enables_automatic_promotion(self):
        status = self.lab.status()
        self.assertFalse(status['automatic_skill_promotion_enabled'])
        self.assertTrue(status['human_approval_required_for_promotion'])
        self.assertFalse(status['fine_tuned_model'])


if __name__ == '__main__':
    unittest.main()
