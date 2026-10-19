"""Independent archive seal rejects coordinated edits and index replacement."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

import sports_historical_extension_seal as seal


class IndependentHistoricalSealTests(unittest.TestCase):
    def seed(self,root):
        paths=[Path('input/source.json.gz'),Path('input/source.receipt.json')]
        for p in paths:
            (root/p).parent.mkdir(parents=True,exist_ok=True)
            (root/p).write_bytes(b'original')
        self.enterContext(patch.object(seal,'expected_paths',return_value=paths))
        count,digest=seal.content_index(root)
        saved={'schema':'tyler-completed-independent-historical-sources-v1',
               'source_files':count,'source_file_index_sha256':digest,
               **{k:False for k in seal.GUARDS},'NO_BET':True,'actual_wagers':0}
        path=root/seal.MANIFEST;path.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(saved).encode();path.write_bytes(raw)
        self.enterContext(patch.object(seal,'MANIFEST_SHA256',hashlib.sha256(raw).hexdigest()))
        return paths

    def test_originals_verify_but_coordinated_source_and_receipt_edits_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);paths=self.seed(root)
            report=seal.verify(root)
            self.assertEqual(report['indexed_source_files_verified'],2)
            for guard in seal.GUARDS:self.assertIs(report[guard],False)
            self.assertFalse(report['source_origin_or_publication_time_attested'])
            for p in paths:(root/p).write_bytes(b'coordinated alteration')
            with self.assertRaisesRegex(ValueError,'index differs'):seal.verify(root)

    def test_recomputed_manifest_cannot_silently_replace_pinned_index(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);paths=self.seed(root)
            (root/paths[0]).write_bytes(b'altered')
            path=root/seal.MANIFEST;saved=json.loads(path.read_bytes())
            saved['source_file_index_sha256']=seal.content_index(root)[1]
            path.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError,'manifest digest changed'):seal.verify(root)

    def test_missing_and_symlinked_sources_fail(self):
        for kind in ('missing','symlink','directory'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                root=Path(td);paths=self.seed(root);p=root/paths[0];p.unlink()
                if kind=='symlink':p.symlink_to(root/paths[1])
                if kind=='directory':p.mkdir()
                with self.assertRaisesRegex(ValueError,'nonregular'):seal.verify(root)

    def test_separate_future_files_do_not_change_frozen_scope(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root);original=seal.verify(root)
            (root/'new-independent-scope').write_bytes(b'new data')
            self.assertEqual(seal.verify(root),original)


if __name__=='__main__':unittest.main()
