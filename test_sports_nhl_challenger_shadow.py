"""Synthetic fail-closed tests for the forward-only NHL development shadow."""
import json
import shutil
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

import sports_benchmark_review as review
import sports_nhl_challenger_shadow as shadow


class NhlForwardShadowTests(unittest.TestCase):
    def prepare(self, base):
        for path in (shadow.ROOT / 'protocol.json', shadow.SOURCE):
            dest = base / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
        root = base / shadow.LIVE
        (root / 'predictions').mkdir(parents=True, exist_ok=True)
        (root / 'results').mkdir(parents=True, exist_ok=True)
        kickoff = '2026-10-17T00:00:00+00:00'
        original = {
            'sport': 'NHL', 'game_id': 'fixture', 'event_id': 'espnfixture',
            'home': 'H', 'away': 'A', 'home_id': '1', 'away_id': '2',
            'season': 2026, 'kickoff': kickoff,
            'generated_at': '2026-10-16T18:00:00+00:00',
            'recorded_at': '2026-10-16T18:00:01+00:00',
            'model_sha256': 'synthetic-frozen-model-digest',
            'features': [1.0, 0.25],
            'model': {'home': .53, 'away': .47},
            'fixed_elo': {'home': .58, 'away': .42},
            'market': {'conditional_home_probability': .56},
            'market_observed_at': '2026-10-16T16:50:00+00:00',
            'NO_BET': True, 'actual_wagers': 0,
        }
        original['sha256'] = review.digest(original)
        path = root / 'predictions/fixture.json'
        path.write_text(json.dumps(original))
        return root, path, original

    def final(self, root, original):
        y = 'home'
        scores = {
            name: {**review.binary_scores(original[name]['home'] if name != 'market'
                              else original['market']['conditional_home_probability'], y),
                   }
            for name in ('model', 'fixed_elo', 'market')
        }
        # The original settlement's official score key is 'correct' (bool),
        # while our shared scoring library uses 'accuracy' (float).
        for score in scores.values():
            score['correct'] = bool(score.pop('accuracy'))
        result = {
            'sport': 'NHL', 'game_id': 'fixture', 'event_id': 'espnfixture',
            'home_score': 3, 'away_score': 2, 'outcome': 'home',
            'verified_at': '2026-10-17T03:00:00+00:00',
            'prediction_sha256': original['sha256'], 'scores': scores,
        }
        (root / 'results/fixture.json').write_text(json.dumps(result))

    def test_future_only_enrolls_once_and_scores_against_identical_games(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root, source, original = self.prepare(base)
            before = source.read_bytes()
            clock = review.utc('2026-10-16T19:00:00Z')
            first = shadow.evaluate(base, clock)
            self.assertEqual((first['enrolled'], first['newly_enrolled'],
                              first['scored'], first['pending']), (1, 1, 0, 1))
            pred = json.loads((base / shadow.ROOT / 'predictions/fixture.json').read_text())
            frozen = (base / shadow.ROOT / 'predictions/fixture.json').read_bytes()
            self.assertTrue(.5 < pred['home_probability'] < 1)
            self.assertEqual(pred['source_prediction_sha256'], original['sha256'])
            second = shadow.evaluate(base, clock)
            self.assertEqual((second['newly_enrolled'], second['enrolled']), (0, 1))
            self.assertEqual((base / shadow.ROOT / 'predictions/fixture.json').read_bytes(), frozen)
            self.final(root, original)
            no_future_grade = shadow.evaluate(base, clock)
            self.assertEqual(no_future_grade['scored'], 0)
            later = shadow.evaluate(base, review.utc('2026-10-17T05:00:00Z'))
            self.assertEqual((later['scored'], later['pending'], later['same_game_priced_count']),
                             (1, 0, 1))
            for model in ('candidate', 'model', 'fixed_elo', 'market'):
                self.assertEqual(later['same_game_priced'][model]['games'], 1)
            self.assertEqual(later['first_100_enrolled']['status'],
                             'collecting_or_awaiting_selected_finals')
            self.assertFalse(later['promotion_allowed'])
            self.assertTrue(later['NO_BET'])
            self.assertEqual(source.read_bytes(), before)

    def test_never_backfills_old_pregame_or_after_kickoff(self):
        for mutation, when in (
            ({'generated_at': '2026-10-16T16:59:00+00:00',
              'recorded_at': '2026-10-16T16:59:01+00:00'},
             '2026-10-16T19:00:00Z'),
            ({}, '2026-10-17T02:00:00Z'),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                base = Path(folder)
                _, source, original = self.prepare(base)
                original.update(mutation)
                original.pop('sha256')
                original['sha256'] = review.digest(original)
                source.write_text(json.dumps(original))
                result = shadow.evaluate(base, review.utc(when))
                self.assertEqual(result['enrolled'], 0)
                self.assertFalse(list((base / shadow.ROOT / 'predictions').glob('*.json')))

    def test_tampered_existing_prediction_or_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            _, source, _ = self.prepare(base)
            clock = review.utc('2026-10-16T19:00:00Z')
            shadow.evaluate(base, clock)
            path = base / shadow.ROOT / 'predictions/fixture.json'
            record = json.loads(path.read_text())
            record['home_probability'] = 0.91
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                shadow.evaluate(base, clock)
            path.unlink()
            original = json.loads(source.read_text())
            original['features'] = [1, 1]
            source.write_text(json.dumps(original))
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                shadow.evaluate(base, clock)

    def test_future_source_snapshot_cannot_create_shadow(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            _, source, original = self.prepare(base)
            original['source_snapshots'] = [
                {'retrieved_at': '2026-10-16T19:00:00+00:00'}]
            original.pop('sha256')
            original['sha256'] = review.digest(original)
            source.write_text(json.dumps(original))
            with self.assertRaisesRegex(ValueError, 'Source snapshot was retrieved after'):
                shadow.evaluate(base, review.utc('2026-10-16T19:30:00Z'))
            self.assertFalse(list((base / shadow.ROOT / 'predictions').glob('*.json')))

    def test_bad_existing_shadow_blocks_new_forecast_batch(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root, original_path, original = self.prepare(base)
            clock = review.utc('2026-10-16T19:00:00Z')
            shadow.evaluate(base, clock)
            another = {**original, 'game_id': 'fixture2', 'event_id': 'espnfixture2'}
            another.pop('sha256')
            another['sha256'] = review.digest(another)
            (root / 'predictions/fixture2.json').write_text(json.dumps(another))
            first_path = base / shadow.ROOT / 'predictions/fixture.json'
            first = json.loads(first_path.read_text())
            first['home_probability'] = 0.9
            first_path.write_text(json.dumps(first))
            with self.assertRaisesRegex(ValueError, 'Shadow forecast digest mismatch'):
                shadow.evaluate(base, clock)
            self.assertFalse((base / shadow.ROOT / 'predictions/fixture2.json').exists())

    def test_frozen_development_weights_and_provenance_are_locked(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            self.prepare(base)
            protocol_path = base / shadow.ROOT / 'protocol.json'
            data = json.loads(protocol_path.read_text())
            data['weights'] = [.1, .1]
            protocol_path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'weights changed'):
                shadow.evaluate(base, review.utc('2026-10-16T19:00:00Z'))


if __name__ == '__main__':
    unittest.main()
