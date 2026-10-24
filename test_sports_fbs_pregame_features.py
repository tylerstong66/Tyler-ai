from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

import sports_fbs_pregame_features as features
import test_sports_ncaa_espn_identity as fixtures

NOW = fixtures.AT+timedelta(minutes=20)


def reference():
    rows = {}
    for i in range(4):
        start = datetime(2025, 12, 1+i*7, 17, tzinfo=timezone.utc).isoformat()
        rows[str(401000000+i)] = {'league': 'NCAAF_FBS', 'split': 'validation',
            'espn_game_id': str(401000000+i), 'ncaa_game_id': str(6000000+i),
            'home_team_id': '202', 'away_team_id': '101', 'home_score': 28+i, 'away_score': 21+i,
            'ncaa_start_utc': start, 'espn_start_utc': start,
            'observed_available_at_utc': (NOW-timedelta(days=1)).isoformat(),
            'provider_team_names': {'home': 'Tulsa Golden Hurricane', 'away': 'Rice Owls'}}
    return {'source_records': rows, 'source_feature_report_sha256': 'a'*64,
            'historical_school_identity_manifest_sha256': 'b'*64}


class FbsFeatureTests(unittest.TestCase):
    def test_non_utc_collection_clock_creates_replayable_canonical_utc_record(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); self.seed(base)
            clock = NOW.astimezone(timezone(timedelta(hours=-4)))
            features.inspect(base, now=clock, collect=True)
            path = next((base/features.ROOT).glob('*.json')); before = path.read_bytes()
            self.assertEqual(features.inspect(base, now=NOW+timedelta(days=1))['verified_existing'], 1)
            self.assertEqual(json.loads(before)['record']['frozen_at_utc'], NOW.isoformat())
            self.assertEqual(path.read_bytes(), before)

    def seed(self, base, *, later_start=False):
        kwargs = {}
        if later_start:
            start = datetime(2026, 10, 20, 17, tzinfo=timezone.utc)
            kwargs = {'ncaa_when': int(start.timestamp()), 'espn_when': start.isoformat()}
        original = fixtures.espn_game
        def event(*args, **kwargs):
            row = original(*args, **kwargs)
            row['status']['type']['name'] = 'STATUS_FINAL' if kwargs.get('completed') else 'STATUS_SCHEDULED'
            return row
        with patch.object(fixtures, 'espn_game', side_effect=event):
            fixtures.CollegeIdentityTests().seed(base, **kwargs)
        saved = features.identity.run(base=base, now=NOW-timedelta(minutes=10))
        self.enterContext(patch.object(features, '_reference', return_value=reference()))
        return saved['recorded_at_utc'], (NOW-timedelta(minutes=10)).strftime('%Y%m%dT%H%M%S%fZ')

    def test_original_receipts_freeze_once_and_replay_read_only_after_start(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); self.seed(base)
            self.assertEqual(features.inspect(base, now=NOW)['new_feature_observations'], 0)
            self.assertFalse((base/features.ROOT).exists())
            out = features.inspect(base, now=NOW, collect=True)
            self.assertEqual(out['new_feature_observations'], 1)
            path = next((base/features.ROOT).glob('*.json')); before = path.read_bytes()
            row = json.loads(before)['record']
            self.assertEqual(row['reference_features']['home']['prior_games'], 4)
            self.assertEqual(row['reference_features']['home']['mean_margin'], 7)
            self.assertTrue(row['not_a_prediction']); self.assertTrue(row['current_season_form_not_modeled'])
            self.assertEqual(features.inspect(base, now=NOW+timedelta(hours=1), collect=True)['new_feature_observations'], 0)
            self.assertEqual(features.inspect(base, now=NOW+timedelta(days=7))['verified_existing'], 1)
            self.assertEqual(path.read_bytes(), before)

    def test_rehashed_means_or_boolean_guards_cannot_replace_source_replay(self):
        for kind in ('mean', 'wager_bool', 'forecast', 'prediction_integer'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); self.seed(base); features.inspect(base, now=NOW, collect=True)
                path = next((base/features.ROOT).glob('*.json')); saved = json.loads(path.read_bytes())
                if kind == 'mean': saved['record']['reference_features']['home']['mean_margin'] += 1
                elif kind == 'wager_bool': saved['record']['actual_wagers'] = False
                elif kind == 'forecast': saved['record']['forecasting_enabled'] = True
                else: saved['record']['not_a_prediction'] = 1
                saved['record_sha256'] = features.digest(saved['record']); path.write_bytes(features.source.canonical(saved))
                with self.assertRaisesRegex(ValueError, 'original source replay'): features.inspect(base, now=NOW)

    def test_missing_or_late_history_stays_unenrolled(self):
        for kind in ('missing', 'late', 'name'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); self.seed(base); ref = reference()
                if kind == 'missing': ref['source_records'].pop(next(iter(ref['source_records'])))
                elif kind == 'late': next(iter(ref['source_records'].values()))['observed_available_at_utc'] = (NOW+timedelta(hours=1)).isoformat()
                else: next(iter(ref['source_records'].values()))['provider_team_names']['home'] = 'Other University'
                features._reference.return_value = ref
                out = features.inspect(base, now=NOW, collect=True)
                self.assertEqual(out['new_feature_observations'], 0)
                self.assertEqual(len(out['not_enrolled']), 1)
                self.assertFalse((base/features.ROOT).exists())

    def test_other_season_sport_or_duplicate_history_fails_closed(self):
        for kind in ('sport', 'season', 'duplicate'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); self.seed(base); ref = reference(); rows = list(ref['source_records'].values())
                if kind == 'sport': rows[0]['league'] = 'NCAAM_D1'
                elif kind == 'season': rows[0]['espn_start_utc'] = '2024-12-01T17:00:00Z'
                else: ref['source_records'][str(401000003)] = deepcopy(rows[2])
                features._reference.return_value = ref
                with self.assertRaises(ValueError): features.inspect(base, now=NOW, collect=True)
                self.assertFalse((base/features.ROOT).exists())

    def test_stale_or_started_sources_cannot_be_backfilled(self):
        for kind in ('stale', 'started'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); self.seed(base, later_start=True)
                clock = NOW+timedelta(hours=13) if kind == 'stale' else datetime(2026, 10, 20, 17, tzinfo=timezone.utc)
                out = features.inspect(base, now=clock, collect=True)
                self.assertEqual(out['new_feature_observations'], 0)
                self.assertEqual(out['not_enrolled'][0]['reason'], 'SCHEDULE_SOURCE_TOO_OLD_AT_FREEZE' if kind == 'stale' else 'SOURCE_SAVED_START_ALREADY_REACHED')

    def test_live_final_or_postseason_source_never_creates_feature_record(self):
        for kind in ('live', 'final', 'postseason'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); _, stamp = self.seed(base); snapshot = features._snapshot(base, stamp)
                e = next(iter(snapshot['rows']['espn'].values()))
                if kind == 'live': e['state'] = 'in'
                elif kind == 'final': e.update(state='post', provider_completed=True)
                else: e['season_stage'] = 3
                with patch.object(features, '_snapshot', return_value=snapshot):
                    self.assertEqual(features.inspect(base, now=NOW, collect=True)['new_feature_observations'], 0)

    def test_future_source_or_future_saved_freeze_fails(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); self.seed(base)
            with self.assertRaisesRegex(ValueError, 'after feature freeze'):
                features.inspect(base, now=fixtures.AT-timedelta(seconds=1), collect=True)
            features.inspect(base, now=NOW, collect=True)
            with self.assertRaisesRegex(ValueError, 'Future-dated'): features.inspect(base, now=NOW-timedelta(seconds=1))

    def test_invalid_existing_record_stops_all_new_writes(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); self.seed(base); root = base/features.ROOT; root.mkdir(parents=True)
            (root/'401000001.json').write_text('{}')
            with self.assertRaises((ValueError, KeyError)): features.inspect(base, now=NOW, collect=True)
            self.assertEqual(len(list(root.glob('*.json'))), 1)

    def test_source_corruption_or_symlink_fails_before_new_record(self):
        for kind in ('corrupt', 'symlink'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); self.seed(base)
                path = next((base/features.ncaa.ROOT/'captures').glob('*/manifest.json'))
                if kind == 'corrupt': path.write_bytes(b'{}')
                else:
                    original = base/'saved.json'; path.rename(original); path.symlink_to(original)
                with self.assertRaises((ValueError, KeyError)): features.inspect(base, now=NOW, collect=True)
                self.assertFalse((base/features.ROOT).exists())

    def test_nonbijective_current_crosswalk_never_creates_two_records(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); _, stamp = self.seed(base); snapshot = features._snapshot(base, stamp)
            snapshot['manifest']['report']['matched'].append(deepcopy(snapshot['manifest']['report']['matched'][0]))
            with patch.object(features, '_snapshot', return_value=snapshot):
                out = features.inspect(base, now=NOW, collect=True)
                self.assertEqual(out['new_feature_observations'], 0)
                self.assertTrue(all(r['reason'] == 'NON_BIJECTIVE_SOURCE_GAME_IDENTITY' for r in out['not_enrolled']))

    def test_protocol_and_clock_are_required(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError): features.inspect(Path(td), now=NOW)
        with self.assertRaises(ValueError): features.inspect(now=datetime(2026, 10, 19))
        with self.assertRaises(ValueError): features.inspect(now=NOW, collect=1)

    def test_rebound_source_year_or_boolean_guard_still_fails(self):
        for kind in ('year', 'ncaa_bool', 'espn_bool'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); _, stamp = self.seed(base)
                path = base/features.identity.ROOT/'captures'/stamp/'manifest.json'
                crosswalk = json.loads(path.read_bytes()); which = 'espn' if kind == 'espn_bool' else 'ncaa'
                root = features.source.ROOT if which == 'espn' else features.ncaa.ROOT
                manifest_path = base/root/'captures'/crosswalk[which+'_capture']/'manifest.json'
                saved = json.loads(manifest_path.read_bytes())
                if kind == 'year':
                    for snap in saved['snapshots']:
                        if snap['league'] == 'NCAAF_FBS':
                            snap['source_url'] = features.ncaa.graph_url('NCAAF_FBS', year=2025, week=int(snap['window'][5:]))
                else: saved['actual_wagers'] = False
                raw = features.source.canonical(saved); manifest_path.write_bytes(raw)
                crosswalk[which+'_manifest_sha256'] = hashlib.sha256(raw).hexdigest()
                path.write_bytes(features.source.canonical(crosswalk))
                with self.assertRaisesRegex(ValueError, 'target season' if kind == 'year' else
                                            'Invalid NCAA-owned research receipt' if kind == 'ncaa_bool'
                                            else 'research guards'):
                    features.inspect(base, now=NOW, collect=True)

    def test_digest_pinned_protocol_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); path = base/features.ROOT.parent/'protocol.json'; path.parent.mkdir(parents=True)
            changed = dict(features.PROTOCOL, reference_games_per_team=5)
            path.write_bytes(features.source.canonical(changed))
            with self.assertRaisesRegex(ValueError, 'protocol differs'): features._reference(base, NOW)

    def test_symlinked_response_is_rejected_before_source_parsing(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); self.seed(base)
            blob = next((base/features.ncaa.ROOT/'captures').glob('*/*.json.gz'))
            target = base/'original.json.gz'; blob.rename(target); blob.symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'bounded FBS source file'):
                features.inspect(base, now=NOW, collect=True)

    def test_postponed_delayed_missing_or_conflicting_provider_status_is_not_scheduled(self):
        for statuses in ({'STATUS_POSTPONED'}, {'STATUS_DELAYED'}, {None}, {'STATUS_SCHEDULED', 'STATUS_DELAYED'}):
            with self.subTest(statuses=statuses), tempfile.TemporaryDirectory() as td:
                base = Path(td); _, stamp = self.seed(base); snapshot = features._snapshot(base, stamp)
                snapshot['espn_status_names']['401100001'] = statuses
                with patch.object(features, '_snapshot', return_value=snapshot):
                    out = features.inspect(base, now=NOW, collect=True)
                    self.assertEqual(out['new_feature_observations'], 0)
                    self.assertEqual(out['not_enrolled'][0]['reason'], 'PROVIDER_STATUS_NOT_EXPLICITLY_SCHEDULED')


if __name__ == '__main__': unittest.main()
