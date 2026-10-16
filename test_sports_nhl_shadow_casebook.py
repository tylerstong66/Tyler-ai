"""Result-neutral audit-casebook tests (synthetic verified score rows)."""
import unittest

import sports_benchmark_review as review
import sports_nhl_shadow_casebook as c


def fixture(identifier, final_date, priced=True):
    source={
        'sha256':'source-'+identifier,'game_id':identifier,
        'event_id':'E'+identifier,'away':'NJD','home':'WSH',
        'kickoff':'2026-10-17T17:00:00Z',
        'market': {'provider':'archived','conditional_home_probability':.52}
                  if priced else None,
        'market_observed_at':'2026-10-16T17:30:00Z'
    }
    shadow={'sha256':'challenger-'+identifier,
            'source_prediction_sha256':source['sha256']}
    score=lambda p: review.binary_scores(p,'home')
    row={'game_id':identifier,'outcome':'home',
         'verified_at':final_date,
         'home_probabilities':{'candidate':.59,'model':.54,'fixed_elo':.62,
                              'market':.52 if priced else None},
         'candidate':score(.59),'model':score(.54),'fixed_elo':score(.62),
         'market':score(.52) if priced else None}
    return source, shadow, row


class NhlShadowCasebookTests(unittest.TestCase):
    def test_no_score_report_is_explicitly_empty(self):
        out=c.recent_verified([],{}, {})
        self.assertEqual(out['shown'],0)
        self.assertEqual(out['total_settled_shadow_games'],0)
        self.assertEqual(out['games'],[])
        self.assertEqual(out['actual_wagers'],0)

    def test_latest_verified_first_and_25_display_cap_not_performance(self):
        originals, shadows, rows={}, {}, []
        for i in range(29):
            s,sh,r=fixture(str(i),f'2026-10-18T12:{i:02d}:00Z',priced=i%2==0)
            originals[str(i)]=s
            shadows[str(i)]=sh
            rows.append(r)
        out=c.recent_verified(rows,shadows,originals)
        self.assertEqual((out['total_settled_shadow_games'],out['shown']),(29,25))
        self.assertEqual([x['game_id'] for x in out['games']],
                         [str(i) for i in range(28,3,-1)])
        self.assertIsNone(out['games'][0]['challenger_minus_baseline']['market'])
        self.assertIsNotNone(out['games'][1]['challenger_minus_baseline']['market'])
        self.assertEqual(out['games'][0]['saved_market_provider'],None)
        self.assertTrue(out['NO_BET'])

    def test_digests_and_winner_side_verified_with_scores(self):
        s,sh,r=fixture('g','2026-10-18T12:00:00Z')
        out=c.recent_verified([r], {'g':sh},{'g':s})
        row=out['games'][0]
        self.assertEqual(row['verified_winner'],'WSH')
        self.assertEqual(row['verified_winner_side'],'home')
        self.assertEqual(row['original_forecast_sha256'],s['sha256'])
        self.assertAlmostEqual(row['challenger_minus_baseline']['fixed_elo']['log_loss'],
                               r['candidate']['log_loss']-r['fixed_elo']['log_loss'])
        sh['source_prediction_sha256']='tampered'
        with self.assertRaisesRegex(ValueError,'digest mismatch'):
            c.recent_verified([r], {'g':sh},{'g':s})

    def test_rejects_missing_identity_and_bad_outcome(self):
        s,sh,r=fixture('g','2026-10-18T12:00:00Z')
        bad={**r,'outcome':'tie'}
        with self.assertRaisesRegex(ValueError,'two-way final'):
            c.recent_verified([bad],{'g':sh},{'g':s})


if __name__=='__main__':
    unittest.main()
