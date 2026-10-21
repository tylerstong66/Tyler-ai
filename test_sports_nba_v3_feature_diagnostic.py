"""Actual saved source comparison retains a start conflict and never grades."""
from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

import sports_nba_v3_feature_diagnostic as diagnostic

SOURCE = Path(__file__).parent
CAPTURE = '20261021T100537057931Z'
NOW = datetime.now(timezone.utc)


class V3FeatureDiagnosticTests(unittest.TestCase):
    def test_actual_sources_preserve_exact_start_conflict_and_no_grade(self):
        report = diagnostic.build(SOURCE, capture=CAPTURE,
                                  provider_capture='20261021T100530748795Z', now=NOW)
        by_id = {row['nba_game_id']: row for row in report['rows']}
        for identifier in ('0022600001', '0022600002'):
            row = by_id[identifier]
            self.assertEqual(row['status'], 'CORROBORATED_RESULT_OBSERVATION_ONLY')
            self.assertIsNotNone(row['result_observation'])
        conflict = by_id['0022600003']
        self.assertEqual(conflict['reason'], 'NATIVE_DAILY_FINAL_STARTS_NOT_EXACT')
        self.assertTrue(conflict['identity_quarantined'])
        self.assertIsNone(conflict['result_observation'])
        self.assertEqual(conflict['espn_saved_start_drift_minutes'], 20)
        self.assertEqual(conflict['nba_saved_start_drift_minutes'], 0)
        self.assertEqual(report['corroborated_result_observations'], 2)
        self.assertEqual(report['outcomes_enrolled'], 0)
        self.assertTrue(report['diagnostic_only']); self.assertTrue(report['NO_BET'])
        self.assertEqual(report['actual_wagers'], 0)
        for key in ('existing_native_v2_lifecycle_changed', 'settlement_enabled',
                    'official_final_results_verified', 'independent_final_agreement_verified',
                    'prediction_accuracy_computed', 'forecasting_enabled', 'model_training_enabled', 'promotion_allowed'):
            self.assertIs(report[key], False)

    def test_naive_clock_fails_before_source_inspection(self):
        with patch.object(diagnostic.reader, 'inspect') as inspect:
            with self.assertRaisesRegex(ValueError, 'Aware'):
                diagnostic.build(SOURCE, capture=CAPTURE, now=NOW.replace(tzinfo=None))
            inspect.assert_not_called()


if __name__ == '__main__': unittest.main()
