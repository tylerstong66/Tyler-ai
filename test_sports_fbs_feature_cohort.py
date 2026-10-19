from copy import deepcopy
from datetime import timedelta
from pathlib import Path
import json
import tempfile
import unittest

import sports_fbs_feature_cohort as cohort
import test_sports_fbs_pregame_features as fixtures

NOW = fixtures.NOW
START = fixtures.fixtures.AT.replace(hour=17, minute=0)


class FbsCohortTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); self.base = Path(temp.name)
        seed = fixtures.FbsFeatureTests(); _, self.stamp = seed.seed(self.base); self.addCleanup(seed.doCleanups)
        cohort.features.inspect(self.base, now=NOW, collect=True)
        self.path = next((self.base/cohort.features.ROOT).glob('*.json')); self.before = self.path.read_bytes()
        row = json.loads(self.before)['record']; self.records = {row['espn_game_id']: row}
        self.snapshots = {self.stamp: cohort.features._snapshot(self.base, self.stamp)}
        self.current = deepcopy(self.snapshots[self.stamp])
        self.dataset = {'rows': [], 'quarantined': []}
        self.now = NOW

    def classify(self):
        return cohort.classify(self.records, self.snapshots, self.current, self.dataset, now=self.now)

    def final(self):
        self.now = START+timedelta(hours=4)
        at = (START+timedelta(hours=3)).isoformat()
        self.dataset['rows'] = [{'league': 'NCAAF_FBS', 'espn_game_id': '401100001', 'ncaa_game_id': '654321',
            'espn_home_team_id': '202', 'espn_away_team_id': '101', 'ncaa_home_school': 'Tulsa', 'ncaa_away_school': 'Rice',
            'scheduled_start_utc': START.isoformat(), 'ncaa_scheduled_start_utc': START.isoformat(),
            'ncaa_source_observed_at_utc': at, 'espn_source_observed_at_utc': at,
            'result_observation_chronology_verified': True, 'source_archive_sha256_verified': True,
            'source_agreement': 'NCAA_AND_ESPN_REPORTED_SAME_FINAL',
            'independently_certified_official_final': False, 'eligible_for_historical_evaluation': False, 'home_score': 28, 'away_score': 21}]

    def test_real_original_features_replay_and_no_prediction_accuracy_is_computed(self):
        result = cohort.build(self.base, now=NOW)
        self.assertEqual(result['frozen_feature_observations'], 1)
        self.assertEqual(result['corroborated_result_observations'], 0)
        self.assertEqual(self.path.read_bytes(), self.before)
        self.assertFalse(result['prediction_accuracy_computed']); self.assertTrue(result['NO_BET'])

    def test_stale_sources_after_start_still_do_not_prove_a_result(self):
        self.now = START+timedelta(days=1)
        report = self.classify()
        self.assertTrue(all(report['source_older_than_12_hours'].values()))
        self.assertEqual(report['rows'][0]['status'], 'SAVED_START_REACHED_WITHOUT_CORROBORATED_RESULT')
        self.assertEqual(report['corroborated_result_observations'], 0)

    def test_matching_final_observation_remains_separate_from_prediction_grading(self):
        self.final(); result = self.classify()
        self.assertEqual(result['corroborated_result_observations'], 1)
        self.assertEqual(result['rows'][0]['result_observation']['home_score'], 28)
        self.assertFalse(result['historical_evaluation_enabled']); self.assertFalse(result['forecasting_enabled'])

    def test_older_agreement_is_withheld_after_dataset_quarantine(self):
        self.final(); self.dataset['quarantined'] = [{'league': 'NCAAF_FBS', 'espn_game_id': '401100001', 'reasons': ['RESULT_OR_IDENTITY_CHANGED_ACROSS_CAPTURES']}]
        result = self.classify()
        self.assertEqual(result['corroborated_result_observations'], 0)
        self.assertEqual(result['rows'][0]['reason'], 'RESULT_DATASET_QUARANTINED')

    def test_later_absence_does_not_cancel_a_preserved_agreeing_result(self):
        self.final(); self.current['rows']['espn'] = {}; self.current['rows']['ncaa'] = {}
        result = self.classify()
        self.assertEqual(result['corroborated_result_observations'], 1)
        self.assertFalse(result['rows'][0]['espn_present_in_latest_source_pair'])

    def test_new_team_identity_or_wrong_result_cannot_attach_to_original_feature(self):
        for kind in ('current_id', 'current_name', 'result_id'):
            with self.subTest(kind=kind):
                self.current = deepcopy(self.snapshots[self.stamp]); self.final()
                if kind == 'current_id': self.current['rows']['espn']['401100001']['home_team_id'] = '999'
                elif kind == 'current_name': self.current['rows']['ncaa']['654321']['home_name'] = 'Other School'
                else: self.dataset['rows'][0]['ncaa_game_id'] = '654322'
                self.assertEqual(self.classify()['corroborated_result_observations'], 0)
                self.assertTrue(self.classify()['rows'][0]['identity_quarantined'])

    def test_shifted_original_and_current_starts_are_not_rewritten(self):
        self.final(); later = START+timedelta(hours=1)
        self.current['rows']['ncaa']['654321']['source_start_time_epoch'] = str(int(later.timestamp()))
        self.current['rows']['espn']['401100001']['scheduled_start_utc'] = later.isoformat()
        for key in ('scheduled_start_utc', 'ncaa_scheduled_start_utc'): self.dataset['rows'][0][key] = later.isoformat()
        report = self.classify(); row = report['rows'][0]
        self.assertEqual(report['corroborated_result_observations'], 1)
        self.assertEqual(row['ncaa_saved_start_drift_minutes'], 60)
        self.assertEqual(row['original_ncaa_saved_start_utc'], START.isoformat())
        self.assertEqual(self.path.read_bytes(), self.before)

    def test_final_observed_before_original_start_or_in_future_cannot_be_used(self):
        self.final(); self.dataset['rows'][0]['espn_source_observed_at_utc'] = (START-timedelta(seconds=1)).isoformat()
        self.assertEqual(self.classify()['corroborated_result_observations'], 0)
        self.dataset['rows'][0]['espn_source_observed_at_utc'] = (self.now+timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError): self.classify()

    def test_duplicate_results_and_future_current_source_fail_closed(self):
        self.final(); self.dataset['rows'].append(deepcopy(self.dataset['rows'][0]))
        with self.assertRaises(ValueError): self.classify()
        self.dataset['rows'] = []
        self.current['source_manifests']['ncaa']['recorded_at_utc'] = (self.now+timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError): self.classify()

    def test_malformed_or_unreplayed_final_cannot_be_presented_as_result_observation(self):
        for key,value in [('home_score', True),('home_score',-1),('away_score',28),
                          ('source_archive_sha256_verified',1),('source_agreement','UNVERIFIED'),
                          ('eligible_for_historical_evaluation',True),('independently_certified_official_final',True)]:
            self.final();self.dataset['rows'][0][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.classify()


if __name__ == '__main__': unittest.main()
