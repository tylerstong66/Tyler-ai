"""V2 collection tests use explicitly synthetic null-envelope fixtures."""
from datetime import timedelta
import copy
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_owned_daily_observation as v1
import sports_nba_owned_daily_observation_v2 as v2
import sports_expansion_observer as espn
import test_sports_nba_games_page as games_fixture
from test_sports_nba_owned_daily_observation import START, PROVIDER_STAMP

SOURCE = Path(__file__).parent


class V2ObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        source = SOURCE/espn.ROOT/'captures'/PROVIDER_STAMP
        shutil.copytree(source, self.base/espn.ROOT/'captures'/PROVIDER_STAMP)
        games_fixture.GamesPageTests.setUpClass()
        value = copy.deepcopy(games_fixture.GamesPageTests.payload)
        value['props']['pageProps']['isDateOverrideActive'] = None
        self.raw = (b'<script id="__NEXT_DATA__" type="application/json">'
                    +json.dumps(value).encode()+b'</script>')
        self.calls = []

    def collect(self, *, started=START, received=None, raw=None):
        times = iter([started, received or started+timedelta(seconds=1)])
        def fetch(url):
            self.calls.append(url)
            return self.raw if raw is None else raw
        return v2.collect(self.base, days_ahead=0, fetch=fetch, clock=lambda: next(times))

    def folder(self):
        return next((self.base/v2.ROOT).iterdir())

    def test_native_bytes_and_versioned_receipt_replay_without_v1_changes(self):
        result = self.collect(); folder = self.folder()
        self.assertEqual(result['strict_pregame_correlated'], 3)
        self.assertEqual(result['withheld'], [])
        self.assertTrue(result['schema'].endswith('v2'))
        self.assertEqual(gzip.decompress((folder/'nba_games.html.gz').read_bytes()), self.raw)
        self.assertIs(v2.replay(self.base, folder.name, now=START+timedelta(seconds=2))['source_replay_verified'], True)
        self.assertEqual(v1.replay_all(self.base)['receipts_replayed'], 0)
        for flag in ('forecasting_enabled', 'model_training_enabled', 'promotion_allowed',
                     'feature_collection_enabled', 'source_scope_complete',
                     'receipt_clock_independently_attested', 'official_final_results_verified'):
            self.assertIs(result[flag], False)
        self.assertIs(result['NO_BET'], True); self.assertEqual(result['actual_wagers'], 0)

    def test_v1_true_envelope_cannot_be_enrolled_in_v2(self):
        with self.assertRaises(ValueError):
            self.collect(raw=games_fixture.GamesPageTests.raw)
        self.assertFalse((self.base/v2.ROOT).exists())

    def test_repeated_timestamp_never_overwrites(self):
        self.collect(); folder = self.folder()
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        with self.assertRaises(FileExistsError):
            self.collect(started=START+timedelta(seconds=1), received=START+timedelta(seconds=1))
        self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})

    def test_corrupt_or_symlinked_archive_blocks_http(self):
        self.collect(); folder = self.folder()
        outside = self.base/'relocated'
        folder.rename(outside); folder.symlink_to(outside, target_is_directory=True)
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, 'Unexpected NBA daily archive entry'): self.collect()
        self.assertEqual(self.calls, [])

    def test_tampered_manifest_and_raw_body_cannot_replay(self):
        self.collect(); folder = self.folder()
        manifest = folder/'manifest.json'; original = manifest.read_bytes()
        value = json.loads(original); value['forecasting_enabled'] = True
        manifest.write_bytes(espn.canonical(value))
        with self.assertRaisesRegex(ValueError, 'exact source replay'):
            v2.replay(self.base, folder.name, now=START+timedelta(seconds=2))
        manifest.write_bytes(original)
        (folder/'nba_games.html.gz').write_bytes(gzip.compress(self.raw+b' '))
        with self.assertRaisesRegex(ValueError, 'exact source replay'):
            v2.replay(self.base, folder.name, now=START+timedelta(seconds=2))

    def test_stale_provider_and_invalid_receipt_clock_do_not_write(self):
        with self.assertRaisesRegex(ValueError, 'stale or future'):
            self.collect(started=START+timedelta(hours=13))
        self.assertEqual(self.calls, [])
        with self.assertRaises(ValueError):
            self.collect(received=START-timedelta(seconds=1))
        self.assertFalse((self.base/v2.ROOT).exists())

    def test_every_game_requires_exact_unique_future_provider_agreement(self):
        raw, _, provider = v1._provider(self.base, PROVIDER_STAMP)
        key = next(k for k, g in provider.items() if g['home_tricode'] == 'DET')
        variants = []
        for change in ({'state': 'in'}, {'season_stage': 1}, {'provider_completed': True},
                       {'scheduled_start_utc': '2026-10-20T19:01:00+00:00'},
                       {'home_tricode': 'BOS'}):
            changed = copy.deepcopy(provider); changed[key].update(change); variants.append(changed)
        missing = copy.deepcopy(provider); del missing[key]; variants.append(missing)
        duplicate = copy.deepcopy(provider); duplicate['synthetic-duplicate'] = copy.deepcopy(provider[key])
        variants.append(duplicate)
        for changed in variants:
            with self.subTest(changed=changed.get(key)), self.assertRaises(ValueError):
                v1._build(self.raw, raw, changed, started=START,
                          received=START+timedelta(seconds=1), day='2026-10-20',
                          season='2026-27', stamp=PROVIDER_STAMP, offset=0,
                          _protocol=v2.PROTOCOL)

    def test_v1_archive_replays_identically_after_v2_collection(self):
        source = SOURCE/v1.ROOT/'20261020T114514510380Z'
        dest = self.base/v1.ROOT/source.name; shutil.copytree(source, dest)
        # The v1 receipt links another provider capture; retain that dependency.
        saved = json.loads((source/'manifest.json').read_text())
        linked = saved['espn_capture']
        dependency = self.base/espn.ROOT/'captures'/linked
        if not dependency.exists():
            shutil.copytree(SOURCE/espn.ROOT/'captures'/linked, dependency)
        before = {p.name: p.read_bytes() for p in dest.iterdir()}
        # Linked captures later than START must not be used for this synthetic
        # collection. Remove only the copied dependency after replaying v1.
        first = v1.replay(self.base, source.name)
        if linked != PROVIDER_STAMP: shutil.rmtree(dependency)
        self.collect()
        if linked != PROVIDER_STAMP:
            shutil.copytree(SOURCE/espn.ROOT/'captures'/linked, dependency)
        second = v1.replay(self.base, source.name)
        self.assertEqual(first['capture'], second['capture'])
        self.assertEqual(first['strict_pregame_correlated'], second['strict_pregame_correlated'])
        self.assertIs(second['source_replay_verified'], True)
        self.assertEqual(before, {p.name: p.read_bytes() for p in dest.iterdir()})

    def test_cli_is_inert_without_explicit_collection(self):
        with patch('sys.argv', ['v2']), patch.object(v2, 'collect') as collect, patch('builtins.print') as output:
            v2.main(); collect.assert_not_called()
        self.assertIs(json.loads(output.call_args.args[0])['collection_requested'], False)

    def test_retained_native_v2_receipts_replay(self):
        report = v2.replay_all(SOURCE)
        self.assertEqual(report['schema'], v2.PROTOCOL.audit_schema)
        for result in report['reports']:
            self.assertIs(result['source_replay_verified'], True)


if __name__ == '__main__': unittest.main()
