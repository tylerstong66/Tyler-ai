"""Synthetic normalized cases for a read-only daily source lifecycle."""
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
import unittest
from unittest.mock import patch
import sports_nba_native_feature_cohort as native
import test_sports_nba_feature_cohort as fixtures


class NativeCohortTests(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.CohortTests()
        self.case.setUp(); self.case.final()
        self.case.nba['source_reported_actual_end_utc'] = (fixtures.START+timedelta(hours=2)).isoformat()
        self.records = {'0022600000': self.case.frozen}
        self.provider = {'401234567': self.case.espn}

    def manifest(self):
        return {'recorded_at_utc': self.case.nba_at.isoformat(),
                'parsed_final_page': {'games': [self.case.nba]},
                'requested_date': '2026-10-20', 'raw_sha256': 'synthetic-unit-body',
                'page_status': 'SUPPORTED_REGULATION_FINAL_PAGE_SOURCE_ONLY',
                'supported_final_game_count': 1}

    def build(self, manifest=None):
        return native.classify(self.records, manifest or self.manifest(), self.provider,
                provider_observed_at=self.case.espn_at.isoformat(), now=self.case.now)

    def test_exact_final_sources_attach_observation_without_grading(self):
        result = self.build()
        self.assertEqual(result['corroborated_result_observations'], 1)
        self.assertEqual(result['rows'][0]['result_observation']['home_score'], 101)
        for key in ('prediction_accuracy_computed', 'forecasting_enabled', 'model_training_enabled',
                    'historical_evaluation_enabled', 'promotion_allowed', 'settlement_enabled',
                    'feature_backfill_allowed', 'official_final_results_verified',
                    'source_scope_complete', 'receipt_clock_independently_attested'):
            self.assertIs(result[key], False)
        self.assertEqual(result['outcomes_enrolled'], 0)
        self.assertEqual(result['actual_wagers'], 0)
        self.assertIs(result['NO_BET'], True)

    def test_small_current_tipoff_disagreement_is_withheld_and_quarantined(self):
        self.case.espn['scheduled_start_utc'] = (fixtures.START+timedelta(minutes=1)).isoformat()
        result = self.build()
        self.assertEqual(result['corroborated_result_observations'], 0)
        self.assertEqual(result['rows'][0]['reason'], 'NATIVE_DAILY_FINAL_STARTS_NOT_EXACT')
        self.assertEqual(result['identity_quarantined'], 1)

    def test_provider_receipt_before_native_actual_end_is_not_final_proof(self):
        self.case.espn_at = fixtures.START+timedelta(minutes=110)
        result = self.build()
        self.assertEqual(result['corroborated_result_observations'], 0)
        self.assertEqual(result['rows'][0]['reason'], 'FINAL_SOURCE_OBSERVED_BEFORE_NATIVE_REPORTED_END')

    def test_independent_score_and_frozen_team_conflicts_remain_pending(self):
        self.case.espn['away_score'] = 98
        self.assertEqual(self.build()['corroborated_result_observations'], 0)
        self.case.espn['away_score'] = 99
        self.case.espn['home_team_id'] = '99'
        self.assertEqual(self.build()['corroborated_result_observations'], 0)

    def test_empty_or_unsupported_page_does_not_rewrite_old_record_or_imply_cancellation(self):
        before = deepcopy(self.records)
        for status in ('EMPTY_DAY_NO_FINAL_EVIDENCE', 'UNSUPPORTED_OR_NOT_COMPLETE_FINAL_PAGE'):
            manifest = self.manifest(); manifest.update(requested_date='2026-10-19',
                        page_status=status, supported_final_game_count=0, parsed_final_page=None)
            result = self.build(manifest)
            self.assertEqual(result['corroborated_result_observations'], 0)
            self.assertEqual(result['frozen_games_outside_daily_source_date'], 1)
            self.assertEqual(result['rows'][0]['reason'], 'OUTSIDE_REQUESTED_DAILY_SOURCE_DATE')
        self.assertEqual(self.records, before)

    def test_future_source_observation_is_rejected(self):
        self.case.espn_at = self.case.now+timedelta(seconds=1)
        with self.assertRaises(ValueError): self.build()

    def test_missing_native_capture_remains_explicit_after_feature_validation(self):
        with (patch.object(native.cohort.features, '_reference', return_value={}),
              patch.object(native.cohort.features, '_existing', return_value=self.records),
              patch.object(native.post, 'replay_all'), patch.object(Path, 'glob', return_value=iter([]))):
            report = native.build(now=self.case.now)
        self.assertEqual(report['source_status'], 'NO_RETAINED_NATIVE_POSTGAME_RECEIPT')
        self.assertEqual(report['corroborated_result_observations'], 0)
        self.assertFalse(report['forecasting_enabled'])

    def test_actual_saved_sources_replay_without_grading(self):
        report = native.build(Path(__file__).parent)
        self.assertIs(report['forecasting_enabled'], False)
        self.assertEqual(report['outcomes_enrolled'], 0)


if __name__ == '__main__': unittest.main()
