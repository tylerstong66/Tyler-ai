from pathlib import Path
import hashlib
import json
import tempfile
import unittest

import sports_mlb_legacy_source_inventory as inventory
from test_sports_mlb_cross_cohort_audit import seed, edit_hitter


class SourceInventoryTests(unittest.TestCase):
    def fixture(self, root, *, archived=False):
        _, path = seed(root, archived=archived)
        return path, {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()}

    def test_missing_candidates_preserve_originals_and_all_provenance_gaps(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); path, selection = self.fixture(root); before = path.read_bytes()
            report = inventory.build(selection, base=root)
            self.assertEqual(report['receipt_observations'], 4)
            self.assertEqual(report['current_archives_verified'], 0)
            self.assertTrue(all(r['inventory_status'] == 'NO_CURRENT_ARCHIVE_CONTENT_MATCH' for r in report['rows']))
            self.assertFalse(report['original_source_validation_complete'])
            self.assertFalse(report['publication_chronology_checked'])
            self.assertEqual(path.read_bytes(), before)

    def test_two_different_wire_representations_are_candidates_without_timing_claims(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); path, _ = self.fixture(root)
            data = {'roster': [], 'note': 'present now'}
            digest = inventory.archives.canonical_digest(data)
            edit_hitter(path, lambda d: d['source_receipts']['active_roster'].update(response_sha256=digest))
            selection = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()}
            directory = root/inventory.cohorts.HITTER_ROOT/'source_archives'
            for raw in (json.dumps(data).encode(), json.dumps(data, indent=2).encode()):
                inventory.archives.retain(directory, raw, digest)
            report = inventory.build(selection, base=root)
            row = next(r for r in report['rows'] if r['kind'] == 'active_roster')
            self.assertEqual(len(row['current_archive_candidates']), 2)
            self.assertEqual(row['inventory_status'], 'CURRENT_CANONICAL_JSON_MATCH_ONLY')
            self.assertFalse(row['declared_original_archive_replayed'])
            for name in ('candidate_original_wire_bytes_attested', 'candidate_source_url_attested',
                         'candidate_availability_at_freeze_attested'):
                self.assertIs(row[name], False)

    def test_declared_archives_still_require_existing_strict_receipt_replay(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); _, selection = self.fixture(root, archived=True)
            report = inventory.build(selection, base=root)
            self.assertTrue(all(r['declared_original_archive_replayed'] for r in report['rows']))
            self.assertFalse(report['original_source_validation_complete'])
            archive = next((root/inventory.cohorts.HITTER_ROOT/'source_archives').iterdir())
            archive.write_bytes(b'broken')
            with self.assertRaises((ValueError, OSError, EOFError)):
                inventory.build(selection, base=root)

    def test_selected_original_cannot_be_resealed_or_replaced(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); path, selection = self.fixture(root)
            edit_hitter(path, lambda d: d.update(frozen_at_utc='2026-10-16T18:10:40Z'))
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                inventory.build(selection, base=root)

    def test_unrelated_corrupt_or_symlink_archives_fail_even_without_matches(self):
        for symlink in (False, True):
            with self.subTest(symlink=symlink), tempfile.TemporaryDirectory() as td:
                root = Path(td); path, selection = self.fixture(root)
                directory = root/inventory.cohorts.HITTER_ROOT/'source_archives'
                directory.mkdir(); candidate = directory/('a'*64+'.json.gz')
                if symlink: candidate.symlink_to(path)
                else: candidate.write_bytes(b'invalid')
                with self.assertRaises((ValueError, OSError, EOFError)):
                    inventory.build(selection, base=root)

    def test_selection_rejects_mutable_scope_traversal_and_bad_digest(self):
        for selection in ({}, {'../record.json': 'a'*64},
                          {inventory.cohorts.HITTER_ROOT.as_posix()+'/predictions/1_2.json': 'bad'}):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                inventory.build(selection)

    def test_symlinked_archive_directory_cannot_expand_inventory_scope(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as external:
            root = Path(td); _, selection = self.fixture(root)
            (root/inventory.cohorts.HITTER_ROOT/'source_archives').symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'Symlink'):
                inventory.build(selection, base=root)


if __name__ == '__main__':
    unittest.main()
