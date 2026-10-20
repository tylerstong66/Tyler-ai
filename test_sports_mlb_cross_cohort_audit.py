from copy import deepcopy
from pathlib import Path
import hashlib
import json
import tempfile
import unittest

import sports_mlb_cross_cohort_audit as audit

TEAM_START = '2026-10-16T22:00:00Z'
HITTER_START = '2026-10-17T00:00:00Z'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def seed(base, *, hitter_start=HITTER_START, archived=False):
    official = [{'game_id': '849817', 'home_id': '114', 'away_id': '139',
                 'kickoff': TEAM_START, 'state': 'pre', 'completed': False}]
    provider = [{'event_id': '401908026', 'home': 'CLE', 'away': 'TB',
                 'kickoff': TEAM_START, 'state': 'pre', 'completed': False}]
    sources = []
    for uri, payload in [('https://statsapi.mlb.com/api/v1/schedule?date=2026-10-16', official),
            ('https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates=20261016', provider)]:
        raw = audit.review.canonical(payload)+b'\n'; digest = hashlib.sha256(raw).hexdigest()
        path = audit.TEAM_ROOT/'snapshots'/(digest+'.json')
        (base/path).parent.mkdir(parents=True, exist_ok=True); (base/path).write_bytes(raw)
        sources.append({'path': path.as_posix(), 'sha256': digest, 'response_sha256': 'a'*64,
                        'source_url': uri, 'retrieved_at': '2026-10-15T22:19:00Z'})
    team = {'sport': 'MLB', 'game_id': '849817', 'event_id': '401908026',
        'home_id': '114', 'away_id': '139', 'home': 'CLE', 'away': 'TB',
        'kickoff': TEAM_START, 'generated_at': '2026-10-15T22:19:23Z',
        'recorded_at': '2026-10-15T22:19:24Z', 'source_snapshots': sources,
        'NO_BET': True, 'actual_wagers': 0}
    team['sha256'] = audit.review.digest(team)
    team_path = base/audit.TEAM_ROOT/'predictions/849817.json'; write(team_path, team)
    def receipt(uri, data=None):
        r = {'source_url': uri, 'retrieved_at': '2026-10-16T18:10:30Z',
             'data_through': '2026-10-16T18:10:30Z', 'response_sha256': 'b'*64}
        if archived:
            data = data if data is not None else {'data': 'retained'}
            r['response_sha256'] = audit.archives.canonical_digest(data)
            raw = json.dumps(data, indent=2).encode()
            r.update(audit.archives.retain(base/audit.HITTER_ROOT/'source_archives', raw, r['response_sha256']))
        return r
    feed = {'gamePk': 849817, 'gameData': {'status': {'abstractGameState': 'Preview', 'detailedState': 'Scheduled'},
            'datetime': {'dateTime': hitter_start}, 'teams': {'home': {'id': 114}, 'away': {'id': 139}}}}
    hitter = {'schema': audit.props.SPORTS_VERSION, 'model': audit.props.MODEL_NAME,
        'game_id': 849817, 'hitter_id': 608070, 'hitter_side': 'home', 'hitter_team_id': 114,
        'opponent_team_id': 139, 'event_start_utc': hitter_start,
        'source_capture_started_at_utc': '2026-10-16T18:10:00Z', 'frozen_at_utc': '2026-10-16T18:10:39Z',
        'status': 'IMMUTABLE_PREGAME_SHADOW_NO_BET', 'sportsbook_wager_eligible': False,
        'model_calibrated': False, 'actual_wager': 0,
        'source_receipts': {'pregame_game': receipt('https://statsapi.mlb.com/api/v1.1/game/849817/feed/live', feed),
            'active_roster': receipt('https://statsapi.mlb.com/api/v1/teams/114/roster?date=2026-10-16&rosterType=active'),
            'hitter_game_logs': [receipt('https://statsapi.mlb.com/api/v1/people/608070/stats?gameType=R&group=hitting&season='+year+'&stats=gameLog') for year in ('2025', '2026')]}}
    hitter_path = base/audit.HITTER_ROOT/'predictions/849817_608070.json'
    write(hitter_path, audit.props._seal(hitter))
    return team_path, hitter_path


def edit_team(path, mutate):
    data = json.loads(path.read_text()); data.pop('sha256'); mutate(data)
    data['sha256'] = audit.review.digest(data); write(path, data)


def edit_hitter(path, mutate):
    data = json.loads(path.read_text()); data.pop('record_digest_sha256'); mutate(data)
    write(path, audit.props._seal(data))


