"""Synthetic server responses never attest actual native feature publication."""
import base64
import copy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
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

    def test_retained_actual_first_cohort_checks_bytes_without_fresh_server_claim(self):
        base = Path(publication.__file__).parent
        path = base/publication.features.ROOT.parent/'publication_v2/first_cohort.json'
        raw = path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         '5d1ef22f87e72af8d08daa4b2478d0547e54faa510a0d799865b97239887b030')
        report = json.loads(raw)
        self.assertEqual(report['run_id'], 39597562795)
        self.assertEqual(report['head_sha'], 'dd05e2e1a1f0a6b9d6cede5474e908e46cd6fa42')
        self.assertEqual(report['feature_observations_verified'], 2)
        self.assertEqual(report['feature_protocol_sha256'], publication.features.PROTOCOL_SHA256)
        self.assertTrue(report['saved_report_requires_fresh_api_replay'])
        self.assertTrue(report['not_a_prediction']); self.assertFalse(report['forecasting_enabled'])
        observed = datetime.fromisoformat(report['github_server_created_at_utc'].replace('Z', '+00:00'))
        for evidence in report['evidence']:
            path = base/publication.features.ROOT/(evidence['nba_game_id']+'.json')
            original = path.read_bytes(); row = json.loads(original)['record']
            self.assertEqual(evidence['path'], path.relative_to(base).as_posix())
            self.assertEqual(evidence['file_sha256'], hashlib.sha256(original).hexdigest())
            self.assertEqual(evidence['git_blob_sha1'], hashlib.sha1(
                b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest())
            self.assertLessEqual(datetime.fromisoformat(row['frozen_at_utc']), observed)
            for key in ('nba_saved_start_utc', 'espn_saved_start_utc'):
                self.assertLess(observed, datetime.fromisoformat(row[key]))


if __name__ == '__main__': unittest.main()
