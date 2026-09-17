import types
import unittest

import app_v2_19 as v219
from skill_iteration import (
    SKILL_TRAINING_ROUND_CATEGORY,
    SKILL_TRAINING_SESSION_CATEGORY,
    IterativeSkillTrainer,
)
from skill_lab import SkillPromotionLab
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class CandidateEngine(FakeEngine):
    def complete(self, messages, tokens=700, temperature=0.2, json_mode=False):
        system = messages[0]['content']
        self.calls.append((messages, json_mode))
        if not json_mode and 'Improve Tyler AI skill profiles through conservative iteration' in system:
            return (
                'INSTRUCTIONS=Inspect current code first || Verify state before claiming success || '
                'Address benchmark failures explicitly\n'
                'CRITERIA=Grounded || Verified || No unverified side-effect claims\n'
                'RATIONALE=Uses prior failed-candidate evidence to tighten verification.'
            )
        return super().complete(messages, tokens=tokens, temperature=temperature, json_mode=json_mode)


class FeedbackStub:
    def feedback_bundle(self, skill_name, max_attempts=6):
        return {
            'active_version': 1,
            'active_evaluation_id': 'EVL-ACTIVE',
            'active_average_score': 56.0,
            'active_pass_rate': 40.0,
            'active_weaknesses': ['missed deployment verification'],
            'failed_attempts': [{
                'candidate_id': 'CND-OLD',
                'average_score': 51.0,
                'pass_rate': 20.0,
                'weakness_count': 2,
                'weaknesses': ['claimed success too early', 'missed rollback state'],
                'instructions': ['Old failed instruction'],
                'success_criteria': ['Old criterion'],
                'rationale': 'Old failed attempt',
            }],
            'suite_hash': 'suite',
        }


