import json
import math
import tempfile
import unittest
from pathlib import Path

import sports_benchmark_review as r


class ReviewTests(unittest.TestCase):
    def add_game(self, root, sport='NHL', identifier='1', outcome='home', market=.5,
                 model_probability=.7, week=5, kickoff='2026-10-14T00:30:00+00:00'):
        models = r.COHORTS[sport][1]
        pred = {'game_id': identifier, 'event_id': 'espn'+identifier, 'season': 2026, 'week': week,
                'generated_at': '2026-10-11T12:00:00+00:00', 'recorded_at': '2026-10-11T12:00:01+00:00',
                'kickoff': kickoff, 'NO_BET': True, 'actual_wagers': 0,
                'market_observed_at': '2026-10-11T11:59:00+00:00',
                'market': None if market is None else {'conditional_home_probability': market}}
        for i, name in enumerate(models):
            p = model_probability if i == 0 else .5
            pred[name] = {'home': p, 'away': 1-p}
            if sport == 'NFL':
                pred[name] = {'home': p*.98, 'away': (1-p)*.98, 'tie': .02}
        pred['sha256'] = r.digest(pred)
        result = {'game_id': identifier, 'outcome': outcome, 'home_score': 3 if outcome == 'home' else 2,
                  'away_score': 3 if outcome == 'away' else 2, 'prediction_sha256': pred['sha256'],
                  'verified_at': '2026-10-15T10:00:00+00:00', 'scores': {}}
        for name in models:
            probs = pred[name]
            score = {}
            if sport == 'NFL':
                full = r.full_scores(probs, outcome)
                score = {'full_brier': full['brier'], 'full_log_loss': full['log_loss'],
                         'binary_brier': None, 'conditional_log_loss': None, 'correct': None}
            if outcome != 'tie':
                binary = r.binary_scores(probs['home']/(1-probs['tie']) if sport == 'NFL' else probs['home'], outcome)
                score.update({'binary_brier' if sport == 'NFL' else 'brier': binary['brier'],
                              'conditional_log_loss' if sport == 'NFL' else 'log_loss': binary['log_loss'],
                              'correct': bool(binary['accuracy'])})
            result['scores'][name] = score
        if market is not None and outcome != 'tie':
            binary = r.binary_scores(market, outcome)
            result['scores']['market'] = {'binary_brier' if sport == 'NFL' else 'brier': binary['brier'],
                                         'conditional_log_loss' if sport == 'NFL' else 'log_loss': binary['log_loss'],
                                         'correct': bool(binary['accuracy'])}
        for kind, data in [('predictions', pred), ('results', result)]:
            r.write(root/kind/(identifier+'.json'), data)
        return pred, result

    def review(self, root, sport='NHL'):
        return r.review(root, sport, r.COHORTS[sport][1])

    def test_known_scores_have_correct_scale_and_loss(self):
        self.assertAlmostEqual(r.binary_scores(.8, 'home')['brier'], .08)
        self.assertAlmostEqual(r.binary_scores(.8, 'home')['log_loss'], -math.log(.8))
        self.assertEqual(r.binary_scores(.5, 'away')['accuracy'], 0)
        full = r.full_scores({'home': .5, 'away': .4, 'tie': .1}, 'tie')
        self.assertAlmostEqual(full['brier'], 1.22)
        self.assertEqual(full['accuracy'], 0)
        self.assertAlmostEqual(full['log_loss'], -math.log(.1))

    def test_unpriced_forecasts_count_in_full_sample_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.add_game(root, identifier='1', outcome='home', market=.6)
            self.add_game(root, identifier='2', outcome='away', market=None)
            data = self.review(root)
            self.assertEqual(data['settled'], 2)
            self.assertEqual(data['all_decisive']['model']['games'], 2)
            self.assertEqual(data['paired_market']['model']['games'], 1)
            self.assertEqual(data['paired_market']['market']['games'], 1)
            self.assertAlmostEqual(data['all_decisive']['model']['mean']['accuracy'], .5)
            self.assertEqual(data['paired_market']['model']['mean']['accuracy'], 1)
            self.assertEqual(data['paired_differences']['fixed_elo']['games'], 2)
            self.assertEqual(data['paired_differences']['market']['games'], 1)
            self.assertIn(' pp', r.render(data))
            self.assertIn('actual wagers $0', r.render(data))

    def test_nfl_ties_in_full_scores_and_calibration_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for identifier, outcome in [('1', 'home'), ('2', 'tie'), ('3', 'away')]:
                self.add_game(root, 'NFL', identifier, outcome)
            data = self.review(root, 'NFL')
            self.assertEqual(data['settled'], 3)
            self.assertEqual(data['ties'], 1)
            self.assertEqual(data['all_settled_three_outcome']['v2']['games'], 3)
            self.assertEqual(data['all_decisive']['v2']['games'], 2)
            self.assertEqual(data['paired_market']['market']['games'], 2)
            self.assertEqual(data['full_outcome_calibration']['v2']['tie']['games'], 3)
            self.assertEqual(data['conditional_home_calibration']['v2']['games'], 2)
            self.assertAlmostEqual(data['all_settled_three_outcome']['v2']['mean']['accuracy'], 1/3)

    def test_empty_sample_is_unavailable_and_pending_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.add_game(root)
            (root/'results/1.json').unlink()
            data = self.review(root)
            self.assertEqual((data['recorded'], data['settled'], data['pending']), (1, 0, 1))
            self.assertIsNone(data['all_decisive']['model']['mean']['accuracy'])
            self.assertIsNone(data['paired_market']['market']['mean']['brier'])
            self.assertFalse(data['review_due'])
            self.assertIn('Unavailable', r.render(data))

    def test_milestone_at_100_does_not_stop_enrollment_or_infer_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(99):self.add_game(root, identifier=str(i))
            self.assertFalse(self.review(root)['review_due'])
            self.add_game(root, identifier='99')
            data = self.review(root)
            self.assertTrue(data['review_due'])
            self.assertEqual(data['review_status'], 'ready_for_human_review')
            self.add_game(root, identifier='100')
            self.assertEqual(self.review(root)['settled'], 101)
            self.assertTrue(data['NO_BET']);self.assertEqual(data['actual_wagers'], 0)

    def test_corrupt_link_scores_ids_probabilities_and_times_are_rejected(self):
        cases = ['hash', 'link', 'orphan', 'score', 'outcome', 'late', 'naive', 'probability', 'future_market', 'final_time']
        for case in cases:
            with self.subTest(case=case),tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp);pred, result = self.add_game(root)
                if case == 'hash':pred['model']['home'] = .8
                elif case == 'link':result['prediction_sha256'] = 'wrong'
                elif case == 'orphan':result['game_id'] = 'not_saved'
                elif case == 'score':result['scores']['model']['brier'] = 0
                elif case == 'outcome':result['outcome'] = 'away'
                elif case == 'final_time':result['verified_at'] = pred['generated_at']
                else:
                    if case == 'late':pred['recorded_at'] = pred['kickoff']
                    elif case == 'naive':pred['generated_at'] = '2026-10-11T12:00:00'
                    elif case == 'probability':pred['model']['home'] = float('inf')
                    elif case == 'future_market':pred['market_observed_at'] = pred['kickoff']
                    if case != 'probability':
                        pred.pop('sha256');pred['sha256'] = r.digest(pred)
                (root/'predictions/1.json').write_text(json.dumps(pred))
                (root/'results/1.json').write_text(json.dumps(result))
                with self.assertRaises((r.IntegrityError, ValueError)):self.review(root)

    def test_calibration_boundaries_and_empty_bins(self):
        data = r.calibration([(0, False), (.2, True), (1, True)])
        bins = data['bins']
        self.assertEqual([b['games'] for b in bins], [1, 1, 0, 0, 1])
        self.assertIsNone(bins[2]['mean_probability'])
        self.assertIsNone(bins[2]['observed_rate_wilson95'])
        self.assertAlmostEqual(r.wilson(5, 10)[0], .236593090512564, places=10)
        self.assertAlmostEqual(r.wilson(5, 10)[1], .763406909487436, places=10)

    def test_same_block_does_not_create_false_independent_sample(self):
        records = [{'block': 'one-date', 'brier': i/100, 'log_loss': .7, 'accuracy': i % 2} for i in range(100)]
        data = r.estimates(records)
        self.assertEqual(data['games'], 100);self.assertEqual(data['blocks'], 1)
        self.assertEqual(data['uncertainty_status'], 'insufficient_blocks')
        self.assertIsNone(data['ci95']['brier'])

    def test_bootstrap_is_deterministic_game_weighted_and_handles_zero_differences(self):
        records = [{'block': str(i), 'brier': i/10, 'log_loss': i/5, 'accuracy': i % 2} for i in range(5)]
        records += [records[-1].copy() for _ in range(4)]
        data = r.estimates(records, draws=100)
        self.assertEqual(data, r.estimates(list(reversed(records)), draws=100))
        self.assertAlmostEqual(data['mean']['brier'], (1+1.6)/9)
        self.assertIsNotNone(data['ci95']['brier'])
        zeros = [{**record, 'brier': 0, 'log_loss': 0, 'accuracy': 0} for record in records]
        self.assertEqual(r.estimates(zeros, draws=100)['ci95']['brier'], [0, 0])

    def test_real_archived_cohorts_reproduce_existing_scores_without_writes(self):
        for sport, (folder, models) in r.COHORTS.items():
            root = Path(folder)
            before = {str(p): p.read_bytes() for kind in ['predictions', 'results'] for p in (root/kind).glob('*.json')}
            data = self.review(root, sport)
            summary = json.loads((root/'summary.json').read_text())
            self.assertEqual(data['settled'], summary['settled'])
            paired_key = 'paired_priced_decisive_games' if sport == 'NFL' else 'paired_games'
            self.assertEqual(data['paired_market'][models[0]]['games'], summary[paired_key])
            for path, content in before.items():self.assertEqual(Path(path).read_bytes(), content)

    def test_week_and_eastern_date_define_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.add_game(root, identifier='1', kickoff='2026-10-14T00:30:00Z')
            self.add_game(root, identifier='2', kickoff='2026-10-14T03:30:00Z')
            _, rows = r.load_rows(root, 'NHL', r.COHORTS['NHL'][1])
            self.assertEqual({row['block'] for row in rows}, {'2026-10-13'})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.add_game(root, sport='NFL', week=5)
            _, rows = r.load_rows(root, 'NFL', r.COHORTS['NFL'][1])
            self.assertEqual(rows[0]['block'], '2026/5')

    def test_report_continues_other_cohorts_when_one_has_corrupt_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for sport, (folder, _) in r.COHORTS.items():self.add_game(base/folder, sport)
            broken = base/r.COHORTS['NFL'][0]/'results/1.json'
            data = json.loads(broken.read_text());data['prediction_sha256'] = 'wrong';r.write(broken, data)
            output = r.run(base)
            self.assertEqual(output['leagues'][0]['input_integrity'], 'error')
            self.assertIsNone(output['leagues'][0]['review_due'])
            self.assertNotIn('settled', output['leagues'][0])
            self.assertEqual(output['leagues'][1]['settled'], 1)
            self.assertTrue((base/'benchmarks/two_way_prospective/REVIEW_ALL.md').exists())

    def test_saved_collection_failures_and_nfl_enrollment_exclusions_are_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture = root/'captures/20261014T120000Z'
            r.write(capture/'manifest.json', {'errors': []})
            r.write(capture/'enrollment.json', {'excluded': [{'game_id': 'late', 'reason': 'already_started'}]})
            r.write(root/'errors/20261014T130000Z.json', {'error': 'upstream unavailable', 'collection_completed': False})
            data = r.collection_evidence(root, 'NFL')
            self.assertIsNone(data['collection_completed'])
            self.assertEqual(data['excluded'][0]['game_id'], 'late')
            self.assertEqual(data['newer_saved_collection_failure']['error'], 'upstream unavailable')


if __name__ == '__main__':unittest.main()
