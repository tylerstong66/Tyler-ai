import unittest

import app_v2_19_2 as v2192
from skill_lab import SkillPromotionLab
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class StubTrainer:
    def __init__(self, champion=None):
        self.champion = champion

    def champion_candidate(self, skill_name):
        return self.champion

    def latest_session(self, skill_name):
        return {
            'skill_id': 'test-skill',
            'champion_score': 64.0 if self.champion else 56.0,
            'champion_pass_rate': 60.0 if self.champion else 40.0,
            'baseline_average_score': 56.0,
            'baseline_pass_rate': 40.0,
        }

    def _valid_candidate_runs(self, active, champion):
        return [{
            'average_score': 64.0,
            'pass_rate': 60.0,
            'case_results': [
                {'case_id': 'case-weak', 'score': 40, 'weaknesses': ['Verify repository state before claiming success.']},
                {'case_id': 'case-strong', 'score': 90, 'weaknesses': []},
            ],
        }]

    def feedback_bundle(self, skill_name, max_attempts=8):
        return {'active_weaknesses': ['Verify repository state before claiming success.']}

    def status(self):
        return {
            'champion_based_training': True,
            'champion_requires_confirmation': True,
            'automatic_activation': False,
            'human_promotion_required': True,
        }


class ConstrainedMutationTests(unittest.TestCase):
    def make_lab(self):
        store = MemoryStore()
        engine = FakeEngine()
        clock = {'n': 0}

        def now_fn():
            clock['n'] += 1
            return f"2026-09-17T14:{clock['n']:02d}:00+00:00"

        lab = SkillPromotionLab(
            engine, store.get_rows, store.save_row, now_fn=now_fn,
            minimum_candidate_score=80, minimum_improvement=1,
        )
        engine.create_or_update_skill(
            'Test Skill', 'Do safe developer work.',
            instructions=['Inspect current code.', 'Report only verified state.'],
            success_criteria=['Changes are grounded.', 'Claims are verified.'],
            allowed_tools=['reason', 'github'],
        )
        return store, engine, lab

    def test_parser_accepts_one_tagged_replacement(self):
        parsed = v2192._parse_mutation_text(
            'TARGET_KIND=instruction\nTARGET_INDEX=2\n'
            'REPLACEMENT=Verify exact repository state before reporting success.\n'
            'RATIONALE=Targets the weak verification case.'
        )
        self.assertEqual(parsed['target_kind'], 'instruction')
        self.assertEqual(parsed['target_index'], 2)
        self.assertIn('repository state', parsed['replacement'])

    def test_single_mutation_preserves_every_other_field(self):
        parent = {
            'instructions': ['A', 'B', 'C'],
            'success_criteria': ['X', 'Y'],
            'allowed_tools': ['reason'],
        }
        instructions, criteria, diff = v2192._single_mutation(parent, {
            'target_kind': 'criterion', 'target_index': 2,
            'replacement': 'Y improved', 'rationale': 'target weak case',
        })
        self.assertEqual(instructions, ['A', 'B', 'C'])
        self.assertEqual(criteria, ['X', 'Y improved'])
        self.assertEqual(diff['before'], 'Y')
        self.assertEqual(diff['after'], 'Y improved')
        preflight = v2192._structural_preflight(parent, instructions, criteria, ['reason'])
        self.assertTrue(preflight['passed'])
        self.assertEqual(preflight['changed_fields'], 1)

    def test_preflight_blocks_multiple_changes_and_tool_drift(self):
        parent = {
            'instructions': ['A', 'B'], 'success_criteria': ['X'],
            'allowed_tools': ['reason'],
        }
        with self.assertRaisesRegex(RuntimeError, 'exactly 1'):
            v2192._structural_preflight(parent, ['A2', 'B2'], ['X'], ['reason'])
        with self.assertRaisesRegex(RuntimeError, 'tool-permission drift'):
            v2192._structural_preflight(parent, ['A2', 'B'], ['X'], ['reason', 'shell'])

    def test_constrained_candidate_uses_champion_and_changes_one_field_only(self):
        store, engine, lab = self.make_lab()
        champion = {
            'candidate_id': 'CND-CHAMPION1',
            'skill_id': 'test-skill',
            'name': 'Test Skill',
            'purpose': 'Do safe developer work.',
            'base_version': 1,
            'candidate_version': 2,
            'instructions': ['Inspect current code.', 'Report only verified state.'],
            'success_criteria': ['Changes are grounded.', 'Claims are verified.'],
            'allowed_tools': ['reason', 'github'],
            'status': 'candidate',
        }
        stub = StubTrainer(champion)
        old_trainer = v2192.TRAINER
        original_complete = engine.complete

        def complete(messages, tokens=700, temperature=0.2, json_mode=False):
            system = messages[0]['content']
            if 'one narrow skill-profile replacement operation' in system:
                return (
                    'TARGET_KIND=instruction\n'
                    'TARGET_INDEX=2\n'
                    'REPLACEMENT=Report success only after verifying the exact repository or deployment state.\n'
                    'RATIONALE=Targets the weakest verification benchmark without changing other behavior.'
                )
            return original_complete(messages, tokens=tokens, temperature=temperature, json_mode=json_mode)

        v2192.TRAINER = stub
        engine.complete = complete
        try:
            candidate = v2192._constrained_propose_candidate(lab, 'Test Skill')
        finally:
            v2192.TRAINER = old_trainer
            engine.complete = original_complete

        self.assertEqual(candidate['parent_candidate_id'], 'CND-CHAMPION1')
        self.assertTrue(candidate['evolved_from_champion'])
        self.assertTrue(candidate['constrained_mutation'])
        self.assertEqual(candidate['mutation_target_case_id'], 'case-weak')
        self.assertEqual(candidate['preflight']['changed_fields'], 1)
        self.assertEqual(candidate['instructions'][0], champion['instructions'][0])
        self.assertNotEqual(candidate['instructions'][1], champion['instructions'][1])
        self.assertEqual(candidate['success_criteria'], champion['success_criteria'])
        self.assertEqual(candidate['allowed_tools'], champion['allowed_tools'])
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)

    def test_replacement_size_guard_blocks_runaway_rewrite(self):
        parent = {
            'instructions': ['Short instruction'],
            'success_criteria': ['Correct'],
            'allowed_tools': ['reason'],
        }
        with self.assertRaisesRegex(RuntimeError, 'drifted too far'):
            v2192._single_mutation(parent, {
                'target_kind': 'instruction', 'target_index': 1,
                'replacement': 'x' * 181, 'rationale': '',
            })

    def test_version_budget_and_safety_flags(self):
        self.assertEqual(v2192.VERSION_SHORT, 'v2.19.2')
        self.assertEqual(v2192.MAX_MUTATED_FIELDS, 1)
        self.assertLessEqual(
            v2192.ITERATIVE_BENCHMARK_OUTPUT_BUDGET + v2192.ITERATIVE_CANDIDATE_OUTPUT_TOKENS,
            1000,
        )
        self.assertFalse(v2192.TRAINER.status()['automatic_activation'])
        inventory = v2192.EXECUTOR.safe_source_files_fn()
        self.assertIn('app_v2_19_2.py', inventory)
        self.assertIn('app_v2_19_1.py', inventory)
        self.assertIn('champion_training.py', inventory)


if __name__ == '__main__':
    unittest.main()