class IterativeTrainingTests(unittest.TestCase):
    def make_lab(self, active_score=82, candidate_score=70):
        store = MemoryStore()
        engine = FakeEngine()
        engine.active_score = active_score
        engine.candidate_score = candidate_score
        clock = {'n': 0}

        def now_fn():
            clock['n'] += 1
            return f"2026-09-17T00:{clock['n']:02d}:00+00:00"

        lab = SkillPromotionLab(
            engine,
            store.get_rows,
            store.save_row,
            now_fn=now_fn,
            minimum_candidate_score=80,
            minimum_improvement=1,
        )
        engine.create_or_update_skill(
            'Test Skill', 'Do safe work.',
            instructions=['Be accurate'],
            success_criteria=['Correct'],
            allowed_tools=['reason'],
        )
        lab.add_benchmark_case(
            'Test Skill', 'Test request', 'Give a grounded safe answer',
            criteria=['grounded'], case_id='case-one',
        )
        return store, engine, lab, now_fn

    def test_start_requires_fresh_active_benchmark(self):
        store, engine, lab, now_fn = self.make_lab()
        trainer = IterativeSkillTrainer(lab, store.get_rows, store.save_row, now_fn=now_fn)
        with self.assertRaisesRegex(ValueError, 'fresh active benchmark'):
            trainer.start('Test Skill')

    def test_failed_candidate_history_becomes_feedback(self):
        store, engine, lab, now_fn = self.make_lab(active_score=82, candidate_score=70)
        lab.evaluate('Test Skill', 'active')
        candidate = lab.propose_candidate('Test Skill')
        lab.evaluate('Test Skill', 'candidate')
        trainer = IterativeSkillTrainer(lab, store.get_rows, store.save_row, now_fn=now_fn)
        feedback = trainer.feedback_bundle('Test Skill')
        self.assertEqual(feedback['failed_attempts'][0]['candidate_id'], candidate['candidate_id'])
        self.assertEqual(feedback['failed_attempts'][0]['average_score'], 70.0)
        self.assertGreaterEqual(len(feedback['active_weaknesses']), 1)

    def test_worse_round_is_rejected_and_active_skill_stays_v1(self):
        store, engine, lab, now_fn = self.make_lab(active_score=82, candidate_score=70)
        lab.evaluate('Test Skill', 'active')
        trainer = IterativeSkillTrainer(lab, store.get_rows, store.save_row, now_fn=now_fn, max_rounds=3)
        session = trainer.start('Test Skill')
        result = trainer.advance('Test Skill')
        self.assertEqual(session['active_version'], 1)
        self.assertEqual(result['session']['status'], 'needs_next_round')
        self.assertFalse(result['metrics']['gate_passed'])
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)
        self.assertEqual(result['session']['rounds_completed'], 1)
        categories = [x['category'] for x in store.rows]
        self.assertIn(SKILL_TRAINING_SESSION_CATEGORY, categories)
        self.assertIn(SKILL_TRAINING_ROUND_CATEGORY, categories)

    def test_passing_round_still_requires_human_promotion(self):
        store, engine, lab, now_fn = self.make_lab(active_score=82, candidate_score=91)
        lab.evaluate('Test Skill', 'active')
        trainer = IterativeSkillTrainer(lab, store.get_rows, store.save_row, now_fn=now_fn)
        trainer.start('Test Skill')
        result = trainer.advance('Test Skill')
        self.assertTrue(result['metrics']['gate_passed'])
        self.assertEqual(result['session']['status'], 'quality_gate_passed')
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)
        prepared = lab.prepare_promotion('Test Skill')
        self.assertEqual(prepared['status'], 'awaiting_approval')
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)

    def test_round_limit_exhausts_without_activation(self):
        store, engine, lab, now_fn = self.make_lab(active_score=82, candidate_score=60)
        lab.evaluate('Test Skill', 'active')
        trainer = IterativeSkillTrainer(lab, store.get_rows, store.save_row, now_fn=now_fn, max_rounds=1)
        trainer.start('Test Skill')
        result = trainer.advance('Test Skill')
        self.assertEqual(result['session']['status'], 'exhausted')
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)
        with self.assertRaisesRegex(ValueError, 'not eligible'):
            trainer.advance('Test Skill')

    def test_history_aware_candidate_preserves_tools(self):
        store = MemoryStore()
        engine = CandidateEngine()
        lab = SkillPromotionLab(
            engine, store.get_rows, store.save_row,
            now_fn=lambda: '2026-09-17T01:00:00+00:00',
        )
        active = engine.create_or_update_skill(
            'Test Skill', 'Do safe work.',
            instructions=['Inspect first'], success_criteria=['Correct'], allowed_tools=['reason'],
        )
        old_trainer = v219.TRAINER
        v219.TRAINER = FeedbackStub()
        try:
            candidate = v219._iterative_propose_candidate(lab, 'Test Skill')
        finally:
            v219.TRAINER = old_trainer
        self.assertEqual(candidate['allowed_tools'], active['allowed_tools'])
        self.assertEqual(candidate['learned_from_failed_attempts'], 1)
        self.assertEqual(candidate['parent_candidate_id'], 'CND-OLD')
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)
        prompt = engine.calls[0][0][1]['content']
        self.assertIn('claimed success too early', prompt)
        self.assertIn('missed deployment verification', prompt)

    def test_v219_budget_version_and_human_gate(self):
        self.assertEqual(v219.VERSION_SHORT, 'v2.19.0')
        self.assertLessEqual(
            v219.ITERATIVE_BENCHMARK_OUTPUT_BUDGET + v219.ITERATIVE_CANDIDATE_OUTPUT_TOKENS,
            1000,
        )
        self.assertEqual(v219.ITERATIVE_BENCHMARK_OUTPUT_BUDGET, 800)
        self.assertFalse(v219.TRAINER.status()['automatic_activation'])
        self.assertTrue(v219.TRAINER.status()['human_promotion_required'])
        inventory = v219.EXECUTOR.safe_source_files_fn()
        self.assertIn('app_v2_19.py', inventory)
        self.assertIn('skill_iteration.py', inventory)


if __name__ == '__main__':
    unittest.main()
