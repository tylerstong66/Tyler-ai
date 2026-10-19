from copy import deepcopy
from datetime import timedelta
from pathlib import Path
import base64
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

import sports_fbs_feature_publication as publication
import test_sports_fbs_pregame_features as fixtures

NOW = fixtures.NOW+timedelta(hours=1)


class FbsPublicationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); self.base = Path(temp.name)
        fixture = fixtures.FbsFeatureTests(); fixture.seed(self.base); self.addCleanup(fixture.doCleanups)
        publication.features.inspect(self.base, now=fixtures.NOW, collect=True)
        self.run = {'id': 100, 'head_sha': 'a'*40,
            'repository': {'full_name': publication.server.REPOSITORY},
            'head_repository': {'full_name': publication.server.REPOSITORY},
            'path': publication.WORKFLOW, 'event': 'pull_request', 'created_at': '2026-10-17T14:30:00Z'}
        self.calls = []; self.mutation = None

    def fetch(self, url):
        self.calls.append(url)
        if '/actions/runs/' in url: return deepcopy(self.run)
        path = url.split('/contents/')[1].split('?ref=')[0]; raw = (self.base/path).read_bytes()
        value = {'type': 'file', 'path': path, 'size': len(raw), 'encoding': 'base64',
            'sha': hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
            'content': base64.b64encode(raw).decode()}
        if self.mutation: self.mutation(value)
        return value

    def build(self, **kwargs):
        return publication.audit(100, base=self.base, now=NOW, fetch=self.fetch, **kwargs)

    def test_original_source_replay_and_exact_frozen_bytes_are_separate_from_forecasts(self):
        report = self.build()
        self.assertEqual(report['feature_observations_verified'], 1)
        self.assertEqual(report['protocol_sha256'], publication.features.PROTOCOL_SHA256)
        self.assertTrue(report['not_a_prediction']); self.assertTrue(report['NO_BET'])
        self.assertFalse(report['forecasting_enabled']); self.assertEqual(report['actual_wagers'], 0)

    def test_server_time_before_freeze_at_start_or_future_fails(self):
        for timestamp in ('2026-10-17T14:19:59Z', '2026-10-17T17:00:00Z', '2026-10-18T13:00:00Z'):
            self.run['created_at'] = timestamp
            with self.assertRaises(ValueError): self.build()

    def test_wrong_run_workflow_cannot_attest_same_bytes(self):
        self.run['path'] = '.github/workflows/other.yml'
        with self.assertRaises(ValueError): self.build()

    def test_decoded_file_bytes_and_original_blob_metadata_must_both_match(self):
        for key, value in [('sha', 'b'*40), ('path', 'wrong.json'), ('size', True),
                ('content', base64.b64encode(b'other').decode())]:
            with self.subTest(key=key):
                self.mutation = lambda item: item.update({key: value})
                with self.assertRaises(ValueError): self.build()

    def test_recipe_uses_explicit_existing_unique_cohort_only(self):
        for ids in ([], ['401100001', '401100001'], ['401999999']):
            with self.assertRaises(ValueError): self.build(cohort_ids=ids)

    def test_saved_recipe_requires_fresh_query_and_rejects_typed_guard_edit(self):
        report = self.build(); path = self.base/'proof.json'; path.write_text(json.dumps(report))
        self.calls = []
        publication.replay(path, base=self.base, now=NOW, fetch=self.fetch)
        self.assertEqual(len(self.calls), 2)
        report['actual_wagers'] = False; path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'fresh API replay'):
            publication.replay(path, base=self.base, now=NOW, fetch=self.fetch)

    def test_original_record_tamper_cannot_be_attested_after_digest_rehash(self):
        path = next((self.base/publication.features.ROOT).glob('*.json'))
        saved = json.loads(path.read_bytes()); saved['record']['forecasting_enabled'] = True
        saved['record_sha256'] = publication.features.digest(saved['record'])
        path.write_bytes(publication.features.source.canonical(saved))
        with self.assertRaisesRegex(ValueError, 'original source replay'): self.build()


if __name__ == '__main__': unittest.main()
