"""New native-v2 features use their own replay, with legacy cohorts unchanged."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_native_v2_final_v3_cohort as newer
import sports_nba_v3_feature_cohort as legacy

BASE = Path(__file__).parent
CAPTURE = '20261024T163520206576Z'
PROVIDER = '20261024T163445111625Z'


class NativeV2FinalV3Tests(unittest.TestCase):
    def test_original_newer_cohort_matches_twelve_sources_without_pooling_or_writes(self):
        paths = sorted((BASE/newer.features.ROOT).glob('*.json'))
        old_paths = sorted((BASE/legacy.native.cohort.features.ROOT).glob('*.json'))
        originals = paths + old_paths
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in originals}
        with patch('requests.get', side_effect=AssertionError('Unexpected network')):
            report = newer.build(BASE, capture=CAPTURE, provider_capture=PROVIDER)
            old = legacy.build(BASE, capture=CAPTURE, provider_capture=PROVIDER)
        self.assertEqual(report['frozen_feature_observations'], len(paths))
        self.assertEqual(old['frozen_feature_observations'], len(old_paths))
        self.assertEqual(report['corroborated_result_observations'], 12)
        self.assertEqual(old['corroborated_result_observations'], 0)
        self.assertEqual(report['feature_protocol_sha256'], newer.features.PROTOCOL_SHA256)
        self.assertEqual(report['frozen_feature_root'], newer.features.ROOT.as_posix())
        self.assertTrue(report['cross_version_counts_must_not_be_pooled'])
        self.assertEqual(report['feature_cohort'], 'NATIVE_DAILY_V2_ONLY')
        for key in ('settlement_enabled', 'forecasting_enabled', 'model_training_enabled',
                    'historical_evaluation_enabled', 'promotion_allowed', 'feature_backfill_allowed',
                    'prediction_accuracy_computed', 'official_final_results_verified',
                    'independent_final_agreement_verified', 'source_scope_complete'):
            self.assertIs(report[key], False)
        self.assertEqual(report['outcomes_enrolled'], 0)
        self.assertIs(report['NO_BET'], True)
        self.assertEqual(report['actual_wagers'], 0)
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in originals})

    def test_missing_new_final_source_never_uses_legacy_features(self):
        with tempfile.TemporaryDirectory() as td, \
             patch.object(newer.features, '_reference', return_value={}), \
             patch.object(newer.features, '_existing', return_value={'new': {}}), \
             patch.object(legacy.native.cohort.features, '_existing', side_effect=AssertionError('Legacy feature fallback')):
            report = newer.build(td)
        self.assertEqual(report['frozen_feature_observations'], 1)
        self.assertEqual(report['source_status'], 'NO_RETAINED_NATIVE_POSTGAME_RECEIPT')
        self.assertEqual(report['corroborated_result_observations'], 0)
        self.assertEqual(report['outcomes_enrolled'], 0)

    def test_legacy_default_never_reads_newer_feature_root(self):
        with tempfile.TemporaryDirectory() as td, \
             patch.object(legacy.native.cohort.features, '_reference', return_value={}), \
             patch.object(legacy.native.cohort.features, '_existing', return_value={}), \
             patch.object(newer.features, '_existing', side_effect=AssertionError('New cohort leaked into legacy')):
            report = legacy.build(td)
        self.assertEqual(report['frozen_feature_observations'], 0)

    def test_corrupt_newer_record_fails_before_any_final_comparison(self):
        original = next((BASE/newer.features.ROOT).glob('*.json'))
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)/newer.features.ROOT/original.name
            target.parent.mkdir(parents=True); shutil.copyfile(original, target)
            target.write_bytes(target.read_bytes()+b' ')
            before = target.read_bytes()
            with patch.object(newer.features, '_reference', return_value={}), \
                 patch.object(newer.post, 'replay_all') as replay:
                with self.assertRaisesRegex(ValueError, 'digest/encoding'):
                    newer.build(td)
            replay.assert_not_called()
            self.assertEqual(target.read_bytes(), before)

    def test_invalid_pins_and_naive_clock_reject_before_feature_reads(self):
        for kwargs in ({'capture': '../escape'}, {'provider_capture': '../escape'},
                       {'now': datetime.now(timezone.utc).replace(tzinfo=None)}):
            with self.subTest(kwargs=kwargs), patch.object(newer.features, '_reference') as reference:
                with self.assertRaises(ValueError): newer.build(BASE, **kwargs)
                reference.assert_not_called()


if __name__ == '__main__': unittest.main()
