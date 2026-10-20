"""Recent postgame source capture bounds and immutable replay; no grading."""
from datetime import datetime, timedelta, timezone
import gzip
import json
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_postgame_observation as capture

SOURCE = Path(__file__).parent
NOW = datetime(2026, 10, 20, 14, tzinfo=timezone.utc)


class PostgameObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.calls = []
        self.raw = gzip.decompress((SOURCE/capture.final.FIXTURE_ROOT/'nba_games.html.gz').read_bytes())

    def collect(self, *, raw=None, started=NOW, received=None, days_back=1):
        times = iter([started, received or started+timedelta(seconds=1)])
        def fetch(url):
            self.calls.append(url)
            return self.raw if raw is None else raw
        return capture.collect(self.base, days_back=days_back, fetch=fetch, clock=lambda: next(times))

    def stamp(self, record):
        return datetime.fromisoformat(record['recorded_at_utc']).strftime('%Y%m%dT%H%M%S%fZ')

    def test_original_old_page_cannot_be_recast_as_current_final_evidence(self):
        result = self.collect()
        self.assertEqual(self.calls, ['https://www.nba.com/games?date=2026-10-19'])
        self.assertEqual(result['page_status'], 'UNSUPPORTED_OR_NOT_COMPLETE_FINAL_PAGE')
        self.assertIsNone(result['parsed_final_page'])
        self.assertEqual(result['supported_final_game_count'], 0)
        folder = self.base/capture.ROOT/self.stamp(result)
        self.assertEqual(gzip.decompress((folder/'nba_games.html.gz').read_bytes()), self.raw)
        replay = capture.replay(self.base, self.stamp(result), now=NOW+timedelta(seconds=2))
        self.assertTrue(replay['source_bytes_replayed'])
        self.assertEqual(replay['outcomes_enrolled'], 0)

    def test_known_final_shape_under_simulated_unit_clock_never_enrolls_outcomes(self):
        # Artificial unit-test receipt clock only. Original fixture was actually
        # observed in October; this temporary receipt is never research evidence.
        simulated = datetime(2026, 4, 11, 12, tzinfo=timezone.utc)
        result = self.collect(started=simulated)
        self.assertEqual(result['page_status'], 'SUPPORTED_REGULATION_FINAL_PAGE_SOURCE_ONLY')
        self.assertEqual(result['supported_final_game_count'], 15)
        self.assertEqual(result['recorded_at_utc'], (simulated+timedelta(seconds=1)).isoformat())
        for flag in ('official_final_results_verified', 'independent_final_agreement_verified',
                     'settlement_enabled', 'forecasting_enabled', 'feature_backfill_allowed',
                     'model_training_enabled', 'historical_evaluation_enabled', 'promotion_allowed'):
            self.assertIs(result[flag], False)
        self.assertEqual(result['outcomes_enrolled'], 0)

    def test_unsupported_html_is_preserved_opaque_without_partial_finals(self):
        result = self.collect(raw=b'<html>no usable source</html>')
        self.assertEqual(result['page_status'], 'UNSUPPORTED_OR_NOT_COMPLETE_FINAL_PAGE')
        self.assertIsNone(result['parsed_final_page'])
        self.assertEqual(result['supported_final_game_count'], 0)

    def test_empty_day_is_never_positive_final_evidence(self):
        payload = json.loads(re.search(rb'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', self.raw, re.S)[1])
        props = payload['props']['pageProps']
        props['gameCardFeed']['modules'] = []
        props['allGamesInCurrentYear']['2026']['2026-04-10'] = 0
        raw = b'<script id="__NEXT_DATA__" type="application/json">'+json.dumps(payload).encode()+b'</script>'
        result = self.collect(raw=raw, started=datetime(2026, 4, 11, 12, tzinfo=timezone.utc))
        self.assertEqual(result['page_status'], 'EMPTY_DAY_NO_FINAL_EVIDENCE')
        self.assertEqual(result['supported_final_game_count'], 0)
        self.assertFalse(result['official_final_results_verified'])

    def test_single_unsupported_card_withholds_all_other_final_cards(self):
        payload = json.loads(re.search(rb'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', self.raw, re.S)[1])
        payload['props']['pageProps']['gameCardFeed']['modules'][0]['cards'][0]['cardData']['period'] = 5
        raw = b'<script id="__NEXT_DATA__" type="application/json">'+json.dumps(payload).encode()+b'</script>'
        result = self.collect(raw=raw, started=datetime(2026, 4, 11, 12, tzinfo=timezone.utc))
        self.assertEqual(result['page_status'], 'UNSUPPORTED_OR_NOT_COMPLETE_FINAL_PAGE')
        self.assertEqual(result['supported_final_game_count'], 0)
        self.assertIsNone(result['parsed_final_page'])

    def test_invalid_offsets_and_clocks_reject_without_network(self):
        for value in (True, -1, 4, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.collect(days_back=value)
        with self.assertRaises(ValueError): self.collect(started=NOW.replace(tzinfo=None))
        self.assertEqual(self.calls, [])
        for received in (NOW-timedelta(seconds=1), NOW+timedelta(minutes=6)):
            with self.subTest(received=received), self.assertRaises(ValueError):
                self.collect(received=received)
        self.assertFalse((self.base/capture.ROOT).exists())

    def test_existing_receipt_is_not_overwritten_and_future_replay_is_rejected(self):
        result = self.collect(); stamp = self.stamp(result)
        folder = self.base/capture.ROOT/stamp
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        with self.assertRaises(FileExistsError):
            self.collect(started=NOW+timedelta(seconds=1), received=NOW+timedelta(seconds=1))
        self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})
        with self.assertRaisesRegex(ValueError, 'clock/folder'):
            capture.replay(self.base, stamp, now=NOW)

    def test_body_manifest_extra_file_and_folder_tampering_rejected(self):
        result = self.collect(); stamp = self.stamp(result)
        folder = self.base/capture.ROOT/stamp
        body = folder/'nba_games.html.gz'; original = body.read_bytes()
        body.write_bytes(gzip.compress(self.raw+b'\n'))
        with self.assertRaisesRegex(ValueError, 'original source replay'):
            capture.replay(self.base, stamp, now=NOW+timedelta(seconds=2))
        body.write_bytes(original)
        manifest = folder/'manifest.json'; original = manifest.read_bytes()
        row = json.loads(original); row['settlement_enabled'] = True
        manifest.write_bytes(capture.canonical(row))
        with self.assertRaisesRegex(ValueError, 'original source replay'):
            capture.replay(self.base, stamp, now=NOW+timedelta(seconds=2))
        manifest.write_bytes(original); (folder/'extra').touch()
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            capture.replay(self.base, stamp, now=NOW+timedelta(seconds=2))

    def test_redirected_destination_and_incomplete_prior_capture_block_fetch(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.base/'benchmarks').symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'Symlink'): self.collect()
            self.assertEqual(self.calls, []); self.assertEqual(list(Path(outside).iterdir()), [])
        (self.base/'benchmarks').unlink()
        folder = self.base/capture.ROOT/'20261020T130000000000Z'
        folder.mkdir(parents=True); (folder/'manifest.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Unexpected'): self.collect()
        self.assertEqual(self.calls, [])

    def test_oversized_or_empty_body_creates_no_receipt(self):
        for raw in (b'', b'x'*21):
            with self.subTest(raw=raw), patch.object(capture.page, 'MAX_BYTES', 20), self.assertRaises(ValueError):
                self.collect(raw=raw)
        self.assertFalse((self.base/capture.ROOT).exists())

    def test_eastern_date_and_season_boundary_are_fixed_before_fetch(self):
        result = self.collect(started=datetime(2026, 7, 1, 1, tzinfo=timezone.utc), days_back=0)
        self.assertEqual(result['requested_date'], '2026-06-30')
        self.assertEqual(result['season'], '2025-26')
        self.assertEqual(self.calls, ['https://www.nba.com/games?date=2026-06-30'])

    def test_cli_default_is_inert(self):
        with patch('sys.argv', ['capture']), patch.object(capture, 'collect') as collect, patch('builtins.print') as output:
            capture.main(); collect.assert_not_called()
        self.assertFalse(json.loads(output.call_args.args[0])['collection_requested'])


if __name__ == '__main__': unittest.main()
