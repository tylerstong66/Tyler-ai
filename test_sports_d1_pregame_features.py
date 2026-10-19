from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

import sports_d1_pregame_features as f
import test_sports_ncaa_espn_identity as fixture

AT = datetime(2026, 11, 1, 14, tzinfo=timezone.utc)
NOW = AT+timedelta(minutes=20)
START = AT+timedelta(hours=3)


def history():
    rows = {}
    for i in range(9):
        start = datetime(2025, 12, 1, 17, tzinfo=timezone.utc)+timedelta(days=i*7)
        rows[str(401000000+i)] = {'league': 'NCAAM_D1', 'split': 'validation',
            'espn_game_id': str(401000000+i), 'ncaa_game_id': str(6000000+i),
            'home_team_id': '202', 'away_team_id': '101', 'home_score': 80+i, 'away_score': 73+i,
            'ncaa_start_utc': start.isoformat(), 'espn_start_utc': start.isoformat(),
            'observed_available_at_utc': (AT-timedelta(days=1)).isoformat(),
            'provider_team_names': {'home': 'Tulsa Golden Hurricane', 'away': 'Rice Owls'}}
    return {'source_records': rows, 'source_feature_report_sha256': 'a'*64,
            'historical_school_identity_manifest_sha256': 'b'*64}


