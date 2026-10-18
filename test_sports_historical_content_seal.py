"""Original input seals survive appends and detect coordinated input changes."""
from pathlib import Path
import json
import tempfile
import unittest
import sports_historical_content_seal as seal


class HistoricalContentSealTests(unittest.TestCase):
    def seed(self,root):
        paths=seal.expected_paths()
        self.assertEqual(len(paths),2292)
        # Opaque test bytes exercise content integrity only; this seal makes no
        # claim that they pass the separate source JSON/gzip semantic readers.
        for path in paths:
            out=root/path;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b'original')
        count,digest=seal.content_index(root)
        saved={'schema':'tyler-completed-historical-source-acquisition-v1',
               'source_files':count,'source_file_index_sha256':digest,
               'NO_BET':True,'actual_wagers':0,'training_allowed':False,
               'historical_evaluation_enabled':False,'forecasting_enabled':False,
               'promotion_allowed':False,'official_schedule_completeness_certified':False}
        (root/seal.MANIFEST).write_text(json.dumps(saved))
        return paths

    def test_original_bytes_verify_and_new_independent_scopes_can_append(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root)
            before=seal.verify(root)
            extra=root/'benchmarks/college_nba_history_v1/ncaa_owned/NCAAM_D1/train/2024-11-04.json.gz'
            extra.parent.mkdir(parents=True);extra.write_bytes(b'new independent scope')
            self.assertEqual(seal.verify(root),before)
            self.assertEqual(before['indexed_source_files_verified'],2292)
            self.assertFalse(before['source_semantics_verified_by_this_seal'])
            self.assertFalse(before['training_allowed'])

    def test_changing_source_and_receipt_together_still_breaks_frozen_index(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);paths=self.seed(root)
            for path in paths[:2]:
                (root/path).write_bytes(b'coordinated changed bytes')
            with self.assertRaisesRegex(ValueError,'differs from completion'):
                seal.verify(root)

    def test_missing_file_or_enabled_guard_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);paths=self.seed(root)
            (root/paths[0]).unlink()
            with self.assertRaisesRegex(ValueError,'Missing'):
                seal.verify(root)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root)
            p=root/seal.MANIFEST;saved=json.loads(p.read_bytes());saved['training_allowed']=True
            p.write_text(json.dumps(saved))
            with self.assertRaisesRegex(ValueError,'guards changed'):
                seal.verify(root)


if __name__=='__main__':
    unittest.main()
