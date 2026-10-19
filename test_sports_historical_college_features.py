"""College feature diagnostics isolate sports, seasons and availability views."""
import copy
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

import sports_historical_college_features as features
import test_sports_historical_d1_crosscheck as fixtures


def game(index,*,league='NCAAF_FBS',days=None):
    start=datetime(2024,9 if league=='NCAAF_FBS' else 11,4,18,tzinfo=timezone.utc)
    start+=timedelta(days=index*(7 if league=='NCAAF_FBS' else 3) if days is None else days)
    return {'league':league,'split':'train','ncaa_game_id':str(100+index),
        'espn_game_id':str(401000000+index),'home_team_id':'202','away_team_id':'101',
        'home_score':28,'away_score':21,'ncaa_start_utc':start.isoformat(),
        'espn_start_utc':start.isoformat(),'observed_available_at_utc':'2026-10-18T00:00:00Z'}


class HistoricalCollegeFeatureTests(unittest.TestCase):
    def run_rows(self,rows,league='NCAAF_FBS'):
        return features.chronological_features(rows,league=league,split='train')

    def test_separate_sport_windows_and_missing_observation_values(self):
        for league,window in (('NCAAF_FBS',4),('NCAAM_D1',8)):
            rows=[game(i,league=league) for i in range(11)]
            result=self.run_rows(rows,league)[-1]
            actual=result['views']['observed_receipt_time']['home']
            simulated=result['views']['reconstructed_24h']['home']
            self.assertEqual(actual['prior_games'],0);self.assertIsNone(actual['mean_points_for'])
            self.assertIsNone(actual['days_since_prior_start'])
            self.assertEqual(simulated['prior_games'],window)
            self.assertEqual(simulated['mean_margin'],7)
            self.assertFalse(result['eligible_for_model_training'])

    def test_current_and_future_results_cannot_change_earlier_features(self):
        rows=[game(i) for i in range(3)];before=self.run_rows(rows)
        for index in (1,2):
            altered=copy.deepcopy(rows);altered[index]['away_score']=40
            after=self.run_rows(altered)
            for target in range(index+1):self.assertEqual(before[target]['views'],after[target]['views'])
        self.assertEqual(rows,[game(i) for i in range(3)])

    def test_simultaneous_and_exact_24_hour_results_are_excluded(self):
        for days in (0,1):
            out=self.run_rows([game(0),game(1,days=days)])
            self.assertEqual(out[-1]['views']['reconstructed_24h']['home']['prior_games'],0)
        first=game(0);first['espn_start_utc']='2024-09-04T18:20:00Z'
        second=game(1,days=1+10/1440)
        self.assertEqual(self.run_rows([first,second])[-1]['views']['reconstructed_24h']['home']['prior_games'],0)

    def test_actual_receipt_availability_and_late_arrival_event_order(self):
        rows=[game(i) for i in range(7)]
        for i,row in enumerate(rows[:6]):
            row['observed_available_at_utc']=(datetime(2024,10,14,tzinfo=timezone.utc)-timedelta(hours=i)).isoformat()
        out=self.run_rows(rows)[-1]['views']['observed_receipt_time']['home']
        self.assertEqual(out['prior_games'],4)
        self.assertEqual([x['espn_game_id'] for x in out['source_history']],
                         [x['espn_game_id'] for x in rows[2:6]])

    def test_other_sport_or_season_cannot_enter_state(self):
        rows=[game(0),game(1)];before=self.run_rows(rows)
        other=game(0,league='NCAAM_D1')
        self.run_rows([other],'NCAAM_D1')
        self.assertEqual(before,self.run_rows(rows))
        with self.assertRaises(ValueError):self.run_rows(rows+[other])
        other=game(2);other['split']='validation'
        with self.assertRaises(ValueError):self.run_rows(rows+[other])
        other=game(2);other['ncaa_start_utc']='2025-09-04T18:00:00Z'
        with self.assertRaises(ValueError):self.run_rows(rows+[other])

    def test_invalid_teams_scores_chronology_and_duplicate_ids_fail(self):
        for key,value in (('home_score',True),('home_score',21),('home_team_id','101'),
                          ('away_team_id','0'),('observed_available_at_utc','2024-09-04T18:00:00Z'),
                          ('espn_start_utc','2024-09-04T18:00:00')):
            row=game(0);row[key]=value
            with self.assertRaises(ValueError):self.run_rows([row])
        with self.assertRaises(ValueError):self.run_rows([game(0),game(0)])
        self.assertEqual(self.run_rows([game(1),game(0)]),self.run_rows([game(0),game(1)]))

    def test_raw_source_adapter_is_immutable_and_rejects_changed_receipt_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixtures.HistoricalD1CrosscheckTests().seed(root)
            report=features.crosscheck.build(root,league='NCAAM_D1',now=fixtures.NOW)
            before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
            rows=features._records(root,'NCAAM_D1','train',fixtures.NOW,report)
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['source_agreement'],report['corroborated_research_only'][0])
            self.assertEqual(before,{p:p.read_bytes() for p in root.rglob('*') if p.is_file()})
            path=next((root/features.history.ROOT/'sources'/'NCAAM_D1'/'train').glob('*.receipt.json'))
            saved=json.loads(path.read_bytes())
            saved['recorded_at_utc']=(fixtures.NOW-timedelta(hours=1)).isoformat()
            path.write_bytes(features.source.canonical(saved))
            with self.assertRaisesRegex(ValueError,'ESPN receipt changed'):
                features._records(root,'NCAAM_D1','train',fixtures.NOW,report)

    def test_build_verifies_seals_and_keeps_all_eligibility_guards(self):
        rows=[game(0),game(1)]
        report={'school_identity_manifest_sha256':'a'*64,'pending_or_quarantined':3}
        with patch.object(features.original_seal,'verify') as old, \
             patch.object(features.independent_seal,'verify') as new, \
             patch.object(features.crosscheck,'build',return_value=report) as check, \
             patch.object(features,'_records',return_value=rows):
            result=features.build()
            old.assert_called_once();new.assert_called_once();check.assert_called_once()
            self.assertEqual(result['corroborated_target_games'],2)
            for key in ('historical_pregame_features_verified','model_training_enabled',
                        'historical_evaluation_enabled','forecasting_enabled','promotion_allowed',
                        'institutional_membership_verified','source_scope_complete'):
                self.assertIs(result[key],False)
            new.side_effect=ValueError('modified');check.reset_mock()
            with self.assertRaises(ValueError):features.build()
            check.assert_not_called()


if __name__=='__main__':unittest.main()
