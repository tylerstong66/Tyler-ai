import json
import unittest

from skill_engine import (
    SKILL_EXAMPLE_CATEGORY,
    SKILL_PROFILE_CATEGORY,
    SKILL_SCORE_CATEGORY,
    SkillEngine,
)


class MemoryStore:
    def __init__(self):
        self.rows = []
        self.next_id = 1

    def get_rows(self, category, limit):
        rows = [row for row in reversed(self.rows) if row['category'] == category]
        return rows[:limit]

    def save_row(self, text, category, importance):
        row = {
            'id': self.next_id,
            'created_at': f'2026-09-15T00:00:{self.next_id:02d}+00:00',
            'memories': text,
            'category': category,
            'importance': importance,
        }
        self.next_id += 1
        self.rows.append(row)
        return [row]


class SkillEngineTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.calls = []

        def complete(messages, tokens=700, temperature=0.2, json_mode=False):
            self.calls.append({
                'messages': messages,
                'tokens': tokens,
                'temperature': temperature,
                'json_mode': json_mode,
            })
            if json_mode:
                return json.dumps({
                    'score': 92,
                    'passed': True,
                    'strengths': ['accurate'],
                    'weaknesses': ['could be shorter'],
                    'improvement': 'Be more concise.',
                })
            return 'trained response'

        self.engine = SkillEngine(
            self.store.get_rows,
            self.store.save_row,
            complete,
            now_fn=lambda: '2026-09-15T12:00:00+00:00',
        )

    def create_skill(self):
        return self.engine.create_or_update_skill(
            'Job Search',
            'Find realistic roles and tailor application strategy.',
            instructions=['Prefer realistic matches', 'Explain gaps clearly'],
            success_criteria=['Actionable', 'Accurate'],
            allowed_tools=['research_web', 'read_memory'],
        )

    def test_create_and_version_skill(self):
        first = self.create_skill()
        second = self.engine.create_or_update_skill(
            'Job Search',
            'Updated purpose',
        )
        self.assertEqual(first['version'], 1)
        self.assertEqual(second['version'], 2)
        self.assertEqual(self.engine.get_skill('job-search')['purpose'], 'Updated purpose')
        profiles = [row for row in self.store.rows if row['category'] == SKILL_PROFILE_CATEGORY]
        self.assertEqual(len(profiles), 2)

    def test_add_example_and_build_context(self):
        self.create_skill()
        self.engine.add_example(
            'Job Search',
            'Find me a remote operations role.',
            'Return realistic roles ranked by interview odds.',
            tags=['jobs', 'remote'],
        )
        context = self.engine.build_context('job-search')
        self.assertIn('ACTIVE SKILL: Job Search', context)
        self.assertIn('Find me a remote operations role.', context)
        self.assertIn('Return realistic roles ranked by interview odds.', context)
        examples = [row for row in self.store.rows if row['category'] == SKILL_EXAMPLE_CATEGORY]
        self.assertEqual(len(examples), 1)

    def test_run_skill_uses_training_context(self):
        self.create_skill()
        result = self.engine.run_skill('Job Search', 'Help me find a role.')
        self.assertEqual(result, 'trained response')
        self.assertIn('ACTIVE SKILL: Job Search', self.calls[-1]['messages'][0]['content'])
        self.assertEqual(self.calls[-1]['temperature'], 0.15)

    def test_evaluation_is_saved_and_scored(self):
        self.create_skill()
        result = self.engine.evaluate_skill(
            'Job Search',
            'Find a role.',
            expected='A realistic role with reasoning.',
        )
        self.assertEqual(result['score'], 92)
        self.assertTrue(result['passed'])
        scores = [row for row in self.store.rows if row['category'] == SKILL_SCORE_CATEGORY]
        self.assertEqual(len(scores), 1)
        summary = self.engine.skill_summary('Job Search')
        self.assertEqual(summary['average_score'], 92.0)
        self.assertEqual(summary['pass_rate'], 100.0)
        self.assertFalse(summary['fine_tuned_model'])

    def test_export_is_future_fine_tuning_ready(self):
        self.create_skill()
        self.engine.add_example('Job Search', 'Input one', 'Ideal one')
        exported = self.engine.export_training_examples('Job Search')
        self.assertEqual(len(exported), 1)
        roles = [item['role'] for item in exported[0]['messages']]
        self.assertEqual(roles, ['system', 'user', 'assistant'])
        self.assertEqual(exported[0]['messages'][1]['content'], 'Input one')
        self.assertEqual(exported[0]['messages'][2]['content'], 'Ideal one')

    def test_missing_skill_is_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.add_example('missing', 'x', 'y')


if __name__ == '__main__':
    unittest.main()
