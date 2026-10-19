"""Reviewed D1 spellings require a pinned whitelist and replayed source proof."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sports_historical_d1_school_identities as schools
import sports_historical_d1_identity_review as review
import sports_historical_fbs_crosscheck as crosscheck
import sports_historical_college_disputes as disputes
import test_sports_historical_d1_identity_review as review_fixtures
import test_sports_historical_d1_crosscheck as crosscheck_fixtures


class ReviewedD1SchoolTests(unittest.TestCase):
    def seed(self,root,*,mutate=None):
        packet=review.propose(*review_fixtures.fixtures());case=packet['candidate_proposals'][0]
        actual=json.loads(Path(schools.MANIFEST).read_bytes())
        actual.update(entries=[{'ncaa_school':'Penn St.','espn_school':'Penn State',
                    'ncaa_seoname':'penn-state','espn_team_id':'213',
                    'candidate_evidence_sha256':schools.digest(case)}],
                    source_review_report_sha256=schools.digest(packet))
        if mutate:mutate(actual)
        path=root/schools.MANIFEST;path.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(actual).encode();path.write_bytes(raw)
        self.enterContext(patch.object(schools,'MANIFEST_SHA256',hashlib.sha256(raw).hexdigest()))
        self.enterContext(patch.object(schools.review,'build',return_value=packet))
        return path,packet

    def test_pinned_source_spelling_replays_for_both_splits(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td))
            for split in ('train','validation'):
                result=schools.load(td,split=split)
                self.assertEqual(result['aliases'],{'pennst':'Penn State'})
                self.assertEqual(result['reviewed_school_spellings'],1)

    def test_manifest_mutation_is_rejected_before_source_replay(self):
        with tempfile.TemporaryDirectory() as td:
            path,_=self.seed(Path(td));path.write_bytes(path.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'manifest digest'):schools.load(td)
            schools.review.build.assert_not_called()

    def test_changed_original_review_packet_cannot_preserve_alias(self):
        with tempfile.TemporaryDirectory() as td:
            _,packet=self.seed(Path(td))
            packet['candidate_proposals'][0]['espn_team_id']='999'
            with self.assertRaisesRegex(ValueError,'frozen source packet'):schools.load(td)

    def test_unreviewed_or_modified_candidate_evidence_is_rejected(self):
        for kind in ('school','evidence'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                def mutate(saved):
                    saved['entries'][0]['espn_school' if kind=='school' else 'candidate_evidence_sha256']='unknown'
                self.seed(Path(td),mutate=mutate)
                with self.assertRaisesRegex(ValueError,'repeated original-source evidence'):schools.load(td)

    def test_duplicate_alias_or_enabled_training_is_rejected_even_in_new_pin(self):
        for kind in ('duplicate','training'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                def mutate(saved):
                    if kind=='duplicate':saved['entries'].append(copy.deepcopy(saved['entries'][0]))
                    else:saved['training_allowed']=True
                self.seed(Path(td),mutate=mutate)
                with self.assertRaises(ValueError):schools.load(td)

    def test_missing_source_proof_and_wrong_scope_fail(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td));schools.review.build.side_effect=ValueError('source changed')
            with self.assertRaises(ValueError):schools.load(td)
        for kwargs in ({'league':'NBA'},{'split':'other'}):
            with self.assertRaises(ValueError):schools.load(**kwargs)

    def test_opt_in_d1_policy_preserves_default_replay_and_research_guards(self):
        with tempfile.TemporaryDirectory() as td:
            crosscheck_fixtures.HistoricalD1CrosscheckTests().seed(Path(td),school='Penn St.',espn_school='Penn State')
            before=crosscheck.build(td,league='NCAAM_D1',now=crosscheck_fixtures.NOW)
            policy={'aliases':{'pennst':'Penn State'},'manifest_sha256':'a'*64,
                    'policy':'TEST_REVIEWED_SOURCE_NAMES','reviewed_school_spellings':1}
            with patch.object(schools,'load',return_value=policy):
                result=crosscheck.build(td,league='NCAAM_D1',now=crosscheck_fixtures.NOW,
                                        verified_school_aliases=True)
            self.assertEqual(before['two_source_final_agreements'],0)
            self.assertEqual(result['two_source_final_agreements'],1)
            self.assertEqual(result['schema'],'tyler-historical-d1-reviewed-identity-crosscheck-v3')
            self.assertEqual(before,crosscheck.build(td,league='NCAAM_D1',now=crosscheck_fixtures.NOW))
            for key in ('training_allowed','historical_evaluation_enabled','forecasting_enabled',
                        'promotion_allowed','division_one_membership_verified','institutional_identity_certified'):
                self.assertIs(result[key],False)
            self.assertTrue(result['NO_BET']);self.assertEqual(result['actual_wagers'],0)

    def test_newly_recognized_disputed_game_keeps_both_original_claims(self):
        with tempfile.TemporaryDirectory() as td:
            crosscheck_fixtures.HistoricalD1CrosscheckTests().seed(
                Path(td),school='Penn St.',espn_school='Penn State',conflict=True)
            before=disputes.build(td,split='train',now=crosscheck_fixtures.NOW)
            self.assertEqual(before['disputed_games'],0)
            policy={'aliases':{'pennst':'Penn State'},'manifest_sha256':'a'*64,
                    'policy':'TEST_REVIEWED_SOURCE_NAMES','reviewed_school_spellings':1}
            with patch.object(schools,'load',return_value=policy):
                result=disputes.build(td,split='train',now=crosscheck_fixtures.NOW,
                                      verified_school_aliases=True)
            self.assertEqual(result['disputed_games'],1)
            self.assertEqual(result['schema'],'tyler-historical-college-reviewed-score-dispute-casebook-v2')
            case=result['cases'][0]
            self.assertTrue(case['ncaa_observations']);self.assertTrue(case['espn_observations'])
            self.assertFalse(case['eligible_for_result_agreement'])
            self.assertEqual(result['school_identity_manifest_sha256'],'a'*64)


if __name__=='__main__':unittest.main()
