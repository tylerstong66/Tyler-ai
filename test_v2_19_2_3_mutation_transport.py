import json
import unittest

import app_v2_19_2_3 as v21923
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
            'session_id': 'TRN-TRANSPORT01',
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


class MutationTransportTests(unittest.TestCase):
    def make_lab(self):
        store = MemoryStore()
        engine = FakeEngine()
        clock = {'n': 0}

        def now_fn():
            clock['n'] += 1
            return f"2026-09-17T17:{clock['n']:02d}:00+00:00"

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

    def install_stub(self, stub):
        targets = [
            (v21923, 'TRAINER'),
            (v21923.v21922, 'TRAINER'),
            (v21923.v21922.v21921.v2192, 'TRAINER'),
        ]
        old = [(obj, name, getattr(obj, name)) for obj, name in targets]
        for obj, name in targets:
            setattr(obj, name, stub)
        return old

    @staticmethod
    def restore_stub(old):
        for obj, name, value in old:
            setattr(obj, name, value)

    def test_markdown_colon_parser(self):
        raw = (
            '**Option 1:**\n'
            '- **Target Kind:** instruction\n'
            '- **Target Index:** 2\n'
            '- **Replacement:** Report success only after verifying exact repository state.\n'
            '- **Rationale:** Targets verification.\n'
        )
        options = v21923._parse_mutation_slate_resilient(raw)
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]['target_kind'], 'instruction')
        self.assertEqual(options[0]['target_index'], 2)
        self.assertIn('repository state', options[0]['replacement'])

    def test_json_parser_accepts_options_array(self):
        raw = json.dumps({
            'options': [
                {
                    'target_kind': 'criterion',
                    'target_index': 2,
                    'replacement': 'Claims are verified against exact current state.',
                    'rationale': 'Targets verification.',
                },
                {
                    'kind': 'instruction',
                    'index': 1,
                    'replace_with': 'Inspect exact current code before editing.',
                    'reason': 'Alternative.',
                },
            ]
        })
        options = v21923._parse_mutation_slate_resilient(raw)
        self.assertEqual(len(options), 2)
        self.assertEqual(options[0]['target_kind'], 'criterion')
        self.assertEqual(options[1]['target_kind'], 'instruction')

    def test_single_line_tag_parser(self):
        raw = (
            'TARGET_KIND: instruction TARGET_INDEX: 2 '
            'REPLACEMENT: Report only after exact verification. '
            'RATIONALE: Fix the weak case.'
        )
        options = v21923._parse_mutation_slate_resilient(raw)
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]['target_index'], 2)
        self.assertIn('exact verification', options[0]['replacement'])

    def test_unparseable_provider_reply_uses_local_fallback_without_second_call(self):
        store, engine, lab, active, champion = self.make_lab()
        stub = StubTrainer(champion)
        old = self.install_stub(stub)
        original_complete = engine.complete
        calls = {'n': 0}

        def complete(messages, tokens=700, temperature=0.2, json_mode=False):
            calls['n'] += 1
            return 'I recommend making the verification behavior more explicit.'

        engine.complete = complete
        try:
            candidate = v21923._resilient_propose_candidate(lab, 'Test Skill')
        finally:
            engine.complete = original_complete
            self.restore_stub(old)

        self.assertEqual(calls['n'], 1)
        self.assertEqual(candidate['mutation_generation_source'], 'deterministic_fallback')
        self.assertTrue(candidate['mutation_resilient_transport'])
        self.assertTrue(candidate['constrained_mutation'])
        self.assertEqual(candidate['parent_candidate_id'], champion['candidate_id'])
        self.assertEqual(candidate['allowed_tools'], champion['allowed_tools'])
        self.assertEqual(candidate['preflight']['changed_fields'], 1)
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)
        self.assertEqual(
            candidate['mutation_target_weakness'],
            'Verify repository state before claiming success.'
        )

    def test_local_fallback_skips_known_duplicate(self):
        store, engine, lab, active, champion = self.make_lab()
        stub = StubTrainer(champion)
        old = self.install_stub(stub)
        original_complete = engine.complete

        # Seed the first deterministic fallback edit as already attempted.
        focus = {'weakness': 'Verify repository state before claiming success.'}
        first = v21923._local_fallback_mutations(champion, focus, 1)[0]
        v21923.v21922._save_mutation_attempt(
            lab, active, champion, first,
            outcome='selected_novel_candidate',
            requested_index=first['target_index'],
            resolved_index=first['target_index'],
            option_number=1,
            session_id='TRN-OLD',
        )

        def complete(messages, tokens=700, temperature=0.2, json_mode=False):
            return 'No machine-readable mutation was produced.'

        engine.complete = complete
        try:
            candidate = v21923._resilient_propose_candidate(lab, 'Test Skill')
        finally:
            engine.complete = original_complete
            self.restore_stub(old)

        self.assertEqual(candidate['mutation_generation_source'], 'deterministic_fallback')
        self.assertNotEqual(candidate['mutation_key'], v21923.v21922._mutation_key(
            first['target_kind'], first['target_index'], first['replacement']
        ))
        attempts = [
            labmod._parse_row(row) for row in store.rows
            if row['category'] == v21923.MUTATION_ATTEMPT_CATEGORY
        ]
        outcomes = [item['outcome'] for item in attempts]
        self.assertIn('fallback_duplicate_mutation', outcomes)
        self.assertIn('fallback_selected_novel_candidate', outcomes)

    def test_provider_format_still_uses_provider_candidate(self):
        store, engine, lab, active, champion = self.make_lab()
        stub = StubTrainer(champion)
        old = self.install_stub(stub)
        original_complete = engine.complete

        def complete(messages, tokens=700, temperature=0.2, json_mode=False):
            return (
                'OPTION=1\n'
                'TARGET_KIND=criterion\n'
                'TARGET_INDEX=2\n'
                'REPLACEMENT=Claims are verified against exact current repository state.\n'
                'RATIONALE=Targets the weak verification case.'
            )

        engine.complete = complete
        try:
            candidate = v21923._resilient_propose_candidate(lab, 'Test Skill')
        finally:
            engine.complete = original_complete
            self.restore_stub(old)

        self.assertEqual(candidate['mutation_generation_source'], 'provider')
        self.assertEqual(candidate['success_criteria'][0], champion['success_criteria'][0])
        self.assertNotEqual(candidate['success_criteria'][1], champion['success_criteria'][1])
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)

    def test_version_budget_and_safety_flags(self):
        self.assertEqual(v21923.VERSION_SHORT, 'v2.19.2.3')
        self.assertEqual(v21923.MAX_MUTATED_FIELDS, 1)
        self.assertEqual(v21923.MAX_NOVELTY_OPTIONS, 3)
        self.assertGreaterEqual(v21923.MAX_LOCAL_FALLBACK_OPTIONS, 6)
        self.assertLessEqual(
            v21923.ITERATIVE_BENCHMARK_OUTPUT_BUDGET +
            v21923.ITERATIVE_CANDIDATE_OUTPUT_TOKENS,
            1000,
        )
        self.assertFalse(v21923.TRAINER.status()['automatic_activation'])
        self.assertIn('app_v2_19_2_3.py', v21923.EXECUTOR.safe_source_files_fn())


if __name__ == '__main__':
    unittest.main()
