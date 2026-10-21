"""Synthetic server responses never attest actual native feature publication."""
import base64
import copy
from datetime import timedelta
import hashlib
import json
import unittest

import sports_nba_native_feature_publication as publication
import test_sports_nba_native_pregame_features as fixtures


class NativePublicationTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.NativeFeatureTests(); fixture.setUp()
        self.addCleanup(fixture.doCleanups); fixture.collect()
        self.base = fixture.base; self.now = fixture.now+timedelta(minutes=1)
        self.run = {'id': 100, 'head_sha': 'a'*40,
            'repository': {'full_name': publication.shared.REPOSITORY},
            'head_repository': {'full_name': publication.shared.REPOSITORY},
            'path': publication.WORKFLOW, 'event': 'pull_request',
            'created_at': (fixture.now+timedelta(seconds=10)).isoformat()}
        self.calls = []; self.mutation = None

    def fetch(self, url):
        self.calls.append(url)
        if '/actions/runs/' in url: return copy.deepcopy(self.run)
        path = url.split('/contents/')[1].split('?ref=')[0]
        self.assertTrue(path.startswith(publication.features.ROOT.as_posix()+'/'))
        raw = (self.base/path).read_bytes()
        result = {'type': 'file', 'path': path, 'size': len(raw), 'encoding': 'base64',
            'sha': hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
            'content': base64.b64encode(raw).decode()}
        if self.mutation: self.mutation(result)
        return result

    def build(self, **kwargs):
        return publication.audit(100, base=self.base, now=self.now, fetch=self.fetch, **kwargs)

    def test_exact_native_root_bytes_and_protocol_are_isolated_from_v1_evidence(self):
        report = self.build()
        self.assertEqual(report['schema'], publication.SCHEMA)
        self.assertEqual(report['feature_observations_verified'], 3)
        self.assertEqual(report['feature_protocol_sha256'], publication.features.PROTOCOL_SHA256)
        self.assertEqual(report['workflow_path'], publication.WORKFLOW)
        self.assertTrue(report['saved_report_requires_fresh_api_replay'])
        self.assertTrue(report['cross_version_counts_must_not_be_pooled'])
        self.assertTrue(report['not_a_prediction']); self.assertFalse(report['forecasting_enabled'])
        self.assertFalse(report['promotion_allowed']); self.assertEqual(report['actual_wagers'], 0)
        self.assertEqual(len(self.calls), 4)

    def test_late_before_freeze_wrong_workflow_or_altered_original_bytes_fail(self):
        original = self.run['created_at']
        for at in (self.now-timedelta(minutes=2), self.now+timedelta(hours=20)):
            self.run['created_at'] = at.isoformat()
            with self.assertRaises(ValueError): self.build()
        self.run['created_at'] = original; self.run['path'] = publication.shared.WORKFLOW
        with self.assertRaises(ValueError): self.build()
        self.run['path'] = publication.WORKFLOW
        self.mutation = lambda row: row.update(content=base64.b64encode(b'changed').decode())
        with self.assertRaises(ValueError): self.build()

    def test_saved_recipe_requires_fresh_server_query_and_rejects_typed_guard_edit(self):
        report = self.build(); path = self.base/'native-publication.json'
        path.write_text(json.dumps(report)); self.calls.clear()
        publication.replay(path, base=self.base, now=self.now, fetch=self.fetch)
        self.assertEqual(len(self.calls), 4)
        report['actual_wagers'] = False; path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, 'fresh server replay'):
            publication.replay(path, base=self.base, now=self.now, fetch=self.fetch)

    def test_missing_duplicate_or_foreign_cohort_ids_are_not_attested(self):
        for ids in ([], ['0022600001']*2, ['0022699999']):
            with self.assertRaises(ValueError): self.build(cohort_ids=ids)


if __name__ == '__main__': unittest.main()
