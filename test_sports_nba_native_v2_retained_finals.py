"""Retained final-source history must preserve conflicts and frozen identities."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_native_v2_retained_finals as history
import test_sports_nba_feature_cohort as fixtures

BASE = Path(__file__).parent
START = fixtures.START


class RetainedFinalHistoryTests(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.CohortTests(); self.case.setUp(); self.case.final()
        self.addCleanup(self.case.doCleanups)
        self.case.nba.update(home_team_id=1610612752, away_team_id=1610612738,
            source_reported_actual_start_utc=(START+timedelta(minutes=5)).isoformat(),
            source_reported_actual_end_utc=(START+timedelta(hours=2)).isoformat())
        self.records = {'0022600000': self.case.frozen}
        self.native = {'capture':'native-early', 'manifest_sha256':'a'*64,
            'manifest':{'recorded_at_utc':self.case.nba_at.isoformat(),
                'requested_date':'2026-10-20','raw_sha256':'b'*64,
                'page_status':'SUPPORTED_REGULATION_FINAL_PAGE_SOURCE_ONLY',
                'supported_final_game_count':1,'parsed_final_page':{'games':[self.case.nba]}}}
        self.provider = {'capture':'provider-early', 'manifest_sha256':'c'*64,
            'manifest':{'recorded_at_utc':self.case.espn_at.isoformat(),
                'quarantined_provider_games':[], 'snapshots':[{'league':'NBA', 'original_response_sha256':'d'*64}]},
            'games':{'401234567':self.case.espn}}

    def build(self, ns=None, es=None):
        return history.classify(self.records, [self.native] if ns is None else ns,
                                [self.provider] if es is None else es, now=self.case.now)

    def test_repeated_identical_sources_count_one_game_and_select_earliest_clock(self):
        later = deepcopy(self.native); later['capture']='native-late'
        later['manifest']['recorded_at_utc']=(self.case.nba_at+timedelta(minutes=20)).isoformat()
        before = deepcopy((self.records,self.native,self.provider,later))
        out = self.build([later,self.native])
        self.assertEqual((out['frozen_feature_observations'],out['corroborated_result_observations']),(1,1))
        self.assertEqual(out['rows'][0]['source_pair']['native']['capture'],'native-early')
        self.assertEqual(out['rows'][0]['native_final_claims'],2)
        self.assertEqual(before,(self.records,self.native,self.provider,later))
        for key in ('official_final_results_verified','prediction_accuracy_computed','settlement_enabled',
                    'historical_evaluation_enabled','model_training_enabled','forecasting_enabled','promotion_allowed'):
            self.assertIs(out[key],False)
        self.assertEqual(out['outcomes_enrolled'],0); self.assertEqual(out['actual_wagers'],0)

    def test_earlier_date_is_retained_when_latest_sources_cover_another_game(self):
        second=deepcopy(self.case.frozen)
        second.update(nba_game_id='0022600001',espn_game_id='401234568',
            nba_saved_start_utc=(START+timedelta(days=1)).isoformat(),
            espn_saved_start_utc=(START+timedelta(days=1)).isoformat())
        self.records['0022600001']=second
        native=deepcopy(self.native); native['capture']='native-next-day'
        native['manifest']['recorded_at_utc']=(self.case.nba_at+timedelta(days=1)).isoformat()
        native['manifest']['requested_date']='2026-10-21'
        game=native['manifest']['parsed_final_page']['games'][0]
        game['nba_game_id']='0022600001'
        for field in ('tipoff_utc','source_reported_actual_start_utc','source_reported_actual_end_utc'):
            game[field]=(datetime.fromisoformat(game[field])+timedelta(days=1)).isoformat()
        provider=deepcopy(self.provider); provider['capture']='provider-next-day'
        provider['manifest']['recorded_at_utc']=(self.case.espn_at+timedelta(days=1)).isoformat()
        row=provider['games'].pop('401234567'); row['espn_game_id']='401234568'
        row['scheduled_start_utc']=(START+timedelta(days=1)).isoformat()
        provider['games']['401234568']=row
        self.case.now+=timedelta(days=1)
        out=self.build([native,self.native],[provider,self.provider])
        self.assertEqual(out['corroborated_result_observations'],2)
        self.assertEqual(out['pending_feature_observations'],0)
        self.assertEqual({r['source_pair']['native']['requested_date'] for r in out['rows']},
                         {'2026-10-20','2026-10-21'})

    def test_earlier_conflicting_native_score_cannot_be_hidden_by_matching_later_pair(self):
        wrong=deepcopy(self.native); wrong['capture']='native-wrong'
        wrong['manifest']['recorded_at_utc']=(self.case.nba_at-timedelta(minutes=10)).isoformat()
        wrong['manifest']['parsed_final_page']['games'][0]['nba_home_score']=103
        out=self.build([self.native,wrong]); row=out['rows'][0]
        self.assertEqual(out['corroborated_result_observations'],0)
        self.assertEqual(row['reason'],'CONFLICTING_RETAINED_NATIVE_FINAL_CLAIMS')
        self.assertTrue(row['quarantined']); self.assertIsNone(row['source_pair'])
        self.assertEqual({x['capture'] for x in row['conflicting_native_sources']},{'native-early','native-wrong'})

    def test_provider_final_conflict_and_original_quarantine_remain_visible(self):
        wrong=deepcopy(self.provider); wrong['capture']='provider-wrong'
        wrong['games']['401234567']['home_score']=103
        row=self.build(es=[wrong,self.provider])['rows'][0]
        self.assertEqual(row['reason'],'CONFLICTING_RETAINED_PROVIDER_FINAL_CLAIMS')
        self.assertEqual(len(row['conflicting_provider_sources']),2)
        self.provider['manifest']['quarantined_provider_games']=[{'league':'NBA','game_id':'401234567'}]
        row=self.build()['rows'][0]
        self.assertEqual(row['reason'],'RETAINED_PROVIDER_IDENTITY_QUARANTINED')
        self.assertEqual(row['provider_quarantine_sources'][0]['capture'],'provider-early')

    def test_later_competing_game_id_cannot_be_hidden_by_earlier_clean_pair(self):
        for source in ('native','provider'):
            with self.subTest(source=source):
                ns=[self.native]; es=[self.provider]
                if source=='native':
                    other=deepcopy(self.native); other['capture']='native-competing-id'
                    other['manifest']['parsed_final_page']['games'][0]['nba_game_id']='0022600001'
                    ns.append(other); expected='RETAINED_NATIVE_GAME_ID_REASSIGNMENT_OR_AMBIGUITY'
                else:
                    other=deepcopy(self.provider); other['capture']='provider-competing-id'
                    row=other['games'].pop('401234567'); row['espn_game_id']='401234568'
                    row['provider_completed']=False; row['state']='pre'
                    row['home_score']=row['away_score']=None
                    other['games']['401234568']=row
                    es.append(other); expected='RETAINED_PROVIDER_GAME_ID_REASSIGNMENT_OR_AMBIGUITY'
                out=self.build(ns,es)
                self.assertEqual(out['corroborated_result_observations'],0)
                self.assertEqual(out['rows'][0]['reason'],expected)
                self.assertTrue(out['rows'][0]['quarantined'])

    def test_provider_before_native_end_is_withheld_until_a_later_identical_observation(self):
        early=deepcopy(self.provider); early['capture']='provider-before-end'
        early['manifest']['recorded_at_utc']=(START+timedelta(hours=1)).isoformat()
        self.assertEqual(self.build(es=[early])['corroborated_result_observations'],0)
        out=self.build(es=[self.provider,early]); row=out['rows'][0]
        self.assertEqual(out['corroborated_result_observations'],1)
        self.assertEqual(row['source_pair']['provider']['capture'],'provider-early')
        self.assertEqual(row['provider_final_claims_before_native_reported_end'],1)

    def test_changed_start_and_cross_source_score_conflict_cannot_attach_result(self):
        self.case.espn['away_score']=98
        row=self.build()['rows'][0]
        self.assertEqual(row['reason'],'CONFLICTING_FINAL_SCORES_NO_GRADE'); self.assertTrue(row['quarantined'])
        self.case.espn['away_score']=99
        self.case.nba['tipoff_utc']=self.case.espn['scheduled_start_utc']=(START+timedelta(minutes=1)).isoformat()
        row=self.build()['rows'][0]
        self.assertEqual(row['reason'],'CURRENT_START_DIFFERS_FROM_FROZEN_START')
        self.assertIsNone(row['result_observation'])

    def test_future_features_stay_pending_and_cannot_reuse_one_provider_identity(self):
        self.records['0022600000']['nba_saved_start_utc']=(self.case.now+timedelta(days=1)).isoformat()
        self.records['0022600000']['espn_saved_start_utc']=(self.case.now+timedelta(days=1)).isoformat()
        out=self.build(ns=[],es=[])
        self.assertEqual(out['awaiting_original_saved_start'],1)
        self.assertEqual(out['rows'][0]['status'],'AWAITING_ORIGINAL_SAVED_START')
        self.records['0022600001']=dict(self.case.frozen,nba_game_id='0022600001')
        with self.assertRaisesRegex(ValueError,'Non-bijective'):self.build()

    def test_future_source_and_naive_clock_are_rejected(self):
        self.native['manifest']['recorded_at_utc']=(self.case.now+timedelta(seconds=1)).isoformat()
        with self.assertRaisesRegex(ValueError,'Future-dated'):self.build()
        with self.assertRaises(ValueError):history.classify({},[],[],now=datetime(2026,10,24))

    def test_inventory_bound_and_symlink_fail_before_source_reads(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); root=Path('captures');(base/root).mkdir()
            (base/root/'20261024T120000000000Z').mkdir()
            with patch.object(history,'MAX_CAPTURES',0):
                with self.assertRaisesRegex(ValueError,'Unbounded'):history._inventory(base,root)
            (base/'linked').symlink_to(base/root,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'Symlink'):history._inventory(base,Path('linked'))

    def test_valid_provider_capture_without_nba_is_replayed_and_explicitly_counted(self):
        with tempfile.TemporaryDirectory() as td:
            source=history.daily.lifecycle.cohort.source
            at=datetime(2026,8,1,tzinfo=timezone.utc)
            source.capture(lambda _:b'{"events":[],"count":0}',base=td,now=at,days_ahead=0)
            with patch.object(history.daily.features,'_reference',return_value={}), \
                 patch.object(history.daily.features,'_existing',return_value={}):
                out=history.build(td,now=at+timedelta(days=1))
            self.assertEqual(out['provider_inventory_receipts_replayed'],1)
            self.assertEqual(out['provider_receipts_without_nba'],1)
            self.assertEqual(out['corroborated_result_observations'],0)


if __name__ == '__main__':unittest.main()
