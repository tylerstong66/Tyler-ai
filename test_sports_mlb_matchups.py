"""No-network identity, chronology, consistency and fail-closed tests."""
import copy
import unittest
from sports_mlb_matchups import analyze

START = '2026-10-15T23:00:00Z'
NOW = '2026-10-15T17:00:00Z'
THROUGH = '2026-10-14T23:00:00Z'


def example():
    return {
        'game_id': '849831', 'as_of': NOW, 'event_start': START,
        'hitter': {'id': 10001, 'name': 'Synthetic Hitter'},
        'starter': {'id': 20001, 'name': 'Synthetic Starter', 'status': 'probable'},
        'bullpen_candidates': [
            {'id': 30001, 'name': 'Synthetic Reliever A', 'availability': 'unknown'},
            {'id': 30002, 'name': 'Synthetic Reliever B', 'availability': 'limited'}],
        'matchups': [
            {'hitter_id': 10001, 'pitcher_id': 20001, 'pa': 20, 'ab': 18, 'hits': 6, 'home_runs': 1,
             'source_url': 'https://statsapi.mlb.com/api/v1/people/10001/stats',
             'retrieved_at': NOW, 'data_through': THROUGH},
            {'hitter_id': 10001, 'pitcher_id': 30001, 'pa': 4, 'ab': 3, 'hits': 1,
             'source_url': 'https://baseballsavant.mlb.com/leaderboard',
             'retrieved_at': NOW, 'data_through': THROUGH},
        ],
    }


class MatchupResearchTests(unittest.TestCase):
    def test_valid_historical_rates_missing_values_and_no_forecast(self):
        a = analyze(example())
        self.assertEqual(a['decision'], 'RESEARCH ONLY - NO BET')
        self.assertEqual(a['coverage'], {'expected_pitchers': 3, 'pitchers_with_sourced_stats': 2})
        self.assertAlmostEqual(a['starter_matchup']['historical_batting_average'], 1/3, places=4)
        self.assertEqual(a['starter_matchup']['historical_hr_per_pa'], .05)
        self.assertTrue(a['starter_matchup']['small_sample_under_25_pa'])
        self.assertIsNone(a['reliever_matchups'][0]['historical_hr_per_pa'])
        self.assertIsNone(a['reliever_matchups'][1]['historical_batting_average'])
        self.assertIsNone(a['estimated_hit_probability'])
        self.assertIsNone(a['estimated_home_run_probability'])
        self.assertIsNone(a['joint_parlay_probability'])
        self.assertIsNone(a['expected_value'])
        self.assertFalse(a['starter_matchup']['source']['independently_verified'])

    def test_zero_at_bats_has_no_invented_average(self):
        a = example()
        a['matchups'][0].update(pa=1, ab=0, hits=0, home_runs=0)
        out = analyze(a)
        self.assertIsNone(out['starter_matchup']['historical_batting_average'])
        self.assertEqual(out['starter_matchup']['historical_hr_per_pa'], 0)

    def test_wrong_player_or_pitcher_rejected(self):
        for key, value in [('hitter_id', 9999), ('pitcher_id', 9999)]:
            with self.subTest(key=key):
                a = example(); a['matchups'][0][key] = value
                with self.assertRaises(ValueError): analyze(a)

    def test_duplicate_rows_and_pitchers_rejected(self):
        a = example(); a['matchups'].append(copy.deepcopy(a['matchups'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate'): analyze(a)
        a = example(); a['bullpen_candidates'].append(copy.deepcopy(a['bullpen_candidates'][0]))
        with self.assertRaisesRegex(ValueError, 'distinct'): analyze(a)

    def test_future_and_postgame_data_rejected(self):
        for field in ('retrieved_at', 'data_through'):
            with self.subTest(field=field):
                a = example(); a['matchups'][0][field] = '2026-10-15T19:00:00Z'
                with self.assertRaisesRegex(ValueError, 'after'): analyze(a)
        a = example(); a['as_of'] = START
        with self.assertRaisesRegex(ValueError, 'precede'): analyze(a)
        a = example(); a['event_start'] = '2026-10-15T16:00:00Z'
        with self.assertRaisesRegex(ValueError, 'precede'): analyze(a)

    def test_impossible_stats_and_missing_source_rejected(self):
        for updates in ({'pa': 8}, {'ab': 3}, {'hits': 1, 'home_runs': 2}, {'hits': -1},
                        {'pa': True}, {'source_url': 'http://localhost/stats'},
                        {'source_url': 'https://127.0.0.1/stats'},
                        {'retrieved_at': '2026-10-15T17:00:00'},
                        {'data_through': '2026-10-15T18:00:00Z'}):
            with self.subTest(updates=updates):
                a = example(); a['matchups'][0].update(updates)
                with self.assertRaises(ValueError): analyze(a)

    def test_empty_bullpen_coverage_is_explicit(self):
        a = example(); a['bullpen_candidates'] = []; a['matchups'] = []
        out = analyze(a)
        self.assertEqual(out['coverage']['pitchers_with_sourced_stats'], 0)
        self.assertEqual(out['reliever_matchups'], [])
        self.assertTrue(any('No bullpen candidates' in s for s in out['limitations']))

    def test_no_external_source_calls(self):
        a = example()
        a['matchups'][0]['source_url'] = 'https://example.org/source'
        self.assertEqual(analyze(a)['decision'], 'RESEARCH ONLY - NO BET')


if __name__ == '__main__':
    unittest.main()
