"""Historical aliases require both original seasons and preserve exact mode."""
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
import copy
import hashlib
import json
import shutil
import tempfile
import unittest

import sports_historical_school_identities as schools
import sports_historical_fbs_crosscheck as check
import sports_ncaa_historical_owned as owned
import sports_expansion_historical_capture as history

NOW=datetime(2026,10,19,tzinfo=timezone.utc)


class HistoricalSchoolIdentityTests(unittest.TestCase):
    def fixture(self,root):
        saved=json.loads(schools.MANIFEST.read_bytes());saved['entries']=saved['entries'][:1]
        for part,evidence in saved['entries'][0]['evidence'].items():
            n=evidence['ncaa'];e=evidence['espn']
            for folder,stem in ((owned.ROOT/part,f"week-{n['week']:02d}"),
                                (history.ROOT/'sources/NCAAF_FBS'/part,e['source_date'])):
                for suffix in ('.json.gz','.receipt.json'):
                    src=folder/(stem+suffix);dest=root/src;dest.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(src,dest)
        return saved

    def write(self,root,saved):
        p=root/schools.MANIFEST;p.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(saved).encode();p.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def test_real_both_season_identity_sources_replay(self):
        out=schools.load(now=NOW)
        self.assertEqual(out['reviewed_school_spellings'],83)
        self.assertEqual(out['aliases']['pennst'],'Penn State')
        self.assertEqual(out['aliases']['miamifl'],'Miami')
        self.assertNotIn('penn',out['aliases']) # no counterpart in both declared source seasons
        self.assertNotIn('saintfrancis',out['aliases'])

    def test_corrupt_manifest_and_original_source_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);saved=self.fixture(root);digest=self.write(root,saved)
            with self.assertRaisesRegex(ValueError,'digest mismatch'):schools.load(root,now=NOW)
            with patch.object(schools,'MANIFEST_SHA256',digest):
                self.assertEqual(schools.load(root,now=NOW)['reviewed_school_spellings'],1)
                part='train';n=saved['entries'][0]['evidence'][part]['ncaa']
                (root/owned.ROOT/part/f"week-{n['week']:02d}.json.gz").write_bytes(b'bad')
                with self.assertRaises(ValueError):schools.load(root,now=NOW)

    def test_review_cannot_bind_a_different_school_or_unstable_team(self):
        for mutation in ('ncaa_school','espn_team','missing_split','duplicate','guard'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as td:
                root=Path(td);saved=self.fixture(root);entry=saved['entries'][0]
                if mutation=='ncaa_school':entry['ncaa_school']='Unrelated University'
                if mutation=='espn_team':entry['evidence']['validation']['espn']['team_id']='99999999'
                if mutation=='missing_split':entry['evidence'].pop('validation')
                if mutation=='duplicate':saved['entries'].append(copy.deepcopy(entry))
                if mutation=='guard':saved['training_allowed']=True
                digest=self.write(root,saved)
                with patch.object(schools,'MANIFEST_SHA256',digest),self.assertRaises(ValueError):
                    schools.load(root,now=NOW)

    def test_opt_in_improves_coverage_and_exact_v1_remains_unchanged(self):
        for part,strict_count,reviewed_count in (('train',468,951),('validation',450,925)):
            with self.subTest(split=part):
                strict=check.build(split=part,now=NOW)
                reviewed=check.build(split=part,now=NOW,verified_school_aliases=True)
                self.assertEqual(strict['two_source_final_agreements'],strict_count)
                self.assertEqual(reviewed['two_source_final_agreements'],reviewed_count)
                strict_ids={r['espn_game_id'] for r in strict['corroborated_research_only']}
                reviewed_ids={r['espn_game_id'] for r in reviewed['corroborated_research_only']}
                self.assertTrue(strict_ids<=reviewed_ids)
                self.assertEqual(len(reviewed_ids),len(reviewed['corroborated_research_only']))
                self.assertEqual(reviewed['school_identity_manifest_sha256'],schools.MANIFEST_SHA256)
                self.assertTrue(reviewed['NO_BET']);self.assertEqual(reviewed['actual_wagers'],0)
                self.assertFalse(reviewed['training_allowed']);self.assertFalse(reviewed['forecasting_enabled'])
        with self.assertRaises(ValueError):check.build(league='NCAAM_D1',verified_school_aliases=True,now=NOW)


if __name__=='__main__':unittest.main()
