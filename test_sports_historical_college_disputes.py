"""Dispute diagnostics preserve both original claims and cannot grade results."""
from pathlib import Path
import hashlib
import tempfile
import unittest

import sports_historical_college_disputes as disputes
import sports_ncaa_d1_historical_owned as owned
import test_sports_historical_d1_crosscheck as fixtures
NOW=fixtures.NOW


class HistoricalCollegeDisputesTests(unittest.TestCase):
    def seed(self,root,**kwargs):
        fixtures.HistoricalD1CrosscheckTests().seed(root,**kwargs)

    def test_conflicting_final_retains_both_claims_and_receipt_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root,conflict=True)
            before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
            out=disputes.build(root,split='train',now=NOW)
            self.assertEqual(out['disputed_games'],1)
            row=out['cases'][0]
            self.assertEqual(row['reason'],'CONFLICTING_FINAL_SCORES_NO_GRADE')
            n=row['ncaa_observations'][0];e=row['espn_observations'][0]
            self.assertNotEqual(n['original_normalized_claim']['ncaa_home_score'],
                                e['original_normalized_claim']['home_score'])
            for observation in (n,e):
                path=root/observation['source_receipt']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),observation['receipt_sha256'])
                self.assertEqual(len(observation['response_sha256']),64)
            self.assertEqual(before,{p:p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.assertEqual(out,disputes.build(root,split='train',now=NOW))
            self.assertFalse(row['eligible_for_result_agreement'])
            for key in ('training_allowed','historical_evaluation_enabled','forecasting_enabled',
                        'official_result_grading_enabled','promotion_allowed','source_scope_complete'):
                self.assertIs(out[key],False)
            self.assertIs(out['NO_BET'],True);self.assertEqual(out['actual_wagers'],0)

    def test_agreement_and_unknown_identity_never_enter_dispute_casebook(self):
        for kwargs in ({},{'school':'Penn St.','espn_school':'Penn State'}):
            with self.subTest(kwargs=kwargs),tempfile.TemporaryDirectory() as td:
                self.seed(Path(td),**kwargs)
                out=disputes.build(td,split='train',now=NOW)
                self.assertEqual(out['cases'],[])
                self.assertEqual(out['disputed_games'],0)
                self.assertEqual(out['other_pending_games'],int(bool(kwargs)))

    def test_duplicate_observations_are_all_retained_once_per_game(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td),conflict=True,days=2)
            out=disputes.build(td,split='train',now=NOW)
            self.assertEqual(out['disputed_games'],1)
            self.assertEqual(len(out['cases'][0]['ncaa_observations']),2)

    def test_corrupt_source_and_invalid_scope_fail_before_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root,conflict=True)
            path=next((root/owned.ROOT/'train').glob('*.json.gz'))
            path.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):disputes.build(root,split='train',now=NOW)
        for kwargs in ({'league':'NBA'},{'split':'other'}):
            with self.assertRaises(ValueError):disputes.build(**kwargs)


if __name__=='__main__':unittest.main()
