"""Synthetic clocks and null envelopes are fixtures, never prospective evidence."""
import copy
from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_postgame_observation as v1
import sports_nba_postgame_observation_v2 as v2
import test_sports_nba_final_games_page as fixtures

SIMULATED = datetime(2026, 4, 11, 12, tzinfo=timezone.utc)
CURRENT = datetime(2026, 10, 20, 14, tzinfo=timezone.utc)


class NativePostgameTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        fixtures.FinalGamesPageTests.setUpClass()
        self.payload = copy.deepcopy(fixtures.FinalGamesPageTests.payload)
        self.payload['props']['pageProps']['isDateOverrideActive'] = None
        self.calls = []

    def raw(self, value=None):
        return b'<script id="__NEXT_DATA__" type="application/json">'+json.dumps(
            self.payload if value is None else value).encode()+b'</script>'

    def collect(self, *, started=SIMULATED, received=None, value=None, days_back=1):
        times = iter([started, received or started+timedelta(seconds=1)])
        def fetch(url):
            self.calls.append(url); return self.raw(value)
        return v2.collect(self.base, days_back=days_back, fetch=fetch, clock=lambda: next(times))

    def folder(self):
        return next((self.base/v2.ROOT).iterdir())

    def test_source_bytes_and_separate_replay_have_no_outcome_authority(self):
        result = self.collect(); folder = self.folder()
        self.assertTrue(result['schema'].endswith('v2'))
        self.assertEqual(result['supported_final_game_count'], 15)
        self.assertEqual(result['page_status'], 'SUPPORTED_REGULATION_FINAL_PAGE_SOURCE_ONLY')
        self.assertEqual(gzip.decompress((folder/'nba_games.html.gz').read_bytes()), self.raw())
        self.assertTrue(v2.replay(self.base, folder.name, now=SIMULATED+timedelta(seconds=2))['source_bytes_replayed'])
        self.assertEqual(v1.replay_all(self.base)['receipts_replayed'], 0)
        for flag in ('official_final_results_verified', 'independent_final_agreement_verified',
                     'feature_backfill_allowed', 'feature_collection_enabled', 'settlement_enabled',
                     'forecasting_enabled', 'historical_evaluation_enabled', 'model_training_enabled',
                     'promotion_allowed', 'receipt_clock_independently_attested'):
            self.assertIs(result[flag], False)
        self.assertEqual(result['outcomes_enrolled'], 0)
        self.assertEqual(result['actual_wagers'], 0); self.assertIs(result['NO_BET'], True)

    def test_old_historical_page_cannot_be_recast_as_current_final_evidence(self):
        result = self.collect(started=CURRENT)
        self.assertEqual(result['requested_date'], '2026-10-19')
        self.assertEqual(result['supported_final_game_count'], 0)
        self.assertEqual(result['page_status'], 'UNSUPPORTED_OR_NOT_COMPLETE_FINAL_PAGE')
        self.assertIsNone(result['parsed_final_page'])

    def test_empty_day_is_explicitly_no_final_evidence(self):
        value = copy.deepcopy(self.payload); p = value['props']['pageProps']
        p['gameCardFeed']['modules'] = []
        p['allGamesInCurrentYear']['2026']['2026-04-10'] = 0
        result = self.collect(value=value)
        self.assertEqual(result['page_status'], 'EMPTY_DAY_NO_FINAL_EVIDENCE')
        self.assertEqual(result['supported_final_game_count'], 0)

    def test_single_overtime_or_live_card_withholds_complete_page(self):
        for change in ({'period': 5}, {'gameStatus': 2}):
            value = copy.deepcopy(self.payload)
            value['props']['pageProps']['gameCardFeed']['modules'][0]['cards'][0]['cardData'].update(change)
            # Each temporary receipt gets a distinct actual simulated clock.
            start = SIMULATED+timedelta(minutes=len(self.calls))
            result = self.collect(value=value, started=start)
            self.assertEqual(result['supported_final_game_count'], 0)
            self.assertIsNone(result['parsed_final_page'])

    def test_true_envelope_is_opaque_in_v2_and_does_not_change_v1(self):
        value = copy.deepcopy(self.payload); value['props']['pageProps']['isDateOverrideActive'] = True
        result = self.collect(value=value)
        self.assertEqual(result['supported_final_game_count'], 0)
        clocks = iter([SIMULATED, SIMULATED+timedelta(seconds=1)])
        original = v1.collect(self.base, fetch=lambda url: self.raw(value), clock=lambda: next(clocks))
        self.assertEqual(original['supported_final_game_count'], 15)
        self.assertEqual(original['schema'], v1.SCHEMA)
        self.assertEqual(v1.replay_all(self.base)['receipts_replayed'], 1)
        self.assertEqual(v2.replay_all(self.base)['receipts_replayed'], 1)

    def test_tampering_no_overwrite_and_future_audit_are_rejected(self):
        self.collect(); folder = self.folder()
        original = (folder/'manifest.json').read_bytes()
        with self.assertRaises(FileExistsError):
            self.collect(started=SIMULATED+timedelta(seconds=1), received=SIMULATED+timedelta(seconds=1))
        self.assertEqual(original, (folder/'manifest.json').read_bytes())
        with self.assertRaises(ValueError): v2.replay(self.base, folder.name, now=SIMULATED)
        value = json.loads(original); value['outcomes_enrolled'] = 15
        (folder/'manifest.json').write_bytes(v1.canonical(value))
        with self.assertRaisesRegex(ValueError, 'original source replay'):
            v2.replay(self.base, folder.name, now=SIMULATED+timedelta(seconds=2))

    def test_invalid_bounds_and_destination_block_network(self):
        for offset in (True, -1, 4, 1.5):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                self.collect(days_back=offset)
        with self.assertRaises(ValueError):
            self.collect(started=SIMULATED.replace(tzinfo=None))
        self.assertEqual(self.calls, [])
        with tempfile.TemporaryDirectory() as outside:
            (self.base/'benchmarks').symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'Symlink'): self.collect()
        self.assertEqual(self.calls, [])

    def test_receipt_clock_reversal_or_overlong_request_creates_no_archive(self):
        for received in (SIMULATED-timedelta(seconds=1), SIMULATED+timedelta(minutes=6)):
            with self.assertRaises(ValueError): self.collect(received=received)
        self.assertFalse((self.base/v2.ROOT).exists())

    def test_cli_default_is_inert(self):
        with patch('sys.argv', ['postgame-v2']), patch.object(v2, 'collect') as collect, patch('builtins.print') as output:
            v2.main(); collect.assert_not_called()
        self.assertIs(json.loads(output.call_args.args[0])['collection_requested'], False)

    def test_retained_native_receipts_replay(self):
        report = v2.replay_all(Path(__file__).parent)
        for row in report['reports']:
            self.assertTrue(row['source_bytes_replayed'])
            self.assertEqual(row['outcomes_enrolled'], 0)


if __name__ == '__main__': unittest.main()
