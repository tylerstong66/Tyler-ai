"""Strict, separately archived native NBA Final-break observations; zero wagers."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import sports_nba_postgame_observation_v2 as v2
import sports_nba_postgame_observation_v3 as v3
import test_sports_nba_final_games_page_v3 as originals

START = datetime(2026, 10, 21, 14, 11, tzinfo=timezone.utc)


class FinalBreakReceiptTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        originals.FinalBreakStatusTests.setUpClass()
        self.raw = originals.FinalBreakStatusTests.original
        self.calls = []

    def collect(self, *, raw=None, started=START, received=None, days_back=1):
        moments = iter((started, received if received is not None else
                        started+timedelta(seconds=2)))
        def fetch(url):
            self.calls.append(url)
            return self.raw if raw is None else raw
        return v3.collect(self.base, days_back=days_back,
                          fetch=fetch, clock=lambda: next(moments))

    def test_real_final_bytes_are_sealed_without_enrolling_outcomes(self):
        report = self.collect()
        self.assertEqual(self.calls, ['https://www.nba.com/games?date=2026-10-20'])
        self.assertEqual(report['page_status'], 'SUPPORTED_REGULATION_FINAL_PAGE_SOURCE_ONLY')
        self.assertEqual(report['supported_final_game_count'], 3)
        self.assertEqual(report['schema'], v3.PROTOCOL.schema)
        for guard in ('independent_final_agreement_verified',
                      'official_final_results_verified', 'settlement_enabled',
                      'forecasting_enabled', 'model_training_enabled',
                      'promotion_allowed', 'feature_backfill_allowed'):
            self.assertIs(report[guard], False)
        self.assertIs(report['NO_BET'], True)
        self.assertEqual(report['outcomes_enrolled'], 0)
        self.assertEqual(report['actual_wagers'], 0)
        stamp = (START+timedelta(seconds=2)).strftime('%Y%m%dT%H%M%S%fZ')
        folder = self.base/v3.ROOT/stamp
        self.assertEqual({p.name for p in folder.iterdir()}, {'manifest.json', 'nba_games.html.gz'})
        self.assertEqual(v3.replay(self.base, stamp, now=START+timedelta(minutes=1))
                         ['supported_final_game_count'], 3)
        self.assertEqual(v3.replay_all(self.base, now=START+timedelta(minutes=1))
                         ['receipts_replayed'], 1)
        self.assertEqual(v2.shared._build(
            self.raw, started=START, received=START+timedelta(seconds=2),
            days_back=1, _protocol=v2.PROTOCOL)['supported_final_game_count'], 0)

    def test_unsupported_break_status_withholds_entire_page(self):
        payload = copy.deepcopy(originals.FinalBreakStatusTests.payload)
        cards = payload['props']['pageProps']['gameCardFeed']['modules'][0]['cards']
        cards[0]['cardData']['gameBreakStatus'] = 'Final/OT'
        raw = (b'<script id="__NEXT_DATA__" type="application/json">'
               + json.dumps(payload).encode() + b'</script>')
        report = self.collect(raw=raw)
        self.assertEqual(report['page_status'], 'UNSUPPORTED_OR_NOT_COMPLETE_FINAL_PAGE')
        self.assertIsNone(report['parsed_final_page'])
        self.assertEqual(report['supported_final_game_count'], 0)
        self.assertEqual(report['outcomes_enrolled'], 0)
        self.assertEqual(v3.replay_all(self.base, now=START+timedelta(minutes=1))
                         ['reports'][0]['supported_final_game_count'], 0)

    def test_corrupted_receipt_blocks_future_requests(self):
        self.collect()
        stamp = (START+timedelta(seconds=2)).strftime('%Y%m%dT%H%M%S%fZ')
        path = self.base/v3.ROOT/stamp/'manifest.json'
        path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaises(ValueError):
            self.collect(started=START+timedelta(minutes=5))
        self.assertEqual(len(self.calls), 1)

    def test_invalid_window_and_receipt_clock_never_publish(self):
        with self.assertRaises(ValueError):
            self.collect(days_back=4)
        self.assertEqual(self.calls, [])
        with self.assertRaises(ValueError):
            self.collect(received=START-timedelta(seconds=1))
        self.assertEqual(list((self.base/v3.ROOT).glob('*/manifest.json')), [])
        with self.assertRaises(ValueError):
            v3.replay(self.base, '../escape', now=START+timedelta(minutes=1))

    def test_audit_empty_and_inert_cli(self):
        self.assertEqual(v3.replay_all(self.base, now=START)['receipts_replayed'], 0)
        run = subprocess.run([sys.executable, str(Path(v3.__file__))],
                             capture_output=True, text=True, check=True)
        report = json.loads(run.stdout)
        self.assertIs(report['collection_requested'], False)
        self.assertEqual(report['actual_wagers'], 0)


if __name__ == '__main__':
    unittest.main()
