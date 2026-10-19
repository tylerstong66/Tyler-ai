from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_feature_cohort as cohort
import test_sports_nba_pregame_features as fixtures

NOW = fixtures.NOW
START = datetime(2026, 10, 20, 19, tzinfo=timezone.utc)


class CohortTests(unittest.TestCase):
    def setUp(self):
        self.frozen = {'nba_game_id': '0022600000', 'espn_game_id': '401234567',
            'frozen_at_utc': NOW.isoformat(), 'nba_saved_start_utc': START.isoformat(),
            'espn_saved_start_utc': START.isoformat(), 'home_team_id': '18', 'away_team_id': '2',
            'reference_features': {'home': {'team_tricode': 'NYK'}, 'away': {'team_tricode': 'BOS'}}}
        self.nba = {'nba_game_id': '0022600000', 'kind': 'regular', 'home_tricode': 'NYK',
            'away_tricode': 'BOS', 'tipoff_utc': START.isoformat(), 'nba_status': 1,
            'nba_postponed_status': None, 'nba_home_score': None, 'nba_away_score': None}
        self.espn = {'espn_game_id': '401234567', 'home_team_id': '18', 'away_team_id': '2',
            'home_tricode': 'NYK', 'away_tricode': 'BOS', 'scheduled_start_utc': START.isoformat(),
            'state': 'pre', 'provider_completed': False, 'season_stage': 2,
            'home_score': None, 'away_score': None}
        self.nba_at = self.espn_at = NOW - timedelta(hours=1)
        self.now = NOW

    def build(self, official=None, provider=None, records=None):
        return cohort.classify(records if records is not None else {'0022600000': self.frozen},
            official if official is not None else [self.nba],
            provider if provider is not None else {'401234567': self.espn},
            nba_observed_at=self.nba_at.isoformat(), espn_observed_at=self.espn_at.isoformat(), now=self.now)

    def final(self):
        self.now = START + timedelta(hours=4)
        self.nba_at = START + timedelta(hours=3)
        self.espn_at = START + timedelta(hours=3, minutes=10)
        self.nba.update(nba_status=3, nba_home_score=101, nba_away_score=99)
        self.espn.update(state='post', provider_completed=True, home_score=101, away_score=99)

    def test_original_source_build_and_read_only_feature_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            fixtures.slot_fixtures.NbaFutureSlotTests().capture(base)
            with patch.object(cohort.features, '_reference', return_value=fixtures.reference()):
                cohort.features.collect(base, now=NOW)
                path = next((base/cohort.features.ROOT).glob('*.json')); before = path.read_bytes()
                result = cohort.build(base, now=NOW)
                self.assertEqual(result['frozen_feature_observations'], 1)
                self.assertEqual(result['corroborated_result_observations'], 0)
                self.assertEqual(result['rows'][0]['reason'], 'BOTH_SOURCES_NOT_FINAL')
                self.assertEqual(path.read_bytes(), before)
                self.assertFalse(result['prediction_accuracy_computed'])
                self.assertTrue(result['NO_BET'])

    def test_corrob_result_is_not_prediction_grading(self):
        self.final(); result = self.build(); row = result['rows'][0]
        self.assertEqual(result['corroborated_result_observations'], 1)
        self.assertEqual(row['result_observation']['home_score'], 101)
        self.assertEqual(row['status'], 'CORROBORATED_RESULT_OBSERVATION_ONLY')
        for key in ('prediction_accuracy_computed', 'historical_evaluation_enabled',
                    'model_training_enabled', 'forecasting_enabled', 'promotion_allowed'):
            self.assertIs(result[key], False)

    def test_one_final_or_score_conflict_stays_pending(self):
        self.final(); self.espn['provider_completed'] = False
        self.assertEqual(self.build()['corroborated_result_observations'], 0)
        self.espn['provider_completed'] = True; self.espn['away_score'] = 98
        row = self.build()['rows'][0]
        self.assertEqual(row['reason'], 'CONFLICTING_FINAL_SCORES_NO_GRADE')
        self.assertIsNone(row['result_observation'])

    def test_stale_pregame_sources_after_saved_start_do_not_prove_live_or_final(self):
        self.now = START + timedelta(days=1)
        result = self.build()
        self.assertTrue(all(result['source_older_than_12_hours'].values()))
        self.assertEqual(result['rows'][0]['status'], 'SAVED_START_REACHED_WITHOUT_CORROBORATED_RESULT')
        self.assertEqual(result['corroborated_result_observations'], 0)

    def test_final_observed_before_saved_start_is_not_accepted(self):
        self.final(); self.nba_at = self.espn_at = START - timedelta(seconds=1)
        self.assertEqual(self.build()['corroborated_result_observations'], 0)

    def test_original_and_latest_start_drifts_are_retained_with_final(self):
        self.final()
        self.nba['tipoff_utc'] = self.espn['scheduled_start_utc'] = (START + timedelta(hours=2)).isoformat()
        result = self.build(); row = result['rows'][0]
        self.assertEqual(result['corroborated_result_observations'], 1)
        self.assertEqual(result['schedule_drift_observed'], 1)
        self.assertEqual(row['nba_saved_start_drift_minutes'], 120)
        self.assertEqual(row['original_nba_saved_start_utc'], START.isoformat())

    def test_earlier_rescheduled_final_before_original_start_remains_quarantined(self):
        self.final()
        self.nba['tipoff_utc'] = self.espn['scheduled_start_utc'] = (START-timedelta(hours=4)).isoformat()
        self.nba_at = self.espn_at = START-timedelta(hours=1)
        row = self.build()['rows'][0]
        self.assertEqual(row['reason'], 'FINAL_NOT_OBSERVED_AFTER_ORIGINAL_AND_LATEST_STARTS')
        self.assertIsNone(row['result_observation'])

    def test_frozen_team_id_or_orientation_change_cannot_attach_final(self):
        self.final()
        for kind in ('espn_id', 'both_abbreviations'):
            with self.subTest(kind=kind):
                n, e = deepcopy(self.nba), deepcopy(self.espn)
                if kind == 'espn_id': e['home_team_id'] = '99'
                else:
                    n['home_tricode'], n['away_tricode'] = 'BOS', 'NYK'
                    e['home_tricode'], e['away_tricode'] = 'BOS', 'NYK'
                result = self.build(official=[n], provider={'401234567': e})
                self.assertEqual(result['identity_quarantined'], 1)
                self.assertEqual(result['corroborated_result_observations'], 0)

    def test_missing_game_never_implies_cancellation_or_substitute_identity(self):
        self.final(); self.nba['nba_game_id'] = '0022600001'
        row = self.build()['rows'][0]
        self.assertEqual(row['reason'], 'NBA_GAME_NOT_PRESENT_IN_LATEST_SOURCE')
        self.assertIsNone(row['result_observation'])
        self.nba['nba_game_id'] = '0022600000'
        self.assertEqual(self.build(provider={})['rows'][0]['reason'], 'ESPN_GAME_NOT_PRESENT_IN_LATEST_SOURCE')

    def test_source_disagrees_on_start_or_has_ambiguous_nearby_repeat(self):
        self.espn['scheduled_start_utc'] = (START+timedelta(hours=2)).isoformat()
        row = self.build()['rows'][0]
        self.assertEqual(row['espn_saved_start_drift_minutes'], 120)
        self.assertTrue(row['identity_quarantined'])
        self.espn['scheduled_start_utc'] = START.isoformat()
        other = dict(self.nba, nba_game_id='0022600001', tipoff_utc=(START+timedelta(days=1)).isoformat())
        self.assertTrue(self.build(official=[self.nba, other])['rows'][0]['identity_quarantined'])

    def test_invalid_clocks_duplicate_source_or_cross_cohort_ids_fail_closed(self):
        with self.assertRaises(ValueError): self.build(official=[self.nba, self.nba])
        duplicate = dict(self.frozen, nba_game_id='0022600001')
        with self.assertRaises(ValueError): self.build(records={'0022600000': self.frozen, '0022600001': duplicate})
        self.nba_at = NOW + timedelta(seconds=1)
        with self.assertRaises(ValueError): self.build()
        with self.assertRaises(ValueError): cohort.build(now=datetime(2026, 10, 19))

    def test_source_corruption_is_not_silently_treated_as_missing(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); fixtures.slot_fixtures.NbaFutureSlotTests().capture(base)
            with patch.object(cohort.features, '_reference', return_value=fixtures.reference()):
                cohort.features.collect(base, now=NOW)
                path = next((base/cohort.source.ROOT/'captures').glob('*/NBA_*.json.gz'))
                path.write_bytes(b'corrupt')
                with self.assertRaises(ValueError): cohort.build(base, now=NOW)

    def test_latest_provider_is_not_silently_replaced_by_old_linked_provider(self):
        import test_sports_nba_official_schedule_audit as source_fixtures
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); fixtures.slot_fixtures.NbaFutureSlotTests().capture(base)
            with patch.object(cohort.features, '_reference', return_value=fixtures.reference()):
                cohort.features.collect(base, now=NOW)
                def fetch(url):
                    event = source_fixtures.espn_event()
                    event['date'] = (START+timedelta(hours=2)).isoformat()
                    events = [event] if 'basketball/nba' in url and 'dates=20261020' in url else []
                    return json.dumps({'events': events, 'count': len(events)}).encode()
                cohort.source.capture(fetch, base=base, now=NOW+timedelta(hours=1), days_ahead=3)
                result = cohort.build(base, now=NOW+timedelta(hours=2))
                self.assertEqual(result['rows'][0]['espn_saved_start_drift_minutes'], 120)
                self.assertTrue(result['source_provenance']['provider_independent_of_nba_linked_snapshot'])
                self.assertEqual(result['source_age_hours']['espn'], 1)
                self.assertEqual(result['source_age_hours']['nba'], 2)
                self.assertEqual(result['corroborated_result_observations'], 0)


if __name__ == '__main__': unittest.main()
