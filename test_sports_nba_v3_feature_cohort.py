"""Version-pinned original v3 source comparison; no forecast or grade creation."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_v3_feature_cohort as v3
import sports_nba_postgame_observation_v2 as v2

BASE = Path(__file__).parent


class V3FrozenSourceAuditTests(unittest.TestCase):
    def test_original_v3_sources_preserve_conflict_and_do_not_grade_or_rewrite(self):
        files = [p for p in (BASE/v3.post.ROOT).rglob('*') if p.is_file()]
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        with patch('requests.get', side_effect=AssertionError('Unexpected network')):
            report = v3.build(BASE, capture='20261021T195302172053Z',
                              provider_capture='20261021T195240786324Z')
        self.assertEqual(report['native_receipt_schema'], v3.post.PROTOCOL.schema)
        self.assertEqual(report['schema'], 'tyler-nba-native-final-break-frozen-feature-source-audit-v3')
        self.assertEqual(report['corroborated_result_observations'], 2)
        rows = {r['nba_game_id']: r for r in report['rows']}
        self.assertEqual(rows['0022600003']['reason'], 'NATIVE_DAILY_FINAL_STARTS_NOT_EXACT')
        self.assertTrue(rows['0022600003']['identity_quarantined'])
        self.assertIsNone(rows['0022600003']['result_observation'])
        for key in ('settlement_enabled', 'forecasting_enabled', 'model_training_enabled',
                    'historical_evaluation_enabled', 'promotion_allowed',
                    'prediction_accuracy_computed', 'official_final_results_verified',
                    'independent_final_agreement_verified', 'source_scope_complete'):
            self.assertIs(report[key], False)
        self.assertTrue(report['NO_BET'])
        self.assertEqual(report['actual_wagers'], 0)
        self.assertEqual(report['outcomes_enrolled'], 0)
        self.assertTrue(report['source_provenance']['provider_original_response_sha256'])
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in files})

    def test_missing_v3_does_not_fall_back_to_v2_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base/v2.ROOT/'20261021T195302172053Z').mkdir(parents=True)
            (base/v2.ROOT/'20261021T195302172053Z'/'manifest.json').write_text('{}')
            with (patch.object(v3.native.cohort.features, '_reference', return_value={}),
                  patch.object(v3.native.cohort.features, '_existing', return_value={})):
                report = v3.build(base)
            self.assertEqual(report['source_status'], 'NO_RETAINED_NATIVE_POSTGAME_RECEIPT')
            self.assertEqual(report['corroborated_result_observations'], 0)
            self.assertEqual(report['outcomes_enrolled'], 0)

    def test_bad_capture_and_future_clock_fail_before_comparison(self):
        for stamp in ('../escape', '/absolute', True):
            with self.subTest(stamp=stamp), patch.object(v3.native.cohort.features, '_reference') as ref:
                with self.assertRaises(ValueError):
                    v3.build(BASE, capture=stamp)
                ref.assert_not_called()
        with self.assertRaises(ValueError):
            v3.build(BASE, now=datetime.now(timezone.utc).replace(tzinfo=None))

    def test_changed_original_v3_manifest_is_rejected(self):
        import shutil
        stamp = '20261021T195302172053Z'
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            shutil.copytree(BASE/v3.post.ROOT/stamp, base/v3.post.ROOT/stamp)
            path = base/v3.post.ROOT/stamp/'manifest.json'
            path.write_bytes(path.read_bytes()+b'\n')
            with (patch.object(v3.native.cohort.features, '_reference', return_value={}),
                  patch.object(v3.native.cohort.features, '_existing', return_value={})):
                with self.assertRaises(ValueError):
                    v3.build(base, capture=stamp)


if __name__ == '__main__': unittest.main()
