import copy
from datetime import datetime, timezone
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_final_page_reference as reference

SOURCE = Path(__file__).parent
CLOCK = datetime(2026, 10, 20, 12, 9, 26, 334105, tzinfo=timezone.utc)


class ReferenceAgreementTests(unittest.TestCase):
    def test_original_two_source_reference_agreement_is_not_prospective_evaluation(self):
        report = reference.build(SOURCE)
        self.assertEqual(report['two_source_final_agreements'], 15)
        self.assertEqual(report['pending_or_quarantined'], 0)
        self.assertEqual(report['new_outcomes_enrolled'], 0)
        self.assertEqual(report['espn_source']['original_body_sha256'],
                         'dd1275f153647d7dcd766042201b7acb600a5aecef0aba2131d445cdb3af8278')
        self.assertTrue(report['NO_BET']); self.assertEqual(report['actual_wagers'], 0)
        for key in ('historical_evaluation_enabled', 'model_training_enabled', 'forecasting_enabled',
                    'promotion_allowed', 'settlement_enabled', 'available_at_historical_pregame_freeze',
                    'current_season_results_verified', 'fresh_source_observation',
                    'independent_official_final_certification_complete'):
            self.assertIs(report[key], False)
        for row in report['corroborated_research_only']:
            self.assertEqual(row['corroboration_available_at_utc'], CLOCK.isoformat())
            self.assertIs(row['pregame_feature_chronology_verified'], False)

    def test_original_provider_receipt_cannot_be_available_before_its_observation(self):
        before = datetime(2026, 10, 18, 17, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, 'future observation'):
            reference.provider_reference(SOURCE, observed_by=before)
        for invalid in (None, CLOCK.replace(tzinfo=None), CLOCK.isoformat()):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'Aware reference'):
                reference.provider_reference(SOURCE, observed_by=invalid)

    def test_changed_sealed_original_provider_bytes_reject(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(SOURCE/reference.history.ROOT, root/reference.history.ROOT)
            target = root/reference.history.ROOT/'sources/NBA/validation/2026-04-10.json.gz'
            target.write_bytes(target.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError, 'content index differs'):
                reference.provider_reference(root, observed_by=CLOCK)

    def test_conflicting_score_is_quarantined_without_selecting_another_identity(self):
        provider, proof = reference.provider_reference(SOURCE, observed_by=CLOCK)
        key = sorted(provider)[0]; changed = copy.deepcopy(provider)
        changed[key]['home_score'] += 1
        with patch.object(reference, 'provider_reference', return_value=(changed, proof)):
            report = reference.build(SOURCE)
        self.assertEqual(report['two_source_final_agreements'], 14)
        self.assertEqual(report['pending_or_quarantined'], 1)
        self.assertEqual(report['pending'][0]['espn_game_id'], key)
        self.assertEqual(report['pending'][0]['reason'], 'CONFLICTING_FINAL_SCORES_NO_GRADE')

    def test_team_mismatch_cannot_be_resolved_using_the_matching_scores(self):
        provider, proof = reference.provider_reference(SOURCE, observed_by=CLOCK)
        key = sorted(provider)[0]; changed = copy.deepcopy(provider)
        changed[key]['home_tricode'] = 'LAL'
        with patch.object(reference, 'provider_reference', return_value=(changed, proof)):
            report = reference.build(SOURCE)
        self.assertEqual(report['two_source_final_agreements'], 14)
        self.assertEqual(report['pending_or_quarantined'], 1)
        self.assertEqual(report['pending'][0]['espn_game_id'], key)
        self.assertEqual(report['pending'][0]['reason'], 'NO_INDEPENDENT_NBA_GAME_FOUND')


if __name__ == '__main__': unittest.main()
