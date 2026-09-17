import unittest

import app_v2_19_1 as v2191
from champion_training import ChampionSkillTrainer, SKILL_CHAMPION_CHECK_CATEGORY
from skill_lab import SkillPromotionLab
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class ChampionTrainingTests(unittest.TestCase):
    def make_lab(self, active_score=56, candidate_score=64):
        store = MemoryStore()
        engine = FakeEngine()
        engine.active_score = active_score
        engine.candidate_score = candidate_score
        clock = {'n': 0}

        def now_fn():
            clock['n'] += 1
            return f"2026-09-17T03:{clock['n']:02d}:00+00:00"

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
        lab.evaluate('Test Skill', 'active')
        return store, engine, lab, now_fn

    def test_historical_best_is_seeded_but_requires_confirmation(self):
        store, engine, lab, now_fn = self.make_lab()
        engine.candidate_score = 51
        lab.propose_candidate('Test Skill')
        lab.evaluate('Test Skill', 'candidate')
        engine.candidate_score = 64
        best_candidate = lab.propose_candidate('Test Skill')
        lab.evaluate('Test Skill', 'candidate')
        engine.candidate_score = 54
        lab.propose_candidate('Test Skill')
        lab.evaluate('Test Skill', 'candidate')

        trainer = ChampionSkillTrainer(lab, store.get_rows, store.save_row, now_fn=now_fn)
        session = trainer.start('Test Skill')
        self.assertEqual(session['status'], 'champion_confirmation_required')
        self.assertEqual(session['pending_champion_candidate_id'], best_candidate['candidate_id'])
        self.assertEqual(session['pending_champion_initial_score'], 64.0)
        self.assertEqual(session['champion_score'], 56.0)
        self.assertEqual(session['champion_source'], 'active_baseline')

    def test_consistent_confirmation_makes_candidate_verified_champion(self):
        store, engine, lab, now_fn = self.make_lab()
        engine.candidate_score = 64
        candidate = lab.propose_candidate('Test Skill')
        lab.evaluate('Test Skill', 'candidate')
        trainer = ChampionSkillTrainer(lab, store.get_rows, store.save_row, now_fn=now_fn)
        trainer.start('Test Skill')

        engine.candidate_score = 62
        result = trainer.advance('Test Skill')
        self.assertEqual(result['mode'], 'champion_confirmation')
        self.assertTrue(result['champion_check']['confirmed'])
        self.assertEqual(result['session']['champion_candidate_id'], candidate['candidate_id'])
        self.assertEqual(result['session']['champion_score'], 63.0)
        self.assertEqual(result['session']['status'], 'needs_next_round')
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)
        categories = [row['category'] for row in store.rows]
        self.assertIn(SKILL_CHAMPION_CHECK_CATEGORY, categories)

    def test_inconsistent_lucky_score_does_not_become_champion(self):
        store, engine, lab, now_fn = self.make_lab()
        engine.candidate_score = 90
        candidate = lab.propose_candidate('Test Skill')
        lab.evaluate('Test Skill', 'candidate')
        trainer = ChampionSkillTrainer(
            lab, store.get_rows, store.save_row, now_fn=now_fn, consistency_tolerance=10
        )
        trainer.start('Test Skill')

        engine.candidate_score = 60
        result = trainer.advance('Test Skill')
        self.assertFalse(result['champion_check']['confirmed'])
        self.assertGreater(result['champion_check']['score_spread'], 10)
        self.assertIsNone(result['session']['champion_candidate_id'])
        self.assertEqual(result['session']['champion_score'], 56.0)
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)
        self.assertEqual(result['candidate']['candidate_id'], candidate['candidate_id'])

    def test_new_candidate_must_beat_champion_then_wait_for_confirmation(self):
        store, engine, lab, now_fn = self.make_lab()
        trainer = ChampionSkillTrainer(lab, store.get_rows, store.save_row, now_fn=now_fn)
        session = trainer.start('Test Skill')
        self.assertEqual(session['status'], 'ready_for_round')

        engine.candidate_score = 64
        result = trainer.advance('Test Skill')
        self.assertEqual(result['mode'], 'candidate_round')
        self.assertTrue(result['champion_metrics']['beats_champion'])
        self.assertEqual(result['session']['status'], 'champion_confirmation_required')
        self.assertIsNone(result['session']['champion_candidate_id'])
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)

    def test_passing_candidate_still_needs_two_runs_and_human_promotion(self):
        store, engine, lab, now_fn = self.make_lab(active_score=82, candidate_score=91)
        trainer = ChampionSkillTrainer(lab, store.get_rows, store.save_row, now_fn=now_fn)
        trainer.start('Test Skill')
        first = trainer.advance('Test Skill')
        self.assertEqual(first['session']['status'], 'champion_confirmation_required')
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)

        second = trainer.advance('Test Skill')
        self.assertTrue(second['champion_check']['confirmed'])
        self.assertEqual(second['session']['status'], 'quality_gate_passed')
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)
        prepared = lab.prepare_promotion('Test Skill')
        self.assertEqual(prepared['status'], 'awaiting_approval')
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)

    def test_champion_parent_is_used_without_broadening_tools(self):
        store, engine, lab, now_fn = self.make_lab()
        trainer = ChampionSkillTrainer(lab, store.get_rows, store.save_row, now_fn=now_fn)
        trainer.start('Test Skill')
        engine.candidate_score = 64
        first = trainer.advance('Test Skill')
        champion_id = first['candidate']['candidate_id']
        engine.candidate_score = 63
        confirmed = trainer.advance('Test Skill')
        self.assertEqual(confirmed['session']['champion_candidate_id'], champion_id)

        old_trainer = v2191.TRAINER
        v2191.TRAINER = trainer
        try:
            child = v2191._champion_propose_candidate(lab, 'Test Skill')
        finally:
            v2191.TRAINER = old_trainer
        self.assertEqual(child['parent_candidate_id'], champion_id)
        self.assertTrue(child['evolved_from_champion'])
        self.assertEqual(child['allowed_tools'], ['reason'])
        self.assertEqual(engine.get_skill('Test Skill')['version'], 1)

    def test_round_budget_version_and_safety_flags(self):
        self.assertEqual(v2191.VERSION_SHORT, 'v2.19.1')
        self.assertLessEqual(
            v2191.ITERATIVE_BENCHMARK_OUTPUT_BUDGET + v2191.ITERATIVE_CANDIDATE_OUTPUT_TOKENS,
            1000,
        )
        status = v2191.TRAINER.status()
        self.assertTrue(status['champion_based_training'])
        self.assertTrue(status['champion_requires_confirmation'])
        self.assertFalse(status['automatic_activation'])
        self.assertTrue(status['human_promotion_required'])
        inventory = v2191.EXECUTOR.safe_source_files_fn()
        self.assertIn('champion_training.py', inventory)
        self.assertIn('app_v2_19_1.py', inventory)


if __name__ == '__main__':
    unittest.main()
