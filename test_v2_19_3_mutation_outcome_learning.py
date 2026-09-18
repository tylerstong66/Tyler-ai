import unittest

import app_v2_19_3 as v2193
import skill_lab as labmod
from skill_lab import (
    SKILL_BENCHMARK_RUN_CATEGORY,
    SKILL_CANDIDATE_CATEGORY,
    SkillPromotionLab,
)
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class ReferenceTrainer:
    def __init__(self, parent):
        self.parent = parent

    def _candidate_by_id(self, skill_name, candidate_id):
        if str(candidate_id or '').upper() == str(self.parent.get('candidate_id') or '').upper():
            return self.parent
        return None

    def _valid_candidate_runs(self, active, candidate):
        return [{
            'run_id': 'EVL-PARENT001',
            'candidate_id': self.parent['candidate_id'],
            'average_score': 64.0,
            'pass_rate': 60.0,
            'case_results': [
                {'case_id': 'case-a', 'score': 70, 'weaknesses': []},
                {'case_id': 'case-b', 'score': 58, 'weaknesses': ['Needs verification.']},
            ],
        }]


class MutationOutcomeLearningTests(unittest.TestCase):
    def make_lab(self):
        store = MemoryStore()
        engine = FakeEngine()
        clock = {'n': 0}

        def now_fn():
            clock['n'] += 1
            return f"2026-09-17T18:{clock['n']:02d}:00+00:00"

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
        return store, engine, lab, active

    def test_semantic_harm_repetition_is_blocked(self):
        prior = 'Report success only after verifying the exact repository state.'
        context = {
            'direction_stats': {},
            'harmful': [{
                'outcome_id': 'MTO-HARM001',
                'replacement': prior,
                'score_delta': -38.0,
                'pass_rate_delta': -40.0,
                'outcome': 'harmful',
            }],
            'beneficial': [],
        }
        rank = v2193._mutation_learning_rank({
            'target_kind': 'instruction',
            'target_index': 2,
            'replacement': prior,
        }, context)
        self.assertTrue(rank['hard_block'])
        self.assertEqual(rank['blocking_outcome_id'], 'MTO-HARM001')
        self.assertGreaterEqual(rank['harmful_similarity'], v2193.HARMFUL_SEMANTIC_BLOCK_THRESHOLD)

    def test_direction_stats_reward_helpful_and_penalize_harmful(self):
        stats = v2193._direction_stats([
            {
                'direction': 'criterion#2', 'score_delta': 8.0,
                'pass_rate_delta': 20.0, 'outcome': 'beneficial',
            },
            {
                'direction': 'instruction#1', 'score_delta': -18.0,
                'pass_rate_delta': -20.0, 'outcome': 'harmful',
            },
        ])
        self.assertGreater(stats['criterion#2']['direction_value'], 0)
        self.assertLess(stats['instruction#1']['direction_value'], 0)
        self.assertEqual(stats['criterion#2']['beneficial_count'], 1)
        self.assertEqual(stats['instruction#1']['harmful_count'], 1)

    def test_provider_slate_is_reordered_by_outcome_history(self):
        raw = (
            'OPTION=1\n'
            'TARGET_KIND=instruction\nTARGET_INDEX=1\n'
            'REPLACEMENT=Inspect current code and summarize it.\n'
            'RATIONALE=First option.\n'
            'OPTION=2\n'
            'TARGET_KIND=criterion\nTARGET_INDEX=2\n'
            'REPLACEMENT=Claims are verified against exact current state.\n'
            'RATIONALE=Second option.\n'
        )
        context = {
            'outcomes': [{'outcome': 'beneficial'}],
            'direction_stats': {
                'instruction#1': {'direction_value': -12.0},
                'criterion#2': {'direction_value': 9.0},
            },
            'harmful': [],
            'beneficial': [],
        }
        token = v2193._LEARNING_CONTEXT.set(context)
        try:
            options = v2193._outcome_sorted_parse(raw, 3)
        finally:
            v2193._LEARNING_CONTEXT.reset(token)
        self.assertEqual(options[0]['target_kind'], 'criterion')
        self.assertEqual(options[0]['target_index'], 2)

    def test_local_recovery_has_novel_options_after_first_three_duplicates(self):
        parent = {
            'instructions': ['Inspect current code.', 'Report only verified state.'],
            'success_criteria': ['Changes are grounded.', 'Claims are verified.'],
        }
        focus = {'weakness': 'Verify repository state before claiming success.'}
        options = v2193._outcome_ranked_local_fallback(parent, focus)

        self.assertGreater(len(options), 3)
        first_three = {
            v2193.v219231.v21923.v21922._mutation_key(
                item['target_kind'], item['target_index'], item['replacement']
            )
            for item in options[:3]
        }
        remaining = [
            item for item in options
            if v2193.v219231.v21923.v21922._mutation_key(
                item['target_kind'], item['target_index'], item['replacement']
            ) not in first_three
        ]
        self.assertTrue(remaining)
        self.assertLessEqual(len(options), v2193.MAX_LOCAL_FALLBACK_OPTIONS)

    def test_historical_candidates_become_cross_session_learning_evidence(self):
        store, engine, lab, active = self.make_lab()
        candidate = {
            'kind': 'skill_candidate',
            'candidate_id': 'CND-HISTORY01',
            'skill_id': active['skill_id'],
            'name': active['name'],
            'purpose': active['purpose'],
            'base_version': 1,
            'candidate_version': 2,
            'parent_candidate_id': 'CND-CHAMPION1',
            'parent_verified_score': 64.0,
            'parent_verified_pass_rate': 60.0,
            'mutation_key': 'mut-history',
            'mutation_diff': {
                'kind': 'criterion', 'resolved_index': 2,
                'before': 'Claims are verified.',
                'after': 'Claims are verified against exact current state.',
            },
            'instructions': list(active['instructions']),
            'success_criteria': [active['success_criteria'][0], 'Claims are verified against exact current state.'],
            'allowed_tools': list(active['allowed_tools']),
            'status': 'candidate',
            'created_at': '2026-09-17T18:00:00+00:00',
        }
        lab._save(SKILL_CANDIDATE_CATEGORY, candidate, 8)
        lab._save(SKILL_BENCHMARK_RUN_CATEGORY, {
            'kind': 'skill_benchmark_run',
            'run_id': 'EVL-HISTORY01',
            'skill_id': active['skill_id'],
            'target_kind': 'candidate',
            'candidate_id': candidate['candidate_id'],
            'average_score': 72.0,
            'pass_rate': 80.0,
            'case_results': [],
            'created_at': '2026-09-17T18:01:00+00:00',
        }, 7)

        evidence = v2193._historical_outcomes(lab, active)
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]['score_delta'], 8.0)
        self.assertEqual(evidence[0]['pass_rate_delta'], 20.0)
        self.assertEqual(evidence[0]['outcome'], 'beneficial')
        context = v2193._build_learning_context(lab, active)
        self.assertEqual(context['outcome_count'], 1)
        self.assertGreater(context['direction_stats']['criterion#2']['direction_value'], 0)

    def test_recorded_outcome_persists_delta_and_case_damage(self):
        store, engine, lab, active = self.make_lab()
        parent = {
            'candidate_id': 'CND-CHAMPION1',
            'skill_id': active['skill_id'],
            'base_version': 1,
        }
        trainer = ReferenceTrainer(parent)
        candidate = {
            'candidate_id': 'CND-BAD001',
            'skill_id': active['skill_id'],
            'base_version': 1,
            'parent_candidate_id': parent['candidate_id'],
            'parent_verified_score': 64.0,
            'parent_verified_pass_rate': 60.0,
            'mutation_attempt_id': 'MTA-BAD001',
            'mutation_key': 'mut-bad',
            'mutation_target_case_id': 'case-b',
            'mutation_target_weakness': 'Needs verification.',
            'mutation_diff': {
                'kind': 'instruction', 'resolved_index': 2,
                'before': 'Report only verified state.',
                'after': 'Report state quickly.',
            },
        }
        result = {
            'mode': 'candidate_round',
            'session': {'session_id': 'TRN-LEARN001'},
            'round': {'round_number': 1},
            'candidate': candidate,
            'evaluation': {
                'run_id': 'EVL-BAD001',
                'average_score': 46.0,
                'pass_rate': 40.0,
                'case_results': [
                    {'case_id': 'case-a', 'score': 70, 'weaknesses': []},
                    {'case_id': 'case-b', 'score': 22, 'weaknesses': ['Verification regressed.']},
                ],
            },
        }
        outcome = v2193._record_candidate_outcome(lab, trainer, result)
        self.assertEqual(outcome['score_delta'], -18.0)
        self.assertEqual(outcome['pass_rate_delta'], -20.0)
        self.assertEqual(outcome['outcome'], 'harmful')
        self.assertTrue(outcome['catastrophic'])
        self.assertIn('case-b', outcome['damaged_case_ids'])
        self.assertNotIn('case-a', outcome['damaged_case_ids'])
        rows = [row for row in store.rows if row['category'] == v2193.MUTATION_OUTCOME_CATEGORY]
        self.assertEqual(len(rows), 1)

    def test_outcome_record_is_idempotent_for_same_evaluation(self):
        store, engine, lab, active = self.make_lab()
        parent = {'candidate_id': 'CND-CHAMPION1', 'skill_id': active['skill_id'], 'base_version': 1}
        trainer = ReferenceTrainer(parent)
        result = {
            'mode': 'candidate_round',
            'session': {'session_id': 'TRN-IDEMPOTENT'},
            'round': {'round_number': 1},
            'candidate': {
                'candidate_id': 'CND-SAME001', 'skill_id': active['skill_id'], 'base_version': 1,
                'parent_candidate_id': parent['candidate_id'],
                'parent_verified_score': 64.0, 'parent_verified_pass_rate': 60.0,
                'mutation_diff': {'kind': 'criterion', 'resolved_index': 1, 'before': 'A', 'after': 'B'},
            },
            'evaluation': {
                'run_id': 'EVL-SAME001', 'average_score': 64.0, 'pass_rate': 60.0,
                'case_results': [],
            },
        }
        first = v2193._record_candidate_outcome(lab, trainer, result)
        second = v2193._record_candidate_outcome(lab, trainer, result)
        self.assertEqual(first['outcome_id'], second['outcome_id'])
        rows = [row for row in store.rows if row['category'] == v2193.MUTATION_OUTCOME_CATEGORY]
        self.assertEqual(len(rows), 1)

    def test_version_budget_and_safety_flags(self):
        self.assertEqual(v2193.VERSION_SHORT, 'v2.19.3')
        self.assertEqual(v2193.MAX_MUTATED_FIELDS, 1)
        self.assertEqual(v2193.MAX_NOVELTY_OPTIONS, 3)
        self.assertLessEqual(
            v2193.ITERATIVE_BENCHMARK_OUTPUT_BUDGET +
            v2193.ITERATIVE_CANDIDATE_OUTPUT_TOKENS,
            1000,
        )
        status = v2193.TRAINER.status()
        self.assertFalse(status['automatic_activation'])
        self.assertTrue(status['human_promotion_required'])
        self.assertIn('app_v2_19_3.py', v2193.EXECUTOR.safe_source_files_fn())
        self.assertIn(v2193.MUTATION_OUTCOME_CATEGORY, v2193.base.SPECIAL_MEMORY_CATEGORIES)


if __name__ == '__main__':
    unittest.main()
