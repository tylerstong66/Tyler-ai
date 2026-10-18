"""Multiple independently replayed captures must not inflate unique game counts."""
import tempfile
import json
import sports_ncaa_espn_identity as identity
import unittest
from datetime import timedelta
from pathlib import Path
from test_sports_college_final_receipts import FinalReceiptTests
from test_sports_ncaa_espn_identity import AT
import sports_college_result_dataset as dataset


class ResultDatasetTests(unittest.TestCase):
    def seed(self, root, **kwargs):
        return FinalReceiptTests().seed(root, **kwargs)[0]

    def test_repeated_verified_game_is_one_row_with_earliest_availability(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = self.seed(root)
            second = self.seed(root, at=AT + timedelta(hours=9))
            out = dataset.assemble(root, [second, first])
            self.assertEqual(out['unique_corroborated_games'], 1)
            self.assertEqual(out['rows'][0]['verified_capture_observations'], 2)
            self.assertEqual(out['rows'][0]['corroboration_available_at_utc'],
                             (AT + timedelta(hours=8)).isoformat())
            self.assertEqual(out, dataset.assemble(root, [first, second]))
            self.assertFalse(out['historical_evaluation_enabled'])
            self.assertFalse(out['model_training_enabled'])
            self.assertEqual(out['actual_wagers'], 0)

    def test_both_sources_changing_final_does_not_silently_replace_label(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); first = self.seed(root)
            second = self.seed(root, at=AT + timedelta(hours=9), score=35)
            out = dataset.assemble(root, [first, second])
            self.assertEqual(out['unique_corroborated_games'], 0)
            self.assertIn('RESULT_OR_IDENTITY_CHANGED_ACROSS_CAPTURES',
                          out['quarantined'][0]['reasons'])

    def test_later_source_disagreement_quarantines_previous_agreement(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); first = self.seed(root)
            second = self.seed(root, at=AT + timedelta(hours=9), conflict=True)
            out = dataset.assemble(root, [first, second])
            self.assertEqual(out['unique_corroborated_games'], 0)
            self.assertIn('CONFLICTING_FINAL_SCORES_NO_GRADE', out['quarantined'][0]['reasons'])

    def test_pregame_pending_is_valid_but_later_state_regression_is_quarantined(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pregame = self.seed(root, at=AT, completed=False)
            final = self.seed(root)
            self.assertEqual(dataset.assemble(root, [pregame, final])['unique_corroborated_games'], 1)
            regression = self.seed(root, at=AT + timedelta(hours=9), completed=False)
            out = dataset.assemble(root, [pregame, final, regression])
            self.assertEqual(out['unique_corroborated_games'], 0)
            self.assertIn('SOURCE_REVERTED_TO_NONFINAL_AFTER_AGREEMENT', out['quarantined'][0]['reasons'])

    def test_ncaa_id_reassigned_between_captures_quarantines_both(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); first = self.seed(root)
            second = self.seed(root, at=AT + timedelta(hours=9), game_id='401100002')
            out = dataset.assemble(root, [first, second])
            self.assertEqual(out['unique_corroborated_games'], 0)
            self.assertEqual(out['quarantined_games'], 2)
            self.assertTrue(all('NCAA_ID_REUSED_ACROSS_CAPTURES' in row['reasons']
                                for row in out['quarantined']))

    def test_nonreproducible_legacy_crosswalk_is_explicitly_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); stamp = self.seed(root)
            path = root / identity.ROOT / 'captures' / stamp / 'manifest.json'
            saved = json.loads(path.read_bytes())
            saved['report']['unique_source_game_identity_matches'] = 999
            path.write_text(json.dumps(saved))
            out = dataset.assemble(root, [stamp])
            self.assertEqual(out['unique_corroborated_games'], 0)
            self.assertEqual(out['captures_rejected'], 1)
            self.assertFalse(out['rejected_capture_receipts'][0]['included_in_result_dataset'])
            self.assertEqual(json.loads(path.read_bytes()), saved)

    def test_corrupt_original_source_aborts_instead_of_excluding_silently(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); stamp = self.seed(root)
            path = next((root / identity.ncaa.ROOT / 'captures').glob('*/*.gz'))
            path.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                dataset.assemble(root, [stamp])

    def test_no_silent_missing_or_duplicate_capture_selection(self):
        for stamps in ([], ['same', 'same']):
            with self.assertRaisesRegex(ValueError, 'unique'):
                dataset.assemble('.', stamps)


if __name__ == '__main__':
    unittest.main()