class D1FeatureTests(unittest.TestCase):
    def seed(self, base):
        def ncaa(url):
            params = json.loads(parse_qs(urlparse(url).query)['variables'][0])
            row = fixture.official_game(when=int(START.timestamp()))
            row['startDate'] = '11/01/2026'
            return json.dumps({'data': {'contests': [row] if params['sportCode'] == 'MBB' else []}}).encode()
        f.ncaa.run(ncaa, base=base, now=AT, days_ahead=0)
        def espn(url):
            row = fixture.espn_game(start=START.isoformat())
            row['status']['type']['name'] = 'STATUS_SCHEDULED'
            return json.dumps({'count': 1, 'events': [row]}).encode() if 'basketball/mens-college-basketball' in url else b'{"count":0,"events":[]}'
        f.source.capture(espn, base=base, now=AT, days_ahead=0)
        f.identity.run(base=base, now=AT+timedelta(minutes=10))
        self.enterContext(patch.object(f, '_reference', return_value=history()))
        return (AT+timedelta(minutes=10)).strftime('%Y%m%dT%H%M%S%fZ')

    def test_real_daily_sources_freeze_last_eight_once_and_preserve_bytes_after_start(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); self.seed(base)
            status = f.inspect(base, now=NOW)
            self.assertEqual(status['current_d1_crosswalk_matches'], 1)
            self.assertTrue(status['d1_current_source_games_available'])
            self.assertFalse((base/f.ROOT).exists())
            self.assertEqual(f.inspect(base, now=NOW, collect=True)['new_feature_observations'], 1)
            path = next((base/f.ROOT).glob('*.json')); before = path.read_bytes()
            row = json.loads(before)['record']; home = row['reference_features']['home']
            self.assertEqual(row['reference_report_sha256'], f.digest(history()))
            self.assertEqual(home['prior_games'], 8)
            self.assertEqual(home['mean_margin'], 7)
            ids = {r['source_row']['espn_game_id'] for r in home['reference_source_rows']}
            self.assertNotIn('401000000', ids)
            self.assertEqual(f.inspect(base, now=NOW+timedelta(days=3))['verified_existing'], 1)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(f.inspect(base, now=NOW, collect=True)['new_feature_observations'], 0)

    def test_insufficient_late_or_wrong_name_history_cannot_be_substituted(self):
        for kind in ('missing', 'late', 'name'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); self.seed(base); ref = history()
                if kind == 'missing':
                    for key in list(ref['source_records'])[:2]: del ref['source_records'][key]
                elif kind == 'late':
                    for row in list(ref['source_records'].values())[:2]: row['observed_available_at_utc'] = (NOW+timedelta(hours=1)).isoformat()
                else: list(ref['source_records'].values())[-1]['provider_team_names']['home'] = 'Different School'
                f._reference.return_value = ref
                out = f.inspect(base, now=NOW, collect=True)
                self.assertEqual(out['new_feature_observations'], 0)
                self.assertEqual(len(out['not_enrolled']), 1)
                self.assertFalse((base/f.ROOT).exists())

    def test_rehashed_means_and_no_bet_guards_cannot_replace_original_replay(self):
        for field in ('mean', 'guard'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                base = Path(td); self.seed(base); f.inspect(base, now=NOW, collect=True)
                path = next((base/f.ROOT).glob('*.json')); saved = json.loads(path.read_bytes())
                if field == 'mean': saved['record']['reference_features']['home']['mean_margin'] += 1
                else: saved['record']['actual_wagers'] = False
                saved['record_sha256'] = f.digest(saved['record']); path.write_bytes(f.source.canonical(saved))
                with self.assertRaisesRegex(ValueError, 'original source replay'): f.inspect(base, now=NOW)

    def test_postponed_live_postseason_stale_and_started_targets_stay_unenrolled(self):
        for kind in ('postponed', 'live', 'postseason', 'stale', 'started'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); stamp = self.seed(base); snapshot = f._snapshot(base, stamp)
                e = next(iter(snapshot['rows']['espn'].values())); clock = NOW
                if kind == 'postponed': snapshot['espn_status_names'][e['espn_game_id']] = {'STATUS_POSTPONED'}
                elif kind == 'live': e['state'] = 'in'
                elif kind == 'postseason': e['season_stage'] = 3
                elif kind == 'stale':
                    for manifest in snapshot['source_manifests'].values(): manifest['recorded_at_utc'] = (NOW-timedelta(hours=13)).isoformat()
                else: clock = START
                with patch.object(f, '_snapshot', return_value=snapshot):
                    self.assertEqual(f.inspect(base, now=clock, collect=True)['new_feature_observations'], 0)

    def test_other_sport_and_reference_season_cannot_enter_d1_history(self):
        for kind in ('sport', 'season'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); self.seed(base); ref = history(); row = list(ref['source_records'].values())[-1]
                if kind == 'sport': row['league'] = 'NCAAF_FBS'
                else: row['espn_start_utc'] = '2024-12-01T17:00:00Z'
                f._reference.return_value = ref
                with self.assertRaises(ValueError): f.inspect(base, now=NOW, collect=True)

    def test_fixed_ncaa_season_url_remains_required_after_rehashing_crosswalk(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); stamp = self.seed(base)
            path = base/f.identity.ROOT/'captures'/stamp/'manifest.json'; walk = json.loads(path.read_bytes())
            original = base/f.ncaa.ROOT/'captures'/walk['ncaa_capture']/'manifest.json'
            manifest = json.loads(original.read_bytes())
            for snap in manifest['snapshots']:
                if snap['league'] == 'NCAAM_D1': snap['source_url'] = f.ncaa.graph_url('NCAAM_D1', year=2025, day=snap['window'])
            raw = f.source.canonical(manifest); original.write_bytes(raw)
            walk['ncaa_manifest_sha256'] = hashlib.sha256(raw).hexdigest(); path.write_bytes(f.source.canonical(walk))
            with self.assertRaises(ValueError): f.inspect(base, now=NOW, collect=True)

    def test_protocol_cannot_silently_switch_reference_window(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); path = base/f.ROOT.parent/'protocol.json'; path.parent.mkdir(parents=True)
            path.write_bytes(f.source.canonical(dict(f.PROTOCOL, reference_games_per_team=4)))
            with self.assertRaisesRegex(ValueError, 'protocol differs'): f._reference(base, NOW)

    def test_future_audit_clock_invalid_existing_or_symlink_source_stops_writes(self):
        for kind in ('future', 'existing', 'symlink'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); self.seed(base)
                if kind == 'future':
                    with self.assertRaisesRegex(ValueError, 'after audit clock'):
                        f.inspect(base, now=AT)
                    continue
                if kind == 'existing':
                    root = base/f.ROOT; root.mkdir(parents=True); (root/'123.json').write_text('{}')
                else:
                    source = next((base/f.ncaa.ROOT/'captures').glob('*/*.json.gz'))
                    original = base/'original.json.gz'; source.rename(original); source.symlink_to(original)
                with self.assertRaises((ValueError, KeyError)): f.inspect(base, now=NOW, collect=True)
                self.assertLessEqual(len(list((base/f.ROOT).glob('*.json'))), 1)

    def test_calendar_bounds_and_nonbijective_target_identity_remain_unenrolled(self):
        for kind in ('early', 'late', 'duplicate'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); stamp = self.seed(base); snapshot = f._snapshot(base, stamp)
                if kind == 'duplicate':
                    snapshot['manifest']['report']['matched'].append(deepcopy(snapshot['manifest']['report']['matched'][0]))
                else:
                    start = datetime(2026, 10, 29, tzinfo=timezone.utc) if kind == 'early' else datetime(2027, 4, 8, tzinfo=timezone.utc)
                    next(iter(snapshot['rows']['ncaa'].values()))['source_start_time_epoch'] = str(int(start.timestamp()))
                    next(iter(snapshot['rows']['espn'].values()))['scheduled_start_utc'] = start.isoformat()
                with patch.object(f, '_snapshot', return_value=snapshot):
                    out = f.inspect(base, now=NOW, collect=True)
                self.assertEqual(out['new_feature_observations'], 0)
                self.assertTrue(all(r['reason'] == ('NON_BIJECTIVE_SOURCE_GAME_IDENTITY' if kind == 'duplicate' else 'OUTSIDE_FIXED_D1_TARGET_SEASON') for r in out['not_enrolled']))

    def test_non_utc_clock_freezes_canonical_utc_bytes_that_replay(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); self.seed(base)
            clock = NOW.astimezone(timezone(timedelta(hours=-4)))
            self.assertEqual(f.inspect(base, now=clock, collect=True)['new_feature_observations'], 1)
            path = next((base/f.ROOT).glob('*.json')); before = path.read_bytes()
            self.assertEqual(json.loads(before)['record']['frozen_at_utc'], NOW.isoformat())
            self.assertEqual(f.inspect(base, now=NOW+timedelta(days=1))['verified_existing'], 1)
            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__': unittest.main()
