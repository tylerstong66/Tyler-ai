"""Independent NCAA history remains immutable and research-only."""
import json
from pathlib import Path
from datetime import datetime, timezone
import tempfile
import unittest
import sports_ncaa_historical_owned as owned
from test_sports_ncaa_espn_identity import official_game

NOW = datetime(2026, 10, 18, tzinfo=timezone.utc)
START = int(datetime(2024, 8, 24, 17, tzinfo=timezone.utc).timestamp())


def payload():
    game = official_game(when=START, final=True)
    game['startDate'] = '08/24/2024'
    return json.dumps({'data': {'contests': [game]}}).encode()


class NcaaHistoricalOwnedTests(unittest.TestCase):
    def test_raw_receipts_replay_without_training_and_append_next_weeks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            out = owned.capture(lambda _: payload(), base=root, now=NOW)
            self.assertEqual(out['new_source_weeks'], 3)
            saved = owned.verify(root, 'train', 1, now=NOW)
            self.assertEqual(saved['parsed_ncaa_games'][0]['ncaa_home_score'], 28)
            self.assertFalse(saved['official_result_grading_enabled'])
            first = (root/owned.ROOT/'train'/'week-01.receipt.json').read_bytes()
            again = owned.capture(lambda _: payload(), base=root, now=NOW, per_run=1)
            self.assertEqual(again['retained_source_weeks'], 4)
            self.assertEqual((root/owned.ROOT/'train'/'week-01.receipt.json').read_bytes(), first)

    def test_bad_season_or_failed_second_response_publishes_no_partial_batch(self):
        for mode in ('season', 'provider'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
                calls = 0
                def fetch(url):
                    nonlocal calls
                    calls += 1
                    if mode == 'season':
                        game = official_game(final=True)
                        return json.dumps({'data': {'contests': [game]}}).encode()
                    return payload() if calls == 1 else b'{"errors":["failed"]}'
                with self.assertRaises(ValueError):
                    owned.capture(fetch, base=td, now=NOW)
                self.assertFalse((Path(td)/owned.ROOT).exists())

    def test_corrupt_retained_source_blocks_fetch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            owned.capture(lambda _: payload(), base=root, now=NOW, per_run=1)
            (root/owned.ROOT/'train'/'week-01.json.gz').write_bytes(b'bad')
            with self.assertRaises(ValueError):
                owned.capture(lambda _: self.fail('No fetch after corrupt receipt'), base=root, now=NOW)

    def test_future_observation_or_enabled_forecasting_blocks_fetch(self):
        for field, value in (('recorded_at_utc', '2027-01-01T00:00:00Z'),
                             ('forecasting_enabled', True)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                owned.capture(lambda _: payload(), base=root, now=NOW, per_run=1)
                path = root/owned.ROOT/'train'/'week-01.receipt.json'
                obj = json.loads(path.read_bytes()); obj[field] = value
                path.write_text(json.dumps(obj))
                with self.assertRaises(ValueError):
                    owned.capture(lambda _: self.fail('No fetch on invalid receipt'), base=root, now=NOW)

    def test_auto_phase_advances_only_after_all_training_week_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = owned.capture(lambda _: payload(), base=root, now=NOW, split='auto')
            self.assertEqual(first['split'], 'train')
            for _ in range(6):
                owned.capture(lambda _: payload(), base=root, now=NOW)
            before = (root/owned.ROOT/'train'/'week-01.receipt.json').read_bytes()
            calls = []
            def validation_source(url):
                calls.append(url)
                game = official_game(when=int(datetime(2025,8,23,17,tzinfo=timezone.utc).timestamp()), final=True)
                game['startDate'] = '08/23/2025'
                return json.dumps({'data': {'contests': [game]}}).encode()
            out = owned.capture(validation_source, base=root, now=NOW, split='auto')
            self.assertEqual((out['split'], out['new_source_weeks']), ('validation', 3))
            self.assertEqual(len(calls), 3)
            self.assertTrue(all('2025' in url for url in calls))
            self.assertEqual((root/owned.ROOT/'train'/'week-01.receipt.json').read_bytes(), before)
            self.assertFalse(out['model_training_enabled'])
            self.assertFalse(out['forecasting_enabled'])
            for _ in range(6):
                owned.capture(validation_source, base=root, now=NOW, split='auto')
            done = owned.capture(lambda _: self.fail('No request after both indices complete'),
                                 base=root, now=NOW, split='auto')
            self.assertEqual((done['new_source_weeks'], done['retained_source_weeks']), (0, 21))

    def test_published_game_date_cannot_contradict_historical_epoch(self):
        obj = json.loads(payload())
        obj['data']['contests'][0]['startDate'] = '08/24/2026'
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, 'contradicts kickoff'):
                owned.capture(lambda _: json.dumps(obj).encode(), base=td, now=NOW)
            self.assertFalse((Path(td)/owned.ROOT).exists())

    def test_scope_and_fetch_budget_are_bounded(self):
        for kwargs in ({'split': '../bad'}, {'per_run': 4}, {'per_run': False}):
            with self.assertRaises(ValueError):
                owned.capture(lambda _: payload(), **kwargs)


if __name__ == '__main__':
    unittest.main()
