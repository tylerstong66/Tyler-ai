import base64
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

import sports_mlb_cohort_publication as publication
import test_sports_mlb_cross_cohort_audit as fixtures

NOW = datetime(2026, 10, 19, 18, tzinfo=timezone.utc)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); team, hitter = fixtures.seed(self.base)
        self.assignments = {p.relative_to(self.base).as_posix(): 100 for p in (team, hitter)}
        self.run = {'id': 100, 'repository': {'full_name': publication.REPOSITORY},
            'head_repository': {'full_name': publication.REPOSITORY}, 'head_sha': 'a'*40,
            'event': 'schedule', 'path': publication.WORKFLOW, 'created_at': '2026-10-16T20:00:00Z'}
        self.mutation = None; self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        if '/actions/runs/' in url: return deepcopy(self.run)
        path = url.split('/contents/')[1].split('?ref=')[0]
        raw = (self.base/path).read_bytes()
        item = {'type': 'file', 'path': path, 'size': len(raw), 'encoding': 'base64',
            'sha': hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
            'content': base64.b64encode(raw).decode()}
        if self.mutation: self.mutation(item)
        return item

    def build(self, assignments=None):
        return publication.audit(self.assignments if assignments is None else assignments,
                                 base=self.base, now=NOW, fetch=self.fetch)

    def test_exact_original_winner_and_hitter_blobs_before_separate_starts(self):
        report = self.build()
        self.assertEqual(report['forecast_files_verified'], 2)
        self.assertEqual(report['winner_records_verified'], 1)
        self.assertEqual(report['hitter_records_verified'], 1)
        self.assertFalse(report['original_source_validation_complete'])
        self.assertTrue(report['saved_report_requires_fresh_api_replay'])
        self.assertTrue(report['NO_BET']); self.assertEqual(report['actual_wagers'], 0)
        self.assertTrue(all('?ref='+'a'*40 in u for u in self.calls if '/contents/' in u))

    def test_wrong_run_repository_event_workflow_or_head_is_rejected(self):
        original = deepcopy(self.run)
        for key, value in [('id', True), ('id', 101), ('repository', {'full_name': 'other/repo'}),
                ('head_repository', {'full_name': 'fork/repo'}), ('path', 'other.yml'),
                ('event', 'push'), ('head_sha', 'main')]:
            with self.subTest(key=key):
                self.run = deepcopy(original); self.run[key] = value
                with self.assertRaises(ValueError): self.build()
        self.run = original

    def test_late_for_one_cohort_cannot_be_accepted_using_other_later_start(self):
        self.run['created_at'] = '2026-10-16T22:00:00Z'
        with self.assertRaises(ValueError): self.build()

    def test_before_freeze_or_future_server_timestamp_fails(self):
        for timestamp in ('2026-10-16T17:00:00Z', '2026-10-20T01:00:00Z'):
            self.run['created_at'] = timestamp
            with self.assertRaises(ValueError): self.build()

    def test_hash_size_type_path_and_decoded_bytes_all_must_match(self):
        for key, value in [('sha', 'b'*40), ('type', 'symlink'), ('size', True), ('path', 'wrong.json'),
                ('encoding', 'utf-8'), ('content', '!!!'), ('content', base64.b64encode(b'other').decode())]:
            with self.subTest(key=key):
                self.mutation = lambda item: item.update({key: value})
                with self.assertRaises(ValueError): self.build()
        self.mutation = None

    def test_empty_unknown_or_boolean_run_assignment_fails_before_requests(self):
        for assignments in ({}, {'../other.json': 100}, {next(iter(self.assignments)): True}):
            self.calls = []
            with self.assertRaises(ValueError): self.build(assignments)
            self.assertEqual(self.calls, [])

    def test_original_file_race_is_rejected(self):
        inputs = publication._inputs(self.base)
        path = next(iter(inputs)); run = publication._run(100, NOW, self.fetch)
        with self.assertRaisesRegex(ValueError, 'changed during'):
            publication._file(path, inputs[path], b'changed after replay', run, self.fetch)

    def test_saved_recipe_replays_server_and_rejects_coordinated_boolean_guard(self):
        report = self.build(); path = self.base/'report.json'; fixtures.write(path, report)
        self.calls = []
        publication.replay(path, base=self.base, now=NOW, fetch=self.fetch)
        self.assertEqual(len(self.calls), 3)
        report['actual_wagers'] = False; fixtures.write(path, report)
        with self.assertRaisesRegex(ValueError, 'fresh API replay'):
            publication.replay(path, base=self.base, now=NOW, fetch=self.fetch)

    def test_original_recipe_remains_fixed_when_additional_hitter_records_arrive(self):
        report = self.build(); path = self.base/'report.json'; fixtures.write(path, report)
        original_path = next((self.base/publication.cohorts.HITTER_ROOT/'predictions').glob('*.json'))
        extra = json.loads(original_path.read_text()); extra.pop('record_digest_sha256'); extra['hitter_id'] = 650490
        for receipt in extra['source_receipts']['hitter_game_logs']:
            receipt['source_url'] = receipt['source_url'].replace('608070', '650490')
        fixtures.write(original_path.with_name('849817_650490.json'), publication.cohorts.props._seal(extra))
        result = publication.replay(path, base=self.base, now=NOW, fetch=self.fetch)
        self.assertEqual(result['forecast_files_verified'], 2)
        self.assertEqual(result['assignments'], self.assignments)

    def test_naive_clock_and_invalid_saved_report_fail(self):
        with self.assertRaises(ValueError):
            publication.audit(self.assignments, base=self.base, now=datetime(2026, 10, 19))
        path = self.base/'report.json'; path.symlink_to(next((self.base/publication.cohorts.TEAM_ROOT/'predictions').glob('*.json')))
        with self.assertRaises(ValueError): publication.replay(path, base=self.base)


if __name__ == '__main__': unittest.main()
