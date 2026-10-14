import hashlib
import shutil
import json
import tempfile
import unittest
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
import sports_benchmark_review as r
import sports_benchmark_coverage as c
import sports_market_evidence as m
import sports_prospective_test as n


class MarketEvidenceTests(unittest.TestCase):
    start = r.utc('2026-10-12T21:00:00Z')

    def fixture(self, root, event_edits=None, observed=None, priced=False):
        pred = {'game_id': '1', 'event_id': 'e1', 'home': 'MIL', 'away': 'LAD',
                'kickoff': self.start.isoformat(), 'recorded_at': (self.start-timedelta(hours=20)).isoformat(),
                'market': {'original': True} if priced else None}
        pred['sha256'] = r.digest(pred)
        n.write_json(root/'predictions/1.json', pred)
        event = {key: pred[key] for key in ('event_id', 'home', 'away', 'kickoff')}
        event.update({'state': 'pre', 'completed': False,
                      'odds': [{'provider': 'fixture', 'home_moneyline': 113, 'away_moneyline': -136}]})
        event.update(event_edits or {})
        capture = n.Capture(root/'capture')
        capture.retain('events.json', [event], {'source_url': 'https://example.com/scoreboard?dates=20261012',
                                             'retrieved_at': (observed or self.start-timedelta(hours=10)).isoformat()})
        return pred, event, capture

    def test_current_pairs_only_invalid_records_do_not_discard_other_quotes(self):
        good = {'provider': {'name': 'test'}, 'moneyline': {'home': {'close': {'odds': '-120'}}, 'away': {'close': {'odds': '+100'}}}}
        bad = deepcopy(good); bad['moneyline']['home']['close']['odds'] = 'OFF'
        opening = {'moneyline': {'home': {'open': {'odds': '-120'}}, 'away': {'open': {'odds': '100'}}}}
        one_side = deepcopy(good); del one_side['moneyline']['away']
        quotes, diagnosis = m.parse_odds([bad, opening, one_side, good])
        self.assertEqual(len(quotes), 1)
        self.assertEqual(diagnosis['issues'], ['invalid_current_moneyline', 'paired_current_moneyline_missing', 'paired_current_moneyline_missing'])
        self.assertAlmostEqual(m.market(quotes[0])['conditional_home_probability'], (120/220)/(120/220+.5))
        self.assertEqual(m.parse_odds([])[1]['status'], 'no_provider_odds')
        bad['moneyline']['home']['close']['odds'] = 99
        self.assertEqual(m.parse_odds([bad])[0], [])

    def test_followup_is_separate_append_only_linked_and_pregame(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); pred, event, capture = self.fixture(root)
            before = (root/'predictions/1.json').read_bytes()
            clock = lambda: self.start-timedelta(hours=9)
            self.assertEqual(m.collect_followups(root, capture, [event], clock), (['1'], []))
            data = json.loads((root/'market_followups/1.json').read_text())
            m.verify_quote(data, pred)
            self.assertEqual(data['prediction_sha256'], pred['sha256'])
            self.assertEqual(before, (root/'predictions/1.json').read_bytes())
            event['odds'][0]['home_moneyline'] = 200
            self.assertEqual(m.collect_followups(root, capture, [event], clock), ([], []))
            self.assertEqual(data, json.loads((root/'market_followups/1.json').read_text()))
            self.assertFalse((root/'results').exists())

    def test_followup_rejects_wrong_event_identity_state_duplicates_or_timestamps(self):
        edits = [{'home': 'TB'}, {'away': 'CLE'}, {'event_id': 'other'},
                 {'kickoff': (self.start+timedelta(minutes=15)).isoformat()},
                 {'state': 'in'}, {'completed': True}]
        for edit in edits:
            with self.subTest(edit=edit), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); pred, event, capture = self.fixture(root, edit)
                new, errors = m.collect_followups(root, capture, [event], lambda: self.start-timedelta(hours=9))
                self.assertFalse(new); self.assertTrue(errors)
                self.assertFalse((root/'market_followups/1.json').exists())
        for observed, clock in [(self.start+timedelta(seconds=1), self.start-timedelta(hours=9)),
                                (self.start-timedelta(hours=10), self.start),
                                (self.start-timedelta(hours=21), self.start-timedelta(hours=9))]:
            with self.subTest(observed=observed, clock=clock), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _, event, capture = self.fixture(root, observed=observed)
                self.assertEqual(m.collect_followups(root, capture, [event], lambda: clock)[0], [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, event, capture = self.fixture(root)
            new, errors = m.collect_followups(root, capture, [event, event], lambda: self.start-timedelta(hours=9))
            self.assertFalse(new); self.assertTrue(errors)

    def test_followup_requires_matching_hashed_snapshot_and_valid_forecast(self):
        for corrupt in ('snapshot', 'forecast', 'missing_snapshot'):
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _, event, capture = self.fixture(root)
                if corrupt == 'snapshot': Path(capture.evidence[0]['path']).write_text(json.dumps([event])+' ')
                if corrupt == 'missing_snapshot': capture.evidence = []
                if corrupt == 'forecast':
                    path = root/'predictions/1.json'; data = json.loads(path.read_text()); data['home'] = 'BAD'; n.write_json(path, data)
                new, errors = m.collect_followups(root, capture, [event], lambda: self.start-timedelta(hours=9))
                self.assertFalse(new); self.assertTrue(errors)

    def test_no_prices_or_already_priced_never_write_followup(self):
        for priced in (False, True):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _, event, capture = self.fixture(root, {'odds': []}, priced=priced)
                self.assertEqual(m.collect_followups(root, capture, [event], lambda: self.start-timedelta(hours=9)), ([], []))

    def test_matching_date_timestamp_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); pred, event, capture = self.fixture(root)
            capture.evidence.insert(0, {'source_url': 'https://example.com/scoreboard?dates=other',
                                      'retrieved_at': (self.start-timedelta(days=2)).isoformat(),
                                      'path': str(root/'empty.json')})
            (root/'empty.json').write_text('[]')
            self.assertEqual(m.collect_followups(root, capture, [event], lambda: self.start-timedelta(hours=9)), (['1'], []))
            quote = json.loads((root/'market_followups/1.json').read_text())
            self.assertEqual(quote['observed_at'], capture.evidence[1]['retrieved_at'])


class CoverageAuditTests(unittest.TestCase):
    def test_archived_counts_missing_odds_and_later_prices_without_writes(self):
        for sport, (folder, models) in r.COHORTS.items():
            original = Path(folder)
            # Pin the archived replay, so later enrollment does not change this
            # regression's expected denominator or missing-price examples.
            cutoff = r.utc('2026-10-14T15:32:56Z')
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                name = 'config.json' if sport == 'NFL' else 'model.json'
                shutil.copy(original/name, root/name)
                for kind in ('predictions', 'results'):
                    (root/kind).mkdir()
                    for path in (original/kind).glob('*.json'):
                        at = json.loads(path.read_text())['recorded_at' if kind == 'predictions' else 'verified_at']
                        if r.utc(at) <= cutoff: shutil.copy(path, root/kind/path.name)
                for path in (original/'captures').glob('*/manifest.json'):
                    if c.stamp(path.parent) <= cutoff:
                        (root/'captures'/path.parent.name).mkdir(parents=True)
                        shutil.copy(path, root/'captures'/path.parent.name/path.name)
                        if (path.parent/'enrollment.json').exists(): shutil.copy(path.parent/'enrollment.json', root/'captures'/path.parent.name/'enrollment.json')
                tracked = list((root/'predictions').glob('*.json'))+list((root/'results').glob('*.json'))
                before = {path: path.read_bytes() for path in tracked}
                data = c.audit(root, sport, models)
                self.assertEqual(before, {path: path.read_bytes() for path in tracked})
            self.assertEqual(data['observed_missing_started_games'], [])
            self.assertEqual(data['started_schedule_games_in_scope'], {'NFL': 13, 'NHL': 22, 'MLB': 4}[sport])
            self.assertEqual(data['decisive_market_paired'], {'NFL': 12, 'NHL': 22, 'MLB': 2}[sport])
            self.assertGreater(data['largest_capture_intervals'][0]['hours'], 5)
            self.assertEqual(data['followup_quotes_separate_from_original_metrics'], [])
            if sport == 'MLB':
                self.assertEqual({row['game_id'] for row in data['market_gaps']}, {'849812', '849813'})
                for row in data['market_gaps']:
                    later = row['later_archived_pregame_quote']
                    self.assertIsNotNone(later)
                    self.assertLess(r.utc(later['observed_at']), r.utc(row['kickoff']))
                    self.assertEqual(later['usage'], 'historical_evidence_only_not_backfilled')

    def fixture(self, root, remove_predictions=False, observation='2026-10-12T10:00:00Z', state='post', bad_hash=False):
        # Small synthetic audit universe: no scoring records are needed.
        (root/'predictions').mkdir(); (root/'results').mkdir()
        n.write_json(root/'model.json', {'frozen_at': '2026-10-11T16:00:00Z'})
        rows = [{'game_id': '1', 'kickoff': '2026-10-12T21:00:00Z', 'home': 'H', 'away': 'A', 'state': 'pre'},
                {'game_id': 'before', 'kickoff': '2026-10-11T15:59:00Z', 'home': 'H', 'away': 'A', 'state': 'post'}]
        cap = n.Capture(root/'captures/20261012T100000000000Z')
        cap.retain('official.json', rows, {'source_url': 'https://api-web.nhle.com/v1/schedule/2026-10-12', 'retrieved_at': observation})
        n.write_json(cap.folder/'manifest.json', {'sources': cap.evidence, 'collection_completed': True})
        rows[0]['state'] = state
        cap2 = n.Capture(root/'captures/20261013T100000000000Z')
        cap2.retain('official.json', rows, {'source_url': 'https://api-web.nhle.com/v1/schedule/2026-10-12', 'retrieved_at': '2026-10-13T10:00:00Z'})
        if bad_hash: cap2.evidence[0]['sha256'] = 'bad'
        n.write_json(cap2.folder/'manifest.json', {'sources': cap2.evidence, 'collection_completed': True})

    def test_missed_opportunity_absent_window_and_unknown_schedule_are_distinct(self):
        cases = [('2026-10-12T10:00:00Z', 'post', 'missed_despite_pregame_schedule_observation'),
                 ('2026-10-11T16:00:00Z', 'post', 'missed_without_pregame_schedule_observation_in_window'),
                 ('2026-10-12T10:00:00Z', 'in', 'unverified_or_not_normally_scheduled')]
        for observed, state, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.fixture(root, observation=observed, state=state)
                data = c.audit(root, 'NHL', ('model', 'fixed_elo'))
                self.assertEqual(len(data['games']), 1)
                self.assertEqual(data['games'][0]['status'], expected)
                self.assertEqual(len(data['observed_missing_started_games']), int(expected.startswith('missed_')))

    def test_snapshot_integrity_failure_withholds_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root, bad_hash=True)
            with self.assertRaisesRegex(ValueError, 'hash mismatch'): c.audit(root, 'NHL', ('model', 'fixed_elo'))

    def test_future_schedule_is_pending_not_missing_and_incomplete_capture_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            path = root/'captures/20261013T100000000000Z/manifest.json'
            data = json.loads(path.read_text()); data['collection_completed'] = False; n.write_json(path, data)
            data = c.audit(root, 'NHL', ('model', 'fixed_elo'))
            self.assertEqual(data['games'][0]['status'], 'awaiting_enrollment')
            self.assertEqual(data['observed_missing_started_games'], [])
            self.assertEqual(data['saved_collector_errors'][0]['error'], 'collection_incomplete')

    def test_one_bad_cohort_does_not_suppress_other_audits(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for folder, _ in r.COHORTS.values(): (base/folder).mkdir(parents=True)
            with patch.object(c, 'audit', side_effect=[ValueError('corrupt'), {'sport':'NHL','input_integrity':'verified','saved':0,'settled':0,'decisive_market_paired':0,'observed_missing_started_games':[]}, {'sport':'MLB','input_integrity':'verified','saved':0,'settled':0,'decisive_market_paired':0,'observed_missing_started_games':[]}]), patch.object(c, 'render', return_value='fixture'):
                reports = c.run(base)
            self.assertEqual([d['input_integrity'] for d in reports], ['error', 'verified', 'verified'])


if __name__ == '__main__':
    unittest.main()
