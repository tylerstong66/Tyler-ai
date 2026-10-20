"""Crosswalk receipt must replay archived sources, never trust report flags."""
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
import sports_ncaa_espn_identity as identity
import sports_ncaa_espn_crosswalk_receipts as receipts
from test_sports_ncaa_espn_identity import AT,CollegeIdentityTests

class CrosswalkReceiptTests(unittest.TestCase):
    def test_crosswalk_and_linked_source_redirects_reject(self):
        for kind in ('crosswalk_folder', 'crosswalk_manifest', 'ancestor', 'ncaa_folder', 'espn_folder'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                root = Path(td); stamp = self.seed(root)
                folder = root/identity.ROOT/'captures'/stamp
                target = {'crosswalk_folder': folder, 'crosswalk_manifest': folder/'manifest.json',
                          'ancestor': root/'benchmarks',
                          'ncaa_folder': next((root/identity.ncaa.ROOT/'captures').iterdir()),
                          'espn_folder': next((root/identity.espn.ROOT/'captures').iterdir())}[kind]
                outside = root/'relocated'; target.rename(outside)
                target.symlink_to(outside, target_is_directory=outside.is_dir())
                with self.assertRaisesRegex(ValueError, 'Symlink'): receipts.verify(root, stamp)

    def seed(self,root):
        CollegeIdentityTests().seed(root)
        identity.run(base=root,now=AT+timedelta(minutes=10))
        return "20261017T141000000000Z"

    def test_original_source_crosswalk_replays_without_grading(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);stamp=self.seed(root)
            out=receipts.verify(root,stamp)
            self.assertEqual(out["strict_identity_matches"],1)
            self.assertTrue(out["identity_crosswalk_replayed"])
            self.assertFalse(out["independent_official_final_verified"])
            self.assertFalse(out["eligible_for_historical_evaluation"])

    def test_forged_crosswalk_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);stamp=self.seed(root)
            path=root/identity.ROOT/"captures"/stamp/"manifest.json"
            obj=json.loads(path.read_text())
            obj["report"]["unique_source_game_identity_matches"]=100
            path.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError,"differs"):
                receipts.verify(root,stamp)

    def test_linked_manifest_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);stamp=self.seed(root)
            linked=next((root/identity.ncaa.ROOT/"captures").glob("*/manifest.json"))
            linked.write_bytes(linked.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"digest mismatch"):
                receipts.verify(root,stamp)

    def test_path_traversal_rejected(self):
        with self.assertRaisesRegex(ValueError,"identifier"):
            receipts.verify(".","../../foo")

if __name__=="__main__":
    unittest.main()
