"""Deterministic, result-blind NHL archived-probability comparison tests."""
import unittest

import sports_benchmark_review as review
import sports_nhl_shadow_preview as preview


class NhlShadowPreviewTests(unittest.TestCase):
    def game(self, name, kickoff, price=.52):
        source = {
            'game_id': name, 'event_id': 'E'+name,
            'home': 'WSH', 'away': 'NJD',
            'kickoff': kickoff,
            'generated_at': '2026-10-16T17:24:56Z',
            'market_observed_at': '2026-10-16T17:24:55Z',
            'sha256': 'source'+name,
            'model': {'home': .54},
            'fixed_elo': {'home': .62},
            'market': ({'provider':'saved', 'conditional_home_probability':price}
                       if price is not None else None),
        }
        saved = {
            'game_id': name, 'event_id': source['event_id'],
            'kickoff': kickoff, 'recorded_at': '2026-10-16T17:24:58Z',
            'source_prediction_sha256': source['sha256'],
            'home_probability': .59, 'sha256': 'shadow'+name,
        }
        return source, saved

    def test_future_only_and_earliest_25_not_best_confidence(self):
        now=review.utc('2026-10-16T18:00:00Z')
        sources, saved={},{}
        for i in range(29):
            start='2026-10-17T%02d:00:00Z' % (i%24)
            # Two days to retain valid hours when adding >24 games.
            start=('2026-10-17T' if i<24 else '2026-10-18T')+f'{i%24:02d}:00:00Z'
            source, shadow=self.game(f'{i:02d}',start)
            source['model']['home']=.4+(i/100)
            sources[shadow['game_id']]=source
            saved[shadow['game_id']]=shadow
        source, shadow=self.game('past','2026-10-16T17:59:00Z')
        sources['past']=source;saved['past']=shadow
        report=preview.upcoming(saved,sources,now)
        self.assertEqual(report['total_future_enrolled'],29)
        self.assertEqual(report['shown'],25)
        self.assertEqual([p['game_id'] for p in report['games']],
                         [f'{i:02d}' for i in range(25)])
        self.assertTrue(report['NO_BET'])
        self.assertEqual(report['actual_wagers'],0)

    def test_missing_market_stays_missing_not_zero(self):
        source, shadow=self.game('no-market','2026-10-17T17:00:00Z',None)
        report=preview.upcoming({'no-market':shadow},{'no-market':source},
                                review.utc('2026-10-16T19:00:00Z'))
        row=report['games'][0]
        self.assertIsNone(row['home_win_probabilities']['saved_market'])
        self.assertIsNone(row['saved_market_observed_at_utc'])
        self.assertFalse(row['live_market_quote'])

    def test_rejects_identity_conflict_and_future_market_quote(self):
        source, shadow=self.game('G1','2026-10-17T17:00:00Z')
        now=review.utc('2026-10-16T19:00:00Z')
        with self.assertRaisesRegex(ValueError,'source identity mismatch'):
            preview.upcoming({'G1':{**shadow,'source_prediction_sha256':'other'}},
                             {'G1':source},now)
        with self.assertRaisesRegex(ValueError,'game identity mismatch'):
            preview.upcoming({'G1':{**shadow,'event_id':'other'}},
                             {'G1':source},now)
        source['market_observed_at']='2026-10-16T19:00:00Z'
        with self.assertRaisesRegex(ValueError,'post-forecast odds'):
            preview.upcoming({'G1':shadow},{'G1':source},now)


if __name__=='__main__':
    unittest.main()
