import unittest

import app_v2_19_2_2 as v21922
import skill_lab as labmod
from skill_lab import SkillPromotionLab
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class StubTrainer:
    def __init__(self, champion):
        self.champion = champion

    def champion_candidate(self, skill_name):
        return self.champion

    def latest_session(self, skill_name):
        return {
            'session_id': 'TRN-NOVELTY01',
            'skill_id': 'test-skill',
            'champion_score': 64.0,
            'champion_pass_rate': 60.0,
            'baseline_average_score': 56.0,
            'baseline_pass_rate': 40.0,
        }

    def _valid_candidate_runs(self, active, champion):
        return [{
            'average_score': 64.0,
            'pass_rate': 60.0,
            'case_results': [{
                'case_id': 'case-weak',
                'score': 40,
                'weaknesses': ['Verify repository state before claiming success.'],
            }],
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


class MutationNoveltyTests(unittest.TestCase):
    def make_lab(self):
        store = MemoryStore()
        engine = FakeEngine()
        clock = {'n': 0}

        def now_fn():
            clock['n'] += 1
            return f"2026-09-17T16:{clock['n']:02d}:00+00:00"

        lab = SkillPromotionLab(
            engine, store.get_rows, store.save_row, now_fn=now_fn,
            minimum_candidate_score=80, minimum_improvement=1,
        )
        active = engine.create_or_update_skill(
            'Test Skill', 'Do safe developer work.',
            instructions=['Inspect current code.', 'Report only verified state.'],
            success_criteria=['Changes are grounded.', 'Claims are verified.'],
            allowed_tools=['reason', 'github'],
        )
        champion = {
            'candidate_id': 'CND-CHAMPION1',
            'skill_id': active['skill_id'],
            'name': active['name'],
            'purpose': active['purpose'],
            'base_version': 1,
            'candidate_version': 2,
            'instructions': list(active['instructions']),
            'success_criteria': list(active['success_criteria']),
            'allowed_tools': list(active['allowed_tools']),
            'status': 'candidate',
        }
        return store, engine, lab, active, champion

    def seed_prior_candidate(self, lab, active, champion, replacement):
        instructions = list(champion['instructions'])
        instructions[1] = replacement
        signature = v21922.v21921.v2192._profile_signature(
            instructions, champion['success_criteria']
        )
        return lab._save(labmod.SKILL_CANDIDATE_CATEGORY, {
            'kind': 'skill_candidate',
            'candidate_id': 'CND-OLDNOVEL1',
            'skill_id': active['skill_id'],
            'name': active['name'],
            'purpose': active['purpose'],
            'base_version': 1,
            'candidate_version': 2,
            'instructions': instructions,
            'success_criteria': list(champion['success_criteria']),
            'allowed_tools': list(champion['allowed_tools']),
            'mutation_diff': {
                'kind': 'instruction', 'index': 2,
                'before': champion['instructions'][1], 'after': replacement,
            },
            'profile_signature': signature,
            'status': 'candidate',
            'created_at': '2026-09-17T15:00:00+00:00',
        }, 8)

    def test_slate_parser_accepts_three_options(self):
        options = v21922._parse_mutation_slate(
            'OPTION=1\nTARGET_KIND=instruction\nTARGET_INDEX=1\nREPLACEMENT=A1\nRATIONALE=r1\n'
            'OPTION=2\nTARGET_KIND=criterion\nTARGET_INDEX=2\nREPLACEMENT=C2\nRATIONALE=r2\n'
            'OPTION=3\nTARGET_KIND=instruction\nTARGET_INDEX=2\nREPLACEMENT=A2\nRATIONALE=r3'
        )
        self.assertEqual(len(options), 3)
        self.assertEqual(options[1]['target_kind'], 'criterion')
        self.assertEqual(options[2]['target_index'], 2)

    def test_mutation_key_normalizes_equivalent_text(self):
        one = v21922._mutation_key('Instruction', 2, ' Verify   exact state ')
        two = v21922._mutation_key('instruction', 2, 'verify exact state')
        self.assertEqual(one, two)

    def test_duplicate_first_option_selects_second_novel_option_in_one_provider_call(self):
        store, engine, lab, active, champion = self.make_lab()
        old_replacement = 'Report success only after verifying exact repository state.'
        self.seed_prior_candidate(lab, active, champion, old_replacement)
        stub = StubTrainer(champion)
        old_trainer = v21922.TRAINER
        old_v2192_trainer = v21922.v21921.v2192.TRAINER
        call_count = {'n': 0}
        original_complete = engine.complete

        def complete(messages, tokens=700, temperature=0.2, json_mode=False):
            call_count['n'] += 1
            return (
                'OPTION=1\nTARGET_KIND=instruction\nTARGET_INDEX=2\n'
                f'REPLACEMENT={old_replacement}\nRATIONALE=old\n'
                'OPTION=2\nTARGET_KIND=criterion\nTARGET_INDEX=2\n'
                'REPLACEMENT=Claims are verified against the exact current repository or deployment state.\n'
                'RATIONALE=fix weakest case\n'
                'OPTION=3\nTARGET_KIND=instruction\nTARGET_INDEX=1\n'
                'REPLACEMENT=Inspect the exact current code and deployment metadata before editing.\n'
                'RATIONALE=alternate'
            )

        v21922.TRAINER = stub
        v21922.v21921.v2192.TRAINER = stub
        engine.complete = complete
        try:
            candidate = v21922._novelty_propose_candidate(lab, 'Test Skill')
        finally:
            v21922.TRAINER = old_trainer
            v21922.v21921.v2192.TRAINER = old_v2192_trainer
            engine.complete = original_complete

        self.assertEqual(call_count['n'], 1)
        self.assertEqual(candidate['mutation_novelty_option'], 2)
        self.assertTrue(candidate['mutation_novelty_tracking'])
        self.assertEqual(candidate['parent_candidate_id'], champion['candidate_id'])
        self.assertEqual(candidate['instructions'], champion['instructions'])
        self.assertNotEqual(candidate['success_criteria'][1], champion['success_criteria'][1])
        self.assertEqual(candidate['allowed_tools'], champion['allowed_tools'])
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)

        attempts = [
            row for row in store.rows
            if row['category'] == v21922.MUTATION_ATTEMPT_CATEGORY
        ]
        self.assertEqual(len(attempts), 2)
        parsed = [labmod._parse_row(row) for row in attempts]
        outcomes = {item['outcome'] for item in parsed}
        self.assertIn('duplicate_mutation', outcomes)
        self.assertIn('selected_novel_candidate', outcomes)

    def test_index_repair_and_novelty_work_together(self):
        store, engine, lab, active, champion = self.make_lab()
        stub = StubTrainer(champion)
        old_trainer = v21922.TRAINER
        old_v2192_trainer = v21922.v21921.v2192.TRAINER
        original_complete = engine.complete

        def complete(messages, tokens=700, temperature=0.2, json_mode=False):
            return (
                'OPTION=1\nTARGET_KIND=criterion\nTARGET_INDEX=99\n'
                'REPLACEMENT=Claims are verified against exact current state before success is reported.\n'
                'RATIONALE=repair malformed index'
            )

        v21922.TRAINER = stub
        v21922.v21921.v2192.TRAINER = stub
        engine.complete = complete
        try:
            candidate = v21922._novelty_propose_candidate(lab, 'Test Skill')
        finally:
            v21922.TRAINER = old_trainer
            v21922.v21921.v2192.TRAINER = old_v2192_trainer
            engine.complete = original_complete

        diff = candidate['mutation_diff']
        self.assertTrue(diff['index_repaired'])
        self.assertEqual(diff['requested_index'], 99)
        self.assertEqual(diff['resolved_index'], 2)
        self.assertEqual(candidate['preflight']['changed_fields'], 1)

    def test_all_duplicate_options_fail_closed_and_persist_attempts(self):
        store, engine, lab, active, champion = self.make_lab()
        replacements = [
            'Report verified state A.',
            'Report verified state B.',
            'Report verified state C.',
        ]
        for value in replacements:
            self.seed_prior_candidate(lab, active, champion, value)
        before_candidates = len(lab.candidates(active['skill_id'], 300))
        stub = StubTrainer(champion)
        old_trainer = v21922.TRAINER
        old_v2192_trainer = v21922.v21921.v2192.TRAINER
        original_complete = engine.complete

        def complete(messages, tokens=700, temperature=0.2, json_mode=False):
            chunks = []
            for i, value in enumerate(replacements, 1):
                chunks.append(
                    f'OPTION={i}\nTARGET_KIND=instruction\nTARGET_INDEX=2\n'
                    f'REPLACEMENT={value}\nRATIONALE=repeat'
                )
            return '\n'.join(chunks)

        v21922.TRAINER = stub
        v21922.v21921.v2192.TRAINER = stub
        engine.complete = complete
        try:
            with self.assertRaisesRegex(RuntimeError, 'novelty slate exhausted'):
                v21922._novelty_propose_candidate(lab, 'Test Skill')
        finally:
            v21922.TRAINER = old_trainer
            v21922.v21921.v2192.TRAINER = old_v2192_trainer
            engine.complete = original_complete

        after_candidates = len(lab.candidates(active['skill_id'], 300))
        self.assertEqual(before_candidates, after_candidates)
        attempts = [
            row for row in store.rows
            if row['category'] == v21922.MUTATION_ATTEMPT_CATEGORY
        ]
        self.assertEqual(len(attempts), 3)
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)

    def test_version_budget_and_safety_flags(self):
        self.assertEqual(v21922.VERSION_SHORT, 'v2.19.2.2')
        self.assertEqual(v21922.MAX_NOVELTY_OPTIONS, 3)
        self.assertEqual(v21922.MAX_MUTATED_FIELDS, 1)
        self.assertLessEqual(
            v21922.ITERATIVE_BENCHMARK_OUTPUT_BUDGET +
            v21922.ITERATIVE_CANDIDATE_OUTPUT_TOKENS,
            1000,
        )
        self.assertFalse(v21922.TRAINER.status()['automatic_activation'])
        self.assertIn(
            v21922.MUTATION_ATTEMPT_CATEGORY,
            v21922.base.SPECIAL_MEMORY_CATEGORIES,
        )
        self.assertIn('app_v2_19_2_2.py', v21922.EXECUTOR.safe_source_files_fn())


if __name__ == '__main__':
    unittest.main()
