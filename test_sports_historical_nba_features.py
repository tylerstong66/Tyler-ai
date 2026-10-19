"""NBA feature diagnostics cannot borrow future or other-season results."""
import copy
from datetime import datetime,timedelta,timezone
import unittest
from unittest.mock import patch

import sports_historical_nba_features as features

START=datetime(2024,10,22,19,tzinfo=timezone.utc)


def game(index,*,days=None,observed=None,score=106):
    start=START+timedelta(days=index*3 if days is None else days)
    at=observed or datetime(2026,10,18,tzinfo=timezone.utc)
    return {'league':'NBA','nba_game_id':f'00224{index:05d}',
        'espn_game_id':str(401000000+index),'home_tricode':'NYK','away_tricode':'BOS',
        'home_score':score,'away_score':100,
        'nba_scheduled_start_utc':start.isoformat(),'espn_scheduled_start_utc':start.isoformat(),
        'nba_source_observed_at_utc':at.isoformat(),'espn_source_observed_at_utc':at.isoformat(),
        'corroboration_available_at_utc':at.isoformat()}


class HistoricalNbaFeatureTests(unittest.TestCase):
    def run_rows(self,rows):return features.chronological_features(rows,season=2024)

    def test_observed_and_reconstructed_availability_never_share_state(self):
        rows=[game(0),game(1)]
        out=self.run_rows(rows)
        first,last=out
        self.assertEqual(first['views']['reconstructed_24h']['home']['prior_games'],0)
        observed=last['views']['observed_receipt_time']['home']
        reconstructed=last['views']['reconstructed_24h']['home']
        self.assertEqual(observed['prior_games'],0)
        self.assertIsNone(observed['mean_points_for'])
        self.assertIsNone(observed['days_since_prior_start'])
        self.assertEqual(reconstructed['prior_games'],1)
        self.assertEqual(reconstructed['mean_margin'],6)
        self.assertEqual(reconstructed['days_since_prior_start'],3)
        self.assertEqual(reconstructed['source_history'][0]['source_row_sha256'],features.digest(rows[0]))
        self.assertFalse(last['eligible_for_model_training'])
        self.assertFalse(last['historical_pregame_availability_attested'])

    def test_current_and_future_scores_cannot_change_earlier_features(self):
        rows=[game(i) for i in range(3)];before=self.run_rows(rows)
        for index in (1,2):
            changed=copy.deepcopy(rows);changed[index]['home_score']=123
            after=self.run_rows(changed)
            for target in range(index+1):
                self.assertEqual(before[target]['views'],after[target]['views'])
        self.assertEqual(rows,[game(i) for i in range(3)])

    def test_24_hour_boundary_and_simultaneous_games_are_not_available(self):
        for days in (0,1):
            with self.subTest(days=days):
                out=self.run_rows([game(0),game(1,days=days)])
                self.assertEqual(out[-1]['views']['reconstructed_24h']['home']['prior_games'],0)
        out=self.run_rows([game(0),game(1,days=1+2/86400)])
        self.assertEqual(out[-1]['views']['reconstructed_24h']['home']['prior_games'],1)

    def test_actual_observation_must_precede_cutoff_and_both_sources_matter(self):
        prior=game(0,observed=START+timedelta(days=1))
        later=game(1,days=2)
        self.assertEqual(self.run_rows([prior,later])[-1]['views']['observed_receipt_time']['home']['prior_games'],1)
        prior['espn_source_observed_at_utc']=later['espn_scheduled_start_utc']
        prior['corroboration_available_at_utc']=later['espn_scheduled_start_utc']
        self.assertEqual(self.run_rows([prior,later])[-1]['views']['observed_receipt_time']['home']['prior_games'],0)

    def test_last_ten_is_by_game_time_even_when_receipts_arrive_out_of_order(self):
        rows=[game(i,observed=START+timedelta(days=40-i/10),score=101+i) for i in range(12)]
        rows.append(game(12,days=45))
        out=self.run_rows(rows)[-1]['views']['observed_receipt_time']['home']
        self.assertEqual(out['prior_games'],10)
        self.assertEqual([x['nba_game_id'] for x in out['source_history']],
                         [x['nba_game_id'] for x in rows[2:12]])

    def test_input_order_and_heldout_call_cannot_change_training_state(self):
        rows=[game(i) for i in range(3)]
        before=self.run_rows(rows)
        self.assertEqual(before,self.run_rows(list(reversed(rows))))
        validation=game(0);validation['nba_game_id']='0022500000'
        for key in ('nba_scheduled_start_utc','espn_scheduled_start_utc'):
            validation[key]='2025-10-22T19:00:00Z'
        features.chronological_features([validation],season=2025)
        self.assertEqual(before,self.run_rows(rows))
        with self.assertRaises(ValueError):self.run_rows(rows+[validation])

    def test_duplicate_ids_and_invalid_source_chronology_fail(self):
        for key,value in (('home_score',True),('home_score',100),('home_tricode','BOS'),
                          ('corroboration_available_at_utc','2026-10-17T00:00:00Z'),
                          ('nba_source_observed_at_utc',START.isoformat()),
                          ('espn_scheduled_start_utc','2024-10-22T19:00:00')):
            with self.subTest(key=key,value=value):
                row=game(0);row[key]=value
                with self.assertRaises(ValueError):self.run_rows([row])
        with self.assertRaises(ValueError):self.run_rows([game(0),game(0)])

    def test_build_verifies_both_seals_before_crosscheck_and_keeps_all_guards(self):
        report={'corroborated_research_only':[game(0)],'pending_or_quarantined':2}
        with patch.object(features.original_seal,'verify') as old, \
             patch.object(features.independent_seal,'verify') as new, \
             patch.object(features.crosscheck,'build',return_value=report) as check:
            result=features.build()
            old.assert_called_once();new.assert_called_once();check.assert_called_once()
            self.assertEqual(result['other_pending_games'],2)
            self.assertEqual(result['protocol_sha256'],features.digest(features.PROTOCOL))
            for k in ('model_training_enabled','historical_evaluation_enabled','forecasting_enabled',
                      'promotion_allowed','source_scope_complete','historical_pregame_features_verified'):
                self.assertIs(result[k],False)
            new.side_effect=ValueError('seal changed');check.reset_mock()
            with self.assertRaises(ValueError):features.build()
            check.assert_not_called()


if __name__=='__main__':unittest.main()
