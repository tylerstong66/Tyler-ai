from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import base64
import hashlib
import json
import tempfile
import unittest

import sports_mlb_archived_source_publication as publication
from test_sports_mlb_cross_cohort_audit import seed, edit_hitter

NOW = datetime(2026, 10, 16, 20, tzinfo=timezone.utc)
SHA = 'a'*40


class ArchivedSourcePublicationTests(unittest.TestCase):
    def fixture(self, base, *, archived=True):
        _, path = seed(base, archived=archived)
        selection = {path.relative_to(base).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()}
        run = {'id': 100, 'head_sha': SHA, 'repository': {'full_name': publication.server.REPOSITORY},
            'head_repository': {'full_name': publication.server.REPOSITORY}, 'path': publication.WORKFLOW,
            'event': 'push', 'created_at': '2026-10-16T19:00:00Z'}
        responses = {publication.server.API+'/actions/runs/100': run}
        files = [path] + list((base/publication.cohorts.HITTER_ROOT/'source_archives').glob('*'))
        for file in files:
            raw = file.read_bytes(); name = file.relative_to(base).as_posix()
            responses[publication.server.API+'/contents/'+name+'?ref='+SHA] = {
                'type': 'file', 'path': name, 'sha': hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
                'size': len(raw), 'encoding': 'base64', 'content': base64.b64encode(raw).decode()}
        return selection, responses

    def audit(self, base, selection, responses):
        return publication.audit(selection, 100, base=base, now=NOW, fetch=lambda u: deepcopy(responses[u]))

    def test_every_record_and_shared_archive_is_bound_without_origin_or_quality_claims(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); selection, responses = self.fixture(base)
            before = {p: p.read_bytes() for p in base.rglob('*') if p.is_file()}
            report = self.audit(base, selection, responses)
            self.assertEqual(report['hitter_records_verified'], 1)
            self.assertEqual(report['distinct_source_archives_verified'], 2)
            self.assertEqual(len(report['records'][0]['source_receipts']), 4)
            self.assertTrue(report['all_declared_original_response_bytes_replayed'])
            for flag in ('source_origin_certified', 'receipt_clock_independently_attested',
                         'model_input_semantics_fully_recomputed', 'prediction_scores_computed'):
                self.assertIs(report[flag], False)
            self.assertEqual(before, {p: p.read_bytes() for p in base.rglob('*') if p.is_file()})

    def test_digest_only_legacy_receipts_cannot_receive_archive_attestation(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); selection, responses = self.fixture(base, archived=False)
            with self.assertRaisesRegex(ValueError, 'declare and replay'):
                self.audit(base, selection, responses)

    def test_wrong_remote_archive_bytes_metadata_or_missing_file_fail(self):
        for mutation in ('bytes', 'sha', 'size', 'type', 'missing'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                base = Path(td); selection, responses = self.fixture(base)
                url = next(k for k in responses if k.endswith('.json.gz?ref='+SHA))
                if mutation == 'bytes': responses[url]['content'] = base64.b64encode(b'not original').decode()
                elif mutation == 'sha': responses[url]['sha'] = 'b'*40
                elif mutation == 'size': responses[url]['size'] = True
                elif mutation == 'type': responses[url]['type'] = 'symlink'
                else: responses[url] = {'message': 'not found'}
                with self.assertRaises(ValueError): self.audit(base, selection, responses)

    def test_server_must_observe_after_freeze_and_before_original_saved_start(self):
        for value in ('2026-10-16T18:00:00Z', '2026-10-17T00:00:00Z'):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as td:
                base = Path(td); selection, responses = self.fixture(base)
                responses[publication.server.API+'/actions/runs/100']['created_at'] = value
                with self.assertRaisesRegex(ValueError, 'follow freeze and precede saved start'):
                    publication.audit(selection, 100, base=base,
                        now=datetime(2026, 10, 17, 1, tzinfo=timezone.utc),
                        fetch=lambda u: deepcopy(responses[u]))

    def test_changed_resealed_record_cannot_override_selected_original(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); selection, responses = self.fixture(base)
            path = base/next(iter(selection))
            edit_hitter(path, lambda r: r.update(frozen_at_utc='2026-10-16T18:10:40Z'))
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                self.audit(base, selection, responses)

    def test_replay_is_fixed_to_explicit_records_and_rejects_changed_saved_claims(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); selection, responses = self.fixture(base)
            report = self.audit(base, selection, responses)
            saved = base/'report.json'; saved.write_text(json.dumps(report))
            extra = base/publication.cohorts.HITTER_ROOT/'predictions/9_9.json'; extra.write_text('bad unrelated record')
            actual = publication.replay(saved, base=base, now=NOW, fetch=lambda u: deepcopy(responses[u]))
            self.assertEqual(actual, report)
            report['source_origin_certified'] = True; saved.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError, 'differs from fresh'):
                publication.replay(saved, base=base, now=NOW, fetch=lambda u: deepcopy(responses[u]))


if __name__ == '__main__':
    unittest.main()
