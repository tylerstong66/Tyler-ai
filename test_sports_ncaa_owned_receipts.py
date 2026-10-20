"""Independent NCAA archived source replay and tampering regression tests."""
import gzip
import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path
import sports_ncaa_official_source as ncaa
import sports_ncaa_owned_receipts as receipts
from test_sports_ncaa_official_source import contest,raw

class NcaaReceiptReplayTests(unittest.TestCase):
    def test_static_symlink_components_rejected(self):
        for kind in ('folder', 'ancestor', 'manifest', 'blob'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                root = Path(td); folder = self.seed(root)
                target = {'folder': folder, 'ancestor': root/'benchmarks',
                          'manifest': folder/'manifest.json',
                          'blob': next(folder.glob('*.json.gz'))}[kind]
                outside = root/'relocated'; target.rename(outside)
                target.symlink_to(outside, target_is_directory=outside.is_dir())
                with self.assertRaisesRegex(ValueError, 'Symlink'): receipts.verify(folder)

    def test_manifest_must_be_bounded_regular_file_before_decoding(self):
        for kind in ('directory', 'oversized'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                folder = self.seed(Path(td)); target = folder/'manifest.json'; target.unlink()
                if kind == 'directory': target.mkdir()
                else:
                    with target.open('wb') as stream: stream.truncate(8_500_001)
                with self.assertRaises(ValueError): receipts.verify(folder)

    def seed(self,root):
        ncaa.run(lambda _:raw(contest()),base=root,
                 now=datetime(2026,10,17,12,tzinfo=timezone.utc),days_ahead=0)
        return root/ncaa.ROOT/"captures"/"20261017T120000000000Z"

    def test_replayed_ncaa_source_never_grants_official_grading(self):
        with tempfile.TemporaryDirectory() as td:
            folder=self.seed(Path(td))
            out=receipts.verify(folder)
            self.assertTrue(out["ncaa_owned_source_sha256_verified"])
            self.assertEqual(out["reconciled_contests"],1)
            self.assertFalse(out["independent_official_final_verified"])
            self.assertFalse(out["eligible_for_historical_evaluation"])

    def test_tampered_ncaa_archive_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            folder=self.seed(Path(td))
            archive=folder/"NCAAF_FBS_week-08.json.gz"
            archive.write_bytes(gzip.compress(raw(contest("999")),mtime=0))
            with self.assertRaisesRegex(ValueError,"digest mismatch"):
                receipts.verify(folder)

    def test_forged_reconciliation_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            folder=self.seed(Path(td))
            target=folder/"manifest.json"
            obj=json.loads(target.read_text())
            obj["unambiguous_ncaa_contests"]=[]
            target.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"differs"):
                receipts.verify(folder)

    def test_oversized_archive_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            folder=self.seed(Path(td))
            archive=folder/"NCAAF_FBS_week-08.json.gz"
            archive.write_bytes(gzip.compress(b"x"*(ncaa.MAX_BYTES+1),mtime=0))
            with self.assertRaisesRegex(ValueError,"exceeds maximum"):
                receipts.verify(folder)

if __name__=="__main__":
    unittest.main()
