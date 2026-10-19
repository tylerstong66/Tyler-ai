import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import sports_nba_feature_publication as publication


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 19, 17, tzinfo=timezone.utc)
        self.records = {'0022600001': {'nba_game_id': '0022600001',
            'frozen_at_utc': '2026-10-19T13:33:00Z',
            'nba_saved_start_utc': '2026-10-20T19:00:00Z',
            'espn_saved_start_utc': '2026-10-20T19:05:00Z'}}
        self.raw = {'0022600001': b'exact original feature bytes\n'}
        self.run = {'id': 123, 'repository': {'full_name': publication.REPOSITORY},
            'head_repository': {'full_name': publication.REPOSITORY},
            'head_sha': 'a' * 40, 'path': publication.WORKFLOW,
            'event': 'pull_request', 'created_at': '2026-10-19T13:43:22Z'}
        raw = self.raw['0022600001']
        self.item = {'type': 'file', 'path': (publication.features.ROOT / '0022600001.json').as_posix(),
            'sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(),
            'size': len(raw), 'encoding': 'base64', 'content': base64.b64encode(raw).decode()}
        self.urls = []

    def fetch(self, url):
        self.urls.append(url)
        return deepcopy(self.run if '/actions/runs/' in url else self.item)

    def build(self):
        return publication._attest(self.records, self.raw, 123, self.now, self.fetch)

    def test_exact_bytes_before_both_saved_starts(self):
        report = self.build()
        self.assertEqual(report['feature_observations_verified'], 1)
        self.assertTrue(report['NO_BET'])
        self.assertFalse(report['forecasting_enabled'])
        self.assertTrue(self.urls[-1].endswith('?ref=' + 'a' * 40))
        self.assertTrue(report['saved_report_requires_fresh_api_replay'])

    def test_run_identity_fail_closed(self):
        for key, value in [('id', True), ('id', 456), ('repository', {'full_name': 'other/repo'}),
                ('head_repository', {'full_name': 'fork/repo'}), ('head_sha', '../main'),
                ('path', 'other.yml'), ('event', 'workflow_dispatch')]:
            with self.subTest(key=key, value=value):
                old = deepcopy(self.run)
                self.run[key] = value
                with self.assertRaises(ValueError): self.build()
                self.run = old

    def test_server_time_boundaries(self):
        for timestamp in ['2026-10-19T13:32:59Z', '2026-10-20T19:00:00Z',
                          '2026-10-21T00:00:00Z']:
            with self.subTest(timestamp=timestamp):
                self.run['created_at'] = timestamp
                with self.assertRaises(ValueError): self.build()

    def test_all_blobs_must_match_not_just_hash_or_filename(self):
        for key, value in [('type', 'symlink'), ('path', 'wrong.json'), ('sha', 'b' * 40),
                ('size', True), ('size', 0), ('encoding', 'utf-8'), ('content', '!!!'),
                ('content', base64.b64encode(b'other bytes').decode())]:
            with self.subTest(key=key, value=value):
                old = deepcopy(self.item)
                self.item[key] = value
                with self.assertRaises(ValueError): self.build()
                self.item = old

    def test_no_empty_or_partial_cohort(self):
        self.raw = {}
        with self.assertRaises(ValueError): self.build()
        self.records = {}
        with self.assertRaises(ValueError): self.build()

    def test_positive_integer_run_id(self):
        for run_id in [True, 0, -1, '123']:
            with self.assertRaises(ValueError):
                publication._attest(self.records, self.raw, run_id, self.now, self.fetch)

    def test_aware_clock_required_before_source_or_network(self):
        with self.assertRaises(ValueError):
            publication.audit(123, now=datetime(2026, 10, 19))

    def test_replayed_file_race_rejected(self):
        with patch.object(publication.features, '_reference', return_value={}), \
             patch.object(publication.features, '_existing', return_value=self.records), \
             patch.object(publication.Path, 'read_bytes', return_value=b'changed'):
            with self.assertRaisesRegex(ValueError, 'changed during'):
                publication.audit(123, now=self.now, fetch=self.fetch)

    def test_saved_report_always_requeries_server_and_preserves_cohort(self):
        saved = self.build()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'report.json'
            path.write_text(json.dumps(saved))
            with patch.object(publication, 'audit', return_value=deepcopy(saved)) as audit:
                publication.replay(path, now=self.now, fetch=self.fetch)
                self.assertEqual(audit.call_args.kwargs['cohort_ids'], ['0022600001'])
                changed = deepcopy(saved)
                changed['head_sha'] = 'b' * 40
                audit.return_value = changed
                with self.assertRaisesRegex(ValueError, 'fresh API replay'):
                    publication.replay(path, now=self.now, fetch=self.fetch)

    def test_saved_report_boolean_tampering_rejected(self):
        saved = self.build()
        actual = deepcopy(saved)
        saved['actual_wagers'] = False
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'report.json'
            path.write_text(json.dumps(saved))
            with patch.object(publication, 'audit', return_value=actual):
                with self.assertRaises(ValueError): publication.replay(path)

    def test_original_cohort_does_not_enroll_later_records(self):
        extra = deepcopy(self.records)
        extra['0022600002'] = dict(extra['0022600001'], nba_game_id='0022600002')
        raw = publication.source.canonical({'record': self.records['0022600001'],
            'record_sha256': publication.features.digest(self.records['0022600001'])})
        with patch.object(publication.features, '_reference', return_value={}), \
             patch.object(publication.features, '_existing', return_value=extra), \
             patch.object(publication.Path, 'read_bytes', return_value=raw), \
             patch.object(publication, '_attest', return_value={}) as attest:
            publication.audit(123, now=self.now, cohort_ids=['0022600001'])
            self.assertEqual(set(attest.call_args.args[0]), {'0022600001'})
            for ids in [[], ['0022600001', '0022600001'], ['0022600999']]:
                with self.assertRaises(ValueError):
                    publication.audit(123, now=self.now, cohort_ids=ids)


if __name__ == '__main__': unittest.main()
