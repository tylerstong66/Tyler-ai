"""Future MLB receipts retain original bytes without weakening forecast guards."""
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
import gzip
import hashlib
import json
import subprocess
import tempfile
import unittest

import sports_mlb_source_archives as archive
from sports_mlb_sources import OfficialMlbReader

RAW = '{"person":{"name":"José"},"games":[]}'.encode()
NOW = datetime(2026, 10, 18, 12, tzinfo=timezone.utc)


class MlbSourceArchiveTests(unittest.TestCase):
    def test_duplicate_json_keys_rejected_before_receipt_or_archive_creation(self):
        cases = (b'{"gamePk":1,"gamePk":2}',
                 b'{"batting":{"atBats":0,"atBats":4}}')
        for raw in cases:
            for retained in (False, True):
                with self.subTest(raw=raw, retained=retained), tempfile.TemporaryDirectory() as td:
                    def get(url, **kwargs):
                        return SimpleNamespace(status_code=200, content=raw, url=url,
                                               json=lambda: json.loads(raw))
                    reader = OfficialMlbReader(get=get, clock=lambda: NOW,
                                               archive_dir=td if retained else None)
                    with self.assertRaises(ValueError): reader.load('schedule')
                    self.assertEqual(reader.audit, [])
                    self.assertEqual(list(Path(td).iterdir()), [])
            with self.subTest(raw=raw, boundary='retain'), tempfile.TemporaryDirectory() as td:
                normalized = archive.canonical_digest(json.loads(raw))
                with self.assertRaises(ValueError): archive.retain(td, raw, normalized)
                self.assertEqual(list(Path(td).iterdir()), [])

    def test_rehashed_duplicate_source_cannot_pass_independent_archive_replay(self):
        for raw in (b'{"gamePk":1,"gamePk":2}',
                    b'{"batting":{"hits":0,"hits":1}}'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as td:
                sha = hashlib.sha256(raw).hexdigest(); filename = sha+'.json.gz'
                path = Path(td)/filename; path.write_bytes(gzip.compress(raw, mtime=0))
                receipt = {'original_response_archive_schema': 'mlb-original-response-archive-v1',
                    'original_response_sha256': sha, 'source_archive_file': filename,
                    'source_url': 'https://statsapi.mlb.com/api/v1/schedule',
                    'response_sha256': archive.canonical_digest(json.loads(raw))}
                before = path.read_bytes()
                with self.assertRaises(ValueError): archive.verify(td, receipt)
                self.assertEqual(path.read_bytes(), before)

    def test_symlinked_archive_root_or_ancestor_rejects_reads_and_writes(self):
        for nested in (False, True):
            with self.subTest(nested=nested), tempfile.TemporaryDirectory() as td:
                base = Path(td); outside = base/'outside'; outside.mkdir()
                evidence = archive.retain(outside, RAW, archive.canonical_digest(json.loads(RAW)))
                evidence.update(source_url='https://statsapi.mlb.com/api/v1/schedule',
                                response_sha256=archive.canonical_digest(json.loads(RAW)))
                link = base/'link'; link.symlink_to(outside, target_is_directory=True)
                root = link
                if nested:
                    child = outside/'child'; child.mkdir()
                    for p in outside.glob('*.gz'):
                        (child/p.name).write_bytes(p.read_bytes())
                    root = link/'child'
                before = {p.relative_to(outside): p.read_bytes() for p in outside.rglob('*') if p.is_file()}
                for operation in (lambda: archive.audit_directory(root),
                                  lambda: archive.verify(root, evidence),
                                  lambda: archive.retain(root, b'{"new":true}', archive.canonical_digest({'new': True}))):
                    with self.assertRaisesRegex(ValueError, 'Symlink'): operation()
                self.assertEqual(before, {p.relative_to(outside): p.read_bytes() for p in outside.rglob('*') if p.is_file()})

    def test_dangling_archive_directory_symlink_is_not_empty(self):
        with tempfile.TemporaryDirectory() as td:
            link = Path(td)/'archive'; link.symlink_to(Path(td)/'absent', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'Symlink'): archive.audit_directory(link)

    def test_reader_retains_original_utf8_response_and_replays_existing_digest(self):
        with tempfile.TemporaryDirectory() as td:
            def get(url, **kwargs):
                return SimpleNamespace(status_code=200, content=RAW, url=url,
                                       json=lambda: json.loads(RAW))
            reader = OfficialMlbReader(get=get, clock=lambda: NOW, archive_dir=td)
            data, receipt = reader.load('schedule', {'sportId': 1})
            self.assertEqual(archive.verify(td, receipt), data)
            self.assertEqual(archive.audit_directory(td), 1)
            original = (Path(td)/receipt['source_archive_file']).read_bytes()
            reader.load('schedule', {'sportId': 1})
            self.assertEqual(archive.audit_directory(td), 1)
            self.assertEqual((Path(td)/receipt['source_archive_file']).read_bytes(), original)

    def test_legacy_hash_is_unavailable_and_changed_original_bytes_fail(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, 'Legacy digest-only'):
                archive.verify(td, {'response_sha256': 'old'})
            evidence = archive.retain(td, RAW, archive.canonical_digest(json.loads(RAW)))
            evidence.update(source_url='https://statsapi.mlb.com/api/v1/schedule',
                            response_sha256=archive.canonical_digest(json.loads(RAW)))
            path = Path(td)/evidence['source_archive_file']
            path.write_bytes(gzip.compress(b'{"changed":true}',mtime=0))
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                archive.verify(td, evidence)

    def test_original_json_must_match_reader_normalization_before_any_write(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                archive.retain(td, RAW, '0'*64)
            self.assertEqual(list(Path(td).iterdir()), [])
            with self.assertRaises(ValueError):
                archive.retain(td, b'x'*(archive.MAX_BYTES+1), '0'*64)

    def test_staged_source_guard_checks_index_bytes_and_rejects_forecast_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(['git','init','-q'],cwd=root,check=True)
            folder = root/archive.ARCHIVE_DIR
            info = archive.retain(folder, RAW, archive.canonical_digest(json.loads(RAW)))
            path = archive.ARCHIVE_DIR+info['source_archive_file']
            subprocess.run(['git','add',path],cwd=root,check=True)
            self.assertEqual(archive.inspect_staged_additions(root), 1)
            # Keep a valid working tree but install an invalid staged blob.
            sha = subprocess.check_output(['git','hash-object','-w','--stdin'],input=b'bad',cwd=root).decode().strip()
            subprocess.run(['git','update-index','--cacheinfo','100644,'+sha+','+path],cwd=root,check=True)
            with self.assertRaises(ValueError):
                archive.inspect_staged_additions(root)
            subprocess.run(['git','rm','--cached','-f',path],cwd=root,check=True,stdout=subprocess.DEVNULL)
            bad = root/'forecast.json'; bad.write_text('{}')
            subprocess.run(['git','add','forecast.json'],cwd=root,check=True)
            with self.assertRaisesRegex(ValueError, 'Only new MLB original'):
                archive.inspect_staged_additions(root)

    def test_archive_traversal_or_unexpected_directory_entries_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td,'unexpected.txt').write_text('bad')
            with self.assertRaises(ValueError):
                archive.audit_directory(td)
            with self.assertRaises(ValueError):
                archive.verify(td, {'original_response_archive_schema':'mlb-original-response-archive-v1',
                                    'source_archive_file':'../outside', 'original_response_sha256':'0'*64})


if __name__ == '__main__':
    unittest.main()
