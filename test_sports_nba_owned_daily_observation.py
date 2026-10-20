from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import sports_nba_owned_daily_observation as daily
import sports_expansion_observer as espn

SOURCE = Path(__file__).parent
START = datetime(2026, 10, 20, 11, 29, 34, tzinfo=timezone.utc)
PROVIDER_STAMP = '20261020T095948145364Z'


class DailyObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        original = SOURCE/espn.ROOT/'captures'/PROVIDER_STAMP
        self.provider = self.base/espn.ROOT/'captures'/PROVIDER_STAMP
        shutil.copytree(original, self.provider)
        self.raw = gzip.decompress((SOURCE/'benchmarks/nba_games_page_v1/initial_probe/official_games_page.html.gz').read_bytes())
        self.calls = []

    def collect(self, *, started=START, received=None, raw=None, offset=0):
        times = iter([started, received or started+timedelta(seconds=1)])
        def fetch(url):
            self.calls.append(url); return self.raw if raw is None else raw
        return daily.collect(self.base, days_ahead=offset, fetch=fetch, clock=lambda: next(times))

    def test_complete_original_sources_match_and_replay(self):
        result = self.collect()
        self.assertEqual(result['strict_pregame_correlated'], 3)
        self.assertEqual(result['withheld'], [])
        self.assertEqual(result['espn_other_date_games_not_covered'], 25)
        self.assertEqual(self.calls, ['https://www.nba.com/games?date=2026-10-20'])
        self.assertEqual(result['recorded_at_utc'], (START+timedelta(seconds=1)).isoformat())
        stamp = espn.utc(result['recorded_at_utc']).strftime('%Y%m%dT%H%M%S%fZ')
        replay = daily.replay(self.base, stamp, now=START+timedelta(seconds=2))
        self.assertIs(replay['source_replay_verified'], True)
        self.assertIs(replay['source_currently_fresh'], True)
        for key in ('feature_collection_enabled', 'forecasting_enabled', 'model_training_enabled',
                    'promotion_allowed', 'source_scope_complete', 'official_final_results_verified',
                    'source_origin_independently_attested', 'receipt_clock_independently_attested'):
            self.assertIs(result[key], False)

    def test_next_day_route_matches_eleven_original_games(self):
        raw = gzip.decompress((SOURCE/'benchmarks/nba_games_page_v1/initial_probe/official_next_games_page.html.gz').read_bytes())
        result = self.collect(raw=raw, offset=1)
        self.assertEqual(result['strict_pregame_correlated'], 11)
        self.assertEqual(result['requested_date'], '2026-10-21')

    def test_existing_capture_never_overwrites(self):
        result = self.collect(); folder = next((self.base/daily.ROOT).iterdir())
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        same_time = START+timedelta(seconds=1)
        with self.assertRaises(FileExistsError): self.collect(started=same_time, received=same_time)
        self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})

    def test_incomplete_existing_receipt_blocks_http(self):
        root = self.base/daily.ROOT/'20261020T110000000000Z'
        root.mkdir(parents=True); (root/'nba_games.html.gz').write_bytes(b'incomplete')
        with self.assertRaisesRegex(ValueError, 'Unexpected NBA daily archive file'): self.collect()
        self.assertEqual(self.calls, [])

    def test_bad_payload_or_date_creates_no_capture(self):
        for raw, offset in ((b'<html>denied</html>', 0), (self.raw, 1)):
            with self.subTest(offset=offset), self.assertRaises(ValueError): self.collect(raw=raw, offset=offset)
        self.assertFalse((self.base/daily.ROOT).exists())

    def test_stale_future_provider_rejects_before_http(self):
        for start in (START+timedelta(hours=13), START-timedelta(hours=2)):
            with self.subTest(start=start), self.assertRaisesRegex(ValueError, 'stale or future'):
                self.collect(started=start)
        self.assertEqual(self.calls, [])

    def test_clock_reversal_duration_and_elapsed_start_rejected(self):
        for received in (START-timedelta(seconds=1), START+timedelta(minutes=6),
                         datetime(2026, 10, 20, 19, tzinfo=timezone.utc)):
            with self.subTest(received=received), self.assertRaises(ValueError):
                self.collect(received=received)
        self.assertFalse((self.base/daily.ROOT).exists())

    def test_invalid_offset_and_naive_clock_before_network(self):
        for offset in (True, -1, 4, 1.5):
            with self.subTest(offset=offset), self.assertRaises(ValueError): self.collect(offset=offset)
        with self.assertRaises(ValueError): self.collect(started=START.replace(tzinfo=None))
        self.assertEqual(self.calls, [])

    def test_tampered_archive_manifest_and_extra_files_reject(self):
        self.collect(); folder = next((self.base/daily.ROOT).iterdir()); stamp = folder.name
        blob = folder/'nba_games.html.gz'; original = blob.read_bytes()
        blob.write_bytes(gzip.compress(self.raw+b'\n'))
        with self.assertRaisesRegex(ValueError, 'exact source replay'): daily.replay(self.base, stamp, now=START+timedelta(seconds=2))
        blob.write_bytes(original)
        manifest = folder/'manifest.json'; original_manifest = manifest.read_bytes()
        value = json.loads(original_manifest); value['feature_collection_enabled'] = True
        manifest.write_bytes(espn.canonical(value))
        with self.assertRaisesRegex(ValueError, 'exact source replay'): daily.replay(self.base, stamp, now=START+timedelta(seconds=2))
        manifest.write_bytes(original_manifest); (folder/'unexpected.txt').write_text('extra')
        with self.assertRaisesRegex(ValueError, 'Unexpected'): daily.replay(self.base, stamp, now=START+timedelta(seconds=2))

    def test_modified_provider_raw_source_rejects(self):
        self.collect(); folder = next((self.base/daily.ROOT).iterdir())
        blob = next(self.provider.glob('NBA_*.json.gz')); raw = gzip.decompress(blob.read_bytes())
        blob.write_bytes(gzip.compress(raw+b'\n'))
        with self.assertRaises(ValueError): daily.replay(self.base, folder.name, now=START+timedelta(seconds=2))

    def test_audit_clock_cannot_precede_receipt_and_reports_staleness(self):
        self.collect(); stamp = next((self.base/daily.ROOT).iterdir()).name
        with self.assertRaisesRegex(ValueError, 'time/folder'): daily.replay(self.base, stamp, now=START)
        result = daily.replay(self.base, stamp, now=START+timedelta(hours=13))
        self.assertIs(result['source_replay_verified'], True)
        self.assertIs(result['source_currently_fresh'], False)

    def test_nonunique_or_nonpregame_espn_game_is_withheld(self):
        provider_raw, _, provider = daily._provider(self.base, PROVIDER_STAMP)
        selected = next(key for key, value in provider.items() if value['home_tricode'] == 'DET')
        for change in ({'state': 'in'}, {'season_stage': 1}, {'provider_completed': True}):
            with self.subTest(change=change):
                modified = {key: dict(value) for key, value in provider.items()}
                modified[selected].update(change)
                result = daily._build(self.raw, provider_raw, modified, started=START,
                    received=START+timedelta(seconds=1), day='2026-10-20', season='2026-27', stamp=PROVIDER_STAMP, offset=0)
                self.assertEqual(result['strict_pregame_correlated'], 2)
                self.assertEqual(len(result['withheld']), 1)

    def test_cli_default_has_no_network_or_writes(self):
        with (patch('sys.argv', ['daily']), patch.object(daily, 'collect') as collect,
                patch('builtins.print') as output):
            daily.main(); collect.assert_not_called()
        self.assertIs(json.loads(output.call_args.args[0])['collection_requested'], False)

    def test_transport_bounds_fixed_host_headers_and_status(self):
        response = MagicMock(); response.__enter__.return_value = response
        response.status_code = 200; response.iter_content.return_value = [b'original']
        get = MagicMock(return_value=response)
        url = 'https://www.nba.com/games?date=2026-10-21'
        self.assertEqual(daily.fetch_page(url, get=get), b'original')
        args = get.call_args.kwargs
        self.assertEqual(args['timeout'], (10, 20))
        self.assertIs(args['allow_redirects'], False)
        self.assertIs(args['stream'], True)
        self.assertNotIn('Authorization', args['headers'])
        self.assertNotIn('Cookie', args['headers'])
        for status in (302, 403, True):
            response.status_code = status; response.iter_content.reset_mock()
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, 'HTTP 200'):
                daily.fetch_page(url, get=get)
            response.iter_content.assert_not_called()
        get.reset_mock()
        with self.assertRaisesRegex(ValueError, 'endpoint'):
            daily.fetch_page('https://example.com/games?date=2026-10-21', get=get)
        get.assert_not_called()

    def test_transport_oversize_rejected(self):
        response = MagicMock(); response.__enter__.return_value = response
        response.status_code = 200
        response.iter_content.return_value = [b'x'*(daily.page.MAX_BYTES+1)]
        with self.assertRaisesRegex(ValueError, 'Oversized'):
            daily.fetch_page('https://www.nba.com/games?date=2026-10-21', get=lambda *a, **k: response)


if __name__ == '__main__': unittest.main()