class CrossCohortTests(unittest.TestCase):
    def test_signed_drift_distinct_freezes_hashes_and_unresolved_original_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); tp, hp = seed(root); before = [p.read_bytes() for p in (tp, hp)]
            report = audit.build(root); row = report['comparisons'][0]
            self.assertEqual(row['hitter_minus_team_saved_start_minutes'], 120)
            self.assertFalse(row['same_contemporaneous_forecast'])
            self.assertNotEqual(row['team_cohort']['frozen_at_utc'], row['hitter_cohort']['frozen_at_utc'])
            self.assertIn('HITTER_LEGACY_SOURCE_BYTES_UNAVAILABLE', row['unresolved'])
            self.assertFalse(row['original_source_validation_complete'])
            self.assertEqual(before, [p.read_bytes() for p in (tp, hp)])
            self.assertFalse(report['prediction_scores_combined']); self.assertTrue(report['NO_BET'])

    def test_single_official_game_review_keeps_original_source_gaps(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); tp, hp = seed(root)
            original = (tp.read_bytes(), hp.read_bytes())
            report = audit.build(root)
            self.assertEqual(report['unique_games_with_saved_start_drift'], 1)
            self.assertEqual(len(report['game_level_source_evidence_review']), 1)
            group = report['game_level_source_evidence_review'][0]
            self.assertEqual(group['game_id'], 849817)
            self.assertEqual(group['distinct_hitter_forecasts'], 1)
            self.assertEqual(group['hitter_minus_team_start_minutes'], [120.0])
            self.assertIn('TEAM_REDUCED_SNAPSHOTS_DO_NOT_REPLAY_ORIGINAL_RESPONSES',
                          group['source_and_publication_gaps'])
            self.assertIn('INDEPENDENT_PUBLICATION_TIMES_NOT_ATTESTED',
                          group['source_and_publication_gaps'])
            self.assertFalse(group['all_hitter_original_responses_replayed'])
            self.assertFalse(group['team_original_response_bytes_replayed'])
            self.assertFalse(group['joint_accuracy_comparison_allowed'])
            self.assertEqual((tp.read_bytes(), hp.read_bytes()), original)
            self.assertIs(report['NO_BET'], True)
            self.assertEqual(report['actual_wagers'], 0)

    def test_zero_drift_still_does_not_merge_independent_cohorts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); seed(root, hitter_start=TEAM_START)
            report = audit.build(root)
            self.assertEqual(report['saved_start_drift_comparisons'], 0)
            self.assertFalse(report['comparisons'][0]['same_contemporaneous_forecast'])

    def test_cross_cohort_team_identity_cannot_be_repaired_by_rehashing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); _, hp = seed(root)
            edit_hitter(hp, lambda d: d.update(hitter_side='away'))
            with self.assertRaisesRegex(ValueError, 'inconsistent team'): audit.build(root)

    def test_original_reduced_source_tamper_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); tp, _ = seed(root)
            snapshot = root/json.loads(tp.read_text())['source_snapshots'][0]['path']
            snapshot.write_bytes(snapshot.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError, 'source bytes changed'): audit.build(root)

    def test_resealed_wrong_original_start_does_not_override_schedule(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); tp, _ = seed(root)
            edit_team(tp, lambda d: d.update(kickoff='2026-10-16T23:00:00Z'))
            with self.assertRaisesRegex(ValueError, 'schedule disagrees'): audit.build(root)

    def test_both_original_forecast_content_seals_are_required(self):
        for name in ('team', 'hitter'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                root = Path(td); tp, hp = seed(root); path = tp if name == 'team' else hp
                data = json.loads(path.read_text()); data['actual_wagers' if name == 'team' else 'actual_wager'] = 99
                write(path, data)
                with self.assertRaises(ValueError): audit.build(root)

    def test_bad_no_bet_and_boolean_wager_guards_fail_even_when_resealed(self):
        for name in ('team', 'hitter'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                root = Path(td); tp, hp = seed(root)
                if name == 'team': edit_team(tp, lambda d: d.update(actual_wagers=False))
                else: edit_hitter(hp, lambda d: d.update(actual_wager=False))
                with self.assertRaises(ValueError): audit.build(root)

    def test_future_or_wrong_endpoint_receipts_do_not_become_verified_sources(self):
        for kind in ('late', 'game', 'roster', 'logs'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                root = Path(td); _, hp = seed(root)
                def mutate(d):
                    receipts = d['source_receipts']
                    if kind == 'late': receipts['pregame_game']['retrieved_at'] = '2026-10-17T02:00:00Z'
                    elif kind == 'game': receipts['pregame_game']['source_url'] = 'https://statsapi.mlb.com/api/v1.1/game/849818/feed/live'
                    elif kind == 'roster': receipts['active_roster']['source_url'] = 'https://statsapi.mlb.com/api/v1/teams/139/roster?date=2026-10-16&rosterType=active'
                    else: receipts['hitter_game_logs'][1] = deepcopy(receipts['hitter_game_logs'][0])
                edit_hitter(hp, mutate)
                with self.assertRaises(ValueError): audit.build(root)

    def test_retained_original_hitter_bytes_are_replayed_but_team_raw_gap_remains(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); seed(root, archived=True)
            row = audit.build(root)['comparisons'][0]
            self.assertTrue(row['hitter_cohort']['all_original_responses_replayed'])
            self.assertTrue(row['hitter_cohort']['original_pregame_response_replayed'])
            self.assertNotIn('HITTER_LEGACY_SOURCE_BYTES_UNAVAILABLE', row['unresolved'])
            self.assertFalse(row['original_source_validation_complete'])

    def test_archived_feed_must_match_original_hitter_start(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); _, hp = seed(root, archived=True)
            edit_hitter(hp, lambda d: d.update(event_start_utc='2026-10-17T01:00:00Z'))
            with self.assertRaisesRegex(ValueError, 'differs from sealed'): audit.build(root)

    def test_missing_archived_response_is_not_silently_legacy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); _, hp = seed(root, archived=True)
            data = json.loads(hp.read_text()); name = data['source_receipts']['pregame_game']['source_archive_file']
            (root/audit.HITTER_ROOT/'source_archives'/name).unlink()
            with self.assertRaises(ValueError): audit.build(root)

    def test_path_traversal_or_symlinked_forecast_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); tp, _ = seed(root)
            edit_team(tp, lambda d: d['source_snapshots'][0].update(path='../outside.json'))
            with self.assertRaises(ValueError): audit.build(root)
            tp, _ = seed(root)
            original = root/'saved-team.json'; tp.rename(original); tp.symlink_to(original)
            with self.assertRaises(ValueError): audit.build(root)


if __name__ == '__main__': unittest.main()
