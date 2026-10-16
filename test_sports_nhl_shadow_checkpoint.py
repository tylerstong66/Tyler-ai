"""Synthetic first-100 challenger checkpoint invariants, no game/network reads."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sports_nhl_shadow_checkpoint as checkpoint


def fixtures(size=100):
    selected = [{'game_id': str(i), 'sha256': 'frozen-sha-'+str(i)}
                for i in range(size)]
    rows = []
    for i in range(size):
        rows.append({
            'game_id': str(i), 'block': f'2026-10-{17+i//10:02d}',
            'candidate': {'brier': 0.2+i/1000, 'log_loss': .4, 'accuracy': 1.0},
            'model': {'brier': .3, 'log_loss': .5, 'accuracy': 1.0},
            'fixed_elo': {'brier': .4, 'log_loss': .6, 'accuracy': 0.0},
            'market': {'brier': .5, 'log_loss': .7, 'accuracy': 0.0} if i%2 else None,
        })
    return selected, rows


def paired(rows):
    return {'games': len(rows), 'candidate_minus_primary_brier':
            sum(row['candidate']['brier']-row['model']['brier'] for row in rows)}


class ShadowCheckpointTests(unittest.TestCase):
    def exercise(self, directory, selected, rows):
        # Shared real estimator has dedicated bootstrap tests. Here isolate
        # checkpoint lifecycle and use fast deterministic metric summaries.
        with patch.object(checkpoint.review, 'estimates', side_effect=lambda data: {
                'games': len(data), 'total_brier': sum(row['brier'] for row in data)}):
            return checkpoint.preserve(directory, selected, rows, 'pinned-policy', paired)

    def test_requires_first_100_finals_not_100_other_settlements(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            selected, rows = fixtures()
            early = self.exercise(root, selected[:99], rows)
            self.assertEqual(early['status'], 'collecting_forecasts')
            other = self.exercise(root, selected, rows[1:])
            self.assertEqual((other['settled_selected'], other['status']),
                             (99, 'awaiting_selected_results'))
            self.assertFalse((root/checkpoint.RELATIVE_PATH).exists())
            final = self.exercise(root, selected, rows)
            self.assertEqual(final['status'], 'preserved')
            self.assertTrue((root/checkpoint.RELATIVE_PATH).is_file())
            saved = json.loads((root/checkpoint.RELATIVE_PATH).read_text())
            self.assertEqual(saved['game_ids'], [str(i) for i in range(100)])
            self.assertEqual(saved['priced_same_games']['market']['games'], 50)
            self.assertIs(saved['NO_BET'], True)
            self.assertFalse(saved['promotion_allowed'])

    def test_preserved_checkpoint_reuses_exact_bytes_and_ignores_later_games(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            selected, rows=fixtures()
            first=self.exercise(root, selected, rows)
            original=(root/checkpoint.RELATIVE_PATH).read_bytes()
            self.assertEqual(first, self.exercise(root, selected, rows))
            self.assertEqual(original, (root/checkpoint.RELATIVE_PATH).read_bytes())
            later_forecast, later_result=fixtures(101)
            self.assertEqual(first, self.exercise(root, later_forecast[:100], later_result))
            self.assertEqual(original, (root/checkpoint.RELATIVE_PATH).read_bytes())

    def test_rejects_modified_forecast_outcome_or_saved_checkpoint(self):
        for change in ('prediction', 'result', 'checkpoint', 'missing_result'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                selected, rows=fixtures()
                self.exercise(root, selected, rows)
                if change=='prediction':
                    selected[0]['sha256']='tampered'
                elif change=='result':
                    rows[0]['candidate']['brier']=1.8
                elif change=='missing_result':
                    rows.pop(0)
                else:
                    path=root/checkpoint.RELATIVE_PATH
                    payload=json.loads(path.read_text())
                    payload['settled']=99
                    path.write_text(json.dumps(payload))
                with self.assertRaisesRegex(ValueError, 'checkpoint or selected inputs changed'):
                    self.exercise(root, selected, rows)

    def test_duplicate_source_identifiers_are_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            selected, rows=fixtures()
            selected[1]['game_id']=selected[0]['game_id']
            with self.assertRaisesRegex(ValueError, 'Repeated NHL shadow forecast'):
                self.exercise(root, selected, rows)
            self.assertFalse((root/checkpoint.RELATIVE_PATH).exists())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            selected, rows=fixtures()
            rows[1]['game_id']=rows[0]['game_id']
            with self.assertRaisesRegex(ValueError, 'Repeated NHL shadow result'):
                self.exercise(root, selected, rows)
            self.assertFalse((root/checkpoint.RELATIVE_PATH).exists())


if __name__=='__main__':
    unittest.main()
