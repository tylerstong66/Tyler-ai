import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from datetime import timedelta
import sports_efficiency_candidate as c
import sports_historical_benchmark as b

ROOT = Path('benchmarks/nfl_efficiency_v2')


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = b.read_games(ROOT.parent/'nfl_independent_v1/games_2010_2025.csv', last=2024)
        cls.stats = c.read_stats(ROOT/'team_stats_2010_2024.csv', cls.games)

    def test_complete_pair_coverage(self):
        self.assertEqual(len(self.stats), 8156)

    def test_duplicate_missing_and_mismatched_stats_fail_closed(self):
        import csv
        game = self.games[0]
        with (ROOT/'team_stats_2010_2024.csv').open() as stream:
            rows = [r for r in csv.DictReader(stream) if r['game_id'] == game.identifier]
        for altered in [rows[:1], rows+[rows[0]], [{**rows[0], 'opponent_team':'BAD'}, rows[1]]]:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'stats.csv'
                with path.open('w',newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader();writer.writerows(altered)
                with self.assertRaises(ValueError):
                    c.read_stats(path,[game])

    def test_current_and_future_stats_do_not_change_pregame_features(self):
        games = self.games[:40]
        original = c.features(games, self.stats)
        altered = dict(self.stats)
        for g in games[20:]:
            for t in (g.home, g.away):
                altered[(g.identifier,t)] = (90000, 70)
        revised = c.features(games, altered)
        self.assertEqual([r['x'] for r in original[:21]], [r['x'] for r in revised[:21]])
        self.assertNotEqual(original[-1]['x'], revised[-1]['x'])

    def test_availability_delay(self):
        with self.assertRaises(ValueError):
            c.features(self.games[:2], self.stats, delay=24)

    def test_unknown_is_unknown(self):
        self.assertEqual(c.availability([], 'g', 'BUF', '2026-10-12T00:00:00Z')['coverage'], 'unknown')

    def observation(self):
        return {'game_id':'g','team':'BUF','player_id':'p','kind':'practice_status','status':'questionable','source_url':'https://www.buffalobills.com/report','source_sha256':'a'*64,'publication_time_verified':True,'published_at':'2026-10-11T10:00:00Z','retrieved_at':'2026-10-11T11:00:00Z'}

    def test_practice_does_not_become_inactive_or_model_feature(self):
        result = c.availability([self.observation()], 'g','BUF','2026-10-12T00:00:00Z')
        self.assertEqual(result['observations'][0]['kind'],'practice_status')
        self.assertFalse(result['injury_effect_enabled'])

    def test_late_and_unverified_observations_rejected(self):
        for patch in [{'retrieved_at':'2026-10-12T01:00:00Z'},{'publication_time_verified':False},{'source_sha256':'bad'},{'team':'MIA'},{'kind':'inferred_healthy'}]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                c.availability([{**self.observation(),**patch}], 'g','BUF','2026-10-12T00:00:00Z')

    def test_reproducibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            c.run(ROOT, Path(tmp)/'out')
            for name in ['model.json','report.json']:
                self.assertEqual((Path(tmp)/'out'/name).read_bytes(), (ROOT/'run_2026_10_11'/name).read_bytes())

    def test_freeze_gate_and_exclusive_output(self):
        model = json.loads((ROOT/'run_2026_10_11/model.json').read_text())
        frozen = b.utc(model['frozen_at'])
        game = replace(self.games[0], kickoff=frozen+timedelta(days=1))
        row = {'game':game,'x':[1,0,1,0,0,0,0],'cutoff':(game.kickoff-timedelta(seconds=1)).isoformat(), 'source_snapshots':[{'source_url':'https://example.com/test-fixture','retrieved_at':frozen.isoformat(),'sha256':'a'*64}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'prediction.json'
            result = c.freeze_prediction(path,model,row,frozen.isoformat(),model['frozen_at'])
            self.assertAlmostEqual(sum(result['probabilities'].values()),1)
            with self.assertRaises(FileExistsError):
                c.freeze_prediction(path,model,row,frozen.isoformat(),model['frozen_at'])
            with self.assertRaises(ValueError):
                c.freeze_prediction(Path(tmp)/'late',model,row,game.kickoff.isoformat(),model['frozen_at'])

    def test_fit_rejects_wrong_dimension(self):
        rows = b.chronological_features(self.games[:2])
        with self.assertRaises(ValueError):
            b.fit(rows,.001,dimension=7)


if __name__ == '__main__':
    unittest.main()
