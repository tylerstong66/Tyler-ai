"""Synthetic feature freezes over strictly replayed native-v2 source fixtures."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import sports_nba_native_pregame_features as features
import test_sports_nba_owned_daily_observation_v2 as receipt_fixtures


class NativeFeatureTests(unittest.TestCase):
    def setUp(self):
        fixture = receipt_fixtures.V2ObservationTests(); fixture.setUp()
        self.addCleanup(fixture.doCleanups); fixture.collect()
        self.base = fixture.base
        self.now = receipt_fixtures.START+timedelta(seconds=2)
        self.stamp = fixture.folder().name
        protocol = self.base/features.ROOT.parent/'protocol.json'
        protocol.parent.mkdir(parents=True); protocol.write_bytes(features.source.canonical(features.PROTOCOL))
        self.snapshot = features._snapshot(self.base, self.stamp, self.now)
        rows = []
        for index, game in enumerate(self.snapshot['official'].values()):
            for day in range(10):
                at = datetime(2026, 4, day+1, 19, tzinfo=timezone.utc).isoformat()
                rows.append({'nba_game_id': f'00225{index*10+day:05d}',
                    'home_tricode': game['home_tricode'], 'away_tricode': game['away_tricode'],
                    'home_score': 100+day, 'away_score': 90+day,
                    'nba_scheduled_start_utc': at, 'espn_scheduled_start_utc': at,
                    'corroboration_available_at_utc': (self.now-timedelta(days=2)).isoformat()})
        self.reference = {'corroborated_research_only': rows}
        # Only historical reference reconstruction is synthetic. Native receipt
        # and independently linked provider originals are exactly replayed.
        self.enterContext(patch.object(features.reference_features, '_reference', return_value=self.reference))

    def collect(self, at=None):
        return features.collect(self.base, clock=lambda: at or self.now)

    def test_exact_source_freeze_replays_and_never_overwrites_or_changes_v1(self):
        old = self.base/features.reference_features.ROOT/'sentinel'
        old.parent.mkdir(parents=True); old.write_bytes(b'synthetic untouched v1 sentinel')
        report = self.collect()
        self.assertEqual(report['new_feature_observations'], 3)
        paths = sorted((self.base/features.ROOT).glob('*.json'))
        before = {p.name: p.read_bytes() for p in paths}
        for path in paths:
            row = json.loads(path.read_bytes())['record']
            self.assertEqual(row['nba_native_daily_capture'], self.stamp)
            self.assertEqual(row['protocol_sha256'], features.PROTOCOL_SHA256)
            self.assertEqual(row['reference_features']['home']['prior_games'], 10)
            self.assertEqual(row['reference_features']['home']['mean_margin'], 10)
            self.assertTrue(row['not_a_prediction']); self.assertTrue(row['original_v1_features_unchanged'])
            self.assertTrue(row['NO_BET']); self.assertEqual(row['actual_wagers'], 0)
            for key in ('forecasting_enabled', 'model_training_enabled', 'historical_evaluation_enabled',
                        'promotion_allowed', 'source_scope_complete', 'full_season_schedule_verified',
                        'independent_publication_time_attested', 'actual_tipoff_time_attested'):
                self.assertIs(row[key], False)
        repeated = self.collect(self.now+timedelta(hours=1))
        self.assertEqual((repeated['verified_existing'], repeated['new_feature_observations']), (3, 0))
        self.assertEqual(features.audit(self.base, now=self.now+timedelta(days=7))['verified_feature_observations'], 3)
        self.assertEqual(before, {p.name: p.read_bytes() for p in paths})
        self.assertEqual(old.read_bytes(), b'synthetic untouched v1 sentinel')

    def test_non_utc_clock_is_normalized_and_reverse_or_overlong_interval_never_writes(self):
        self.collect(self.now.astimezone(timezone(timedelta(hours=-4))))
        path = next((self.base/features.ROOT).glob('*.json'))
        self.assertEqual(json.loads(path.read_bytes())['record']['frozen_at_utc'], self.now.isoformat())
        for end in (self.now-timedelta(seconds=1), self.now+timedelta(minutes=6)):
            times = iter([self.now, end])
            with self.assertRaisesRegex(ValueError, 'interval'):
                features.collect(self.base, clock=lambda: next(times))
        with self.assertRaisesRegex(ValueError, 'Aware'):
            self.collect(self.now.replace(tzinfo=None))

    def test_rehashed_feature_or_guard_edit_cannot_replace_exact_source_replay(self):
        self.collect(); path = next((self.base/features.ROOT).glob('*.json')); original = path.read_bytes()
        for key in ('statistics', 'guard', 'source', 'wagers'):
            value = json.loads(original)
            if key == 'statistics': value['record']['reference_features']['home']['mean_margin'] += 1
            elif key == 'guard': value['record']['forecasting_enabled'] = True
            elif key == 'source': value['record']['nba_response_sha256'] = 'a'*64
            else: value['record']['actual_wagers'] = False
            value['record_sha256'] = features.digest(value['record'])
            path.write_bytes(features.source.canonical(value))
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'original source replay'):
                self.collect()
        path.write_bytes(original)

    def test_started_stale_and_future_observed_sources_are_never_frozen(self):
        matched = self.snapshot['manifest']['matched'][0]
        n = self.snapshot['official'][matched['nba_official_game_id']]
        with self.assertRaisesRegex(ValueError, 'START_ALREADY_REACHED'):
            features._record(self.snapshot, matched, self.reference, features.source.utc(n['tipoff_utc']))
        with self.assertRaisesRegex(ValueError, 'chronology'):
            features._record(self.snapshot, matched, self.reference, self.now-timedelta(seconds=2))
        stale = copy.deepcopy(self.snapshot)
        stamp = (self.now+timedelta(days=2)).isoformat()
        stale['official'][matched['nba_official_game_id']]['tipoff_utc'] = stamp
        stale['provider'][matched['espn_game_id']]['scheduled_start_utc'] = stamp
        with self.assertRaisesRegex(ValueError, 'TOO_OLD'):
            features._record(stale, matched, self.reference, self.now+timedelta(hours=13))

    def test_nonunique_changed_teams_times_status_or_scope_fail(self):
        matched = self.snapshot['manifest']['matched'][0]
        for kind in ('duplicate', 'team', 'start', 'status', 'bool_status', 'completed', 'scope'):
            snap = copy.deepcopy(self.snapshot)
            n = snap['official'][matched['nba_official_game_id']]; e = snap['provider'][matched['espn_game_id']]
            if kind == 'duplicate': snap['manifest']['matched'].append(copy.deepcopy(matched))
            elif kind == 'team': e['home_tricode'] = 'OTHER'
            elif kind == 'start': e['scheduled_start_utc'] = (features.source.utc(n['tipoff_utc'])+timedelta(minutes=1)).isoformat()
            elif kind == 'status': n['nba_status'] = 2
            elif kind == 'bool_status': n['nba_status'] = True
            elif kind == 'completed': e['provider_completed'] = True
            else: e['season_stage'] = 1
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                features._record(snap, matched, self.reference, self.now)

    def test_late_missing_wrong_season_or_duplicate_reference_never_creates_partial_records(self):
        original = copy.deepcopy(self.reference)
        for kind in ('late', 'missing', 'season', 'duplicate'):
            reference = copy.deepcopy(original); rows = reference['corroborated_research_only']
            if kind == 'late': rows[0]['corroboration_available_at_utc'] = (self.now+timedelta(seconds=1)).isoformat()
            elif kind == 'missing': rows.pop(0)
            elif kind == 'season': rows[0]['nba_game_id'] = '0022400000'
            else: rows[1] = copy.deepcopy(rows[0])
            features.reference_features._reference.return_value = reference
            if kind in ('season', 'duplicate'):
                with self.assertRaises(ValueError): self.collect()
                self.assertFalse((self.base/features.ROOT).exists())
            else:
                report = self.collect()
                self.assertEqual(report['new_feature_observations'], 2)
                self.assertEqual(len(report['not_enrolled']), 1)
                for p in (self.base/features.ROOT).glob('*.json'): p.unlink()
                (self.base/features.ROOT).rmdir()

    def test_corrupt_original_source_or_symlinked_destination_blocks_all_new_records(self):
        manifest = self.base/features.receipts.ROOT/self.stamp/'manifest.json'
        original = manifest.read_bytes(); value = json.loads(original); value['forecasting_enabled'] = True
        manifest.write_bytes(features.source.canonical(value))
        with self.assertRaises(ValueError): self.collect()
        self.assertFalse((self.base/features.ROOT).exists()); manifest.write_bytes(original)
        folder = self.base/features.ROOT.parent; outside = self.base/'moved-native-root'
        folder.rename(outside); folder.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError): self.collect()
        self.assertFalse((outside/'records').exists())

    def test_changed_protocol_and_unplanned_feature_files_fail(self):
        path = self.base/features.ROOT.parent/'protocol.json'; original = path.read_bytes()
        path.write_bytes(original+b' ')
        with self.assertRaisesRegex(ValueError, 'protocol'): self.collect()
        path.write_bytes(original)
        folder = self.base/features.ROOT; folder.mkdir(); (folder/'unknown.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'feature file'): self.collect()

    def test_cli_defaults_to_no_collection_without_protocol_or_sources(self):
        result = subprocess.run([sys.executable, str(Path(features.__file__).resolve())],
                                cwd=self.base/'..', capture_output=True, text=True, check=True)
        self.assertFalse(json.loads(result.stdout)['collection_requested'])
        self.assertFalse((self.base/features.ROOT).exists())


if __name__ == '__main__': unittest.main()
