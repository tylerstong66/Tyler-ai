"""Pregame feature observations are replayable, immutable and never predictions."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import copy
import json
import tempfile
import unittest
from unittest.mock import patch

import sports_nba_pregame_features as features
import test_sports_nba_schedule_slots as slot_fixtures

NOW=datetime(2026,10,17,13,tzinfo=timezone.utc)


def reference():
    rows=[]
    for i in range(10):
        at=datetime(2026,4,1+i,19,tzinfo=timezone.utc).isoformat()
        rows.append({'league':'NBA','nba_game_id':f'00225{i:05d}','espn_game_id':str(401000000+i),
                     'home_tricode':'NYK','away_tricode':'BOS','home_score':100+i,'away_score':90+i,
                     'nba_scheduled_start_utc':at,'espn_scheduled_start_utc':at,
                     'corroboration_available_at_utc':(NOW-timedelta(days=2)).isoformat()})
    return {'corroborated_research_only':rows}


class NbaPregameFeatureTests(unittest.TestCase):
    def seed(self,root):
        _,stamp,_=slot_fixtures.NbaFutureSlotTests().capture(root)
        self.enterContext(patch.object(features,'_reference',return_value=reference()))
        return stamp

    def test_real_schedule_receipt_creates_one_feature_record_and_excludes_tbd(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root)
            out=features.collect(root,now=NOW)
            self.assertEqual(out['new_feature_observations'],1)
            path=next((root/features.ROOT).glob('*.json'))
            record=features.verify(path,base=root,now=NOW)
            self.assertEqual(record['nba_game_id'],'0022600000')
            self.assertNotEqual(record['nba_game_id'],'0022699999')
            self.assertEqual(record['reference_features']['home']['prior_games'],10)
            self.assertEqual(record['reference_features']['home']['mean_margin'],10)
            self.assertTrue(record['not_a_prediction'])
            for key in ('model_training_enabled','historical_evaluation_enabled','forecasting_enabled','promotion_allowed',
                        'independent_publication_time_attested','institutional_membership_certified'):
                self.assertIs(record[key],False)
            self.assertIs(record['NO_BET'],True);self.assertEqual(record['actual_wagers'],0)

    def test_repeated_collection_and_later_audit_preserve_exact_original_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root);features.collect(root,now=NOW)
            path=next((root/features.ROOT).glob('*.json'));before=path.read_bytes()
            status=features.collect(root,now=NOW+timedelta(hours=1))
            self.assertEqual(status['verified_existing'],1);self.assertEqual(status['new_feature_observations'],0)
            features.verify(path,base=root,now=NOW+timedelta(days=7))
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(features.audit(root,now=NOW+timedelta(days=7))['verified_feature_observations'],1)

    def test_coordinated_feature_and_digest_edit_cannot_replace_source_replay(self):
        for key in ('mean','guard','prediction','bool_wagers','integer_prediction_flag'):
            with self.subTest(key=key),tempfile.TemporaryDirectory() as td:
                root=Path(td);self.seed(root);features.collect(root,now=NOW)
                path=next((root/features.ROOT).glob('*.json'));saved=json.loads(path.read_bytes())
                if key=='mean':saved['record']['reference_features']['home']['mean_points_for']+=1
                elif key=='guard':saved['record']['promotion_allowed']=True
                elif key=='prediction':saved['record']['not_a_prediction']=False
                elif key=='bool_wagers':saved['record']['actual_wagers']=False
                else:saved['record']['not_a_prediction']=1
                saved['record_sha256']=features.digest(saved['record']);path.write_bytes(features.source.canonical(saved))
                with self.assertRaisesRegex(ValueError,'original-source replay'):features.verify(path,base=root,now=NOW)

    def test_insufficient_or_post_freeze_reference_data_stays_unenrolled(self):
        for kind in ('missing','late','wrong_season','duplicate'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                root=Path(td);self.seed(root);r=reference()
                if kind=='missing':r['corroborated_research_only'].pop()
                elif kind=='late':r['corroborated_research_only'][0]['corroboration_available_at_utc']=(NOW+timedelta(hours=1)).isoformat()
                elif kind=='wrong_season':r['corroborated_research_only'][0]['nba_game_id']='0022400000'
                else:r['corroborated_research_only'][-1]=copy.deepcopy(r['corroborated_research_only'][0])
                features._reference.return_value=r
                if kind in ('wrong_season','duplicate'):
                    with self.assertRaises(ValueError):features.collect(root,now=NOW)
                else:
                    out=features.collect(root,now=NOW);self.assertEqual(out['new_feature_observations'],0)
                    self.assertEqual(out['not_enrolled'][0]['reason'],'INSUFFICIENT_CORROBORATED_REFERENCE_HISTORY')
                self.assertFalse((root/features.ROOT).exists())

    def test_started_or_stale_source_is_never_backfilled(self):
        for when,reason in ((NOW+timedelta(hours=13),'SCHEDULE_SOURCE_TOO_OLD_AT_FREEZE'),
                            (datetime(2026,10,20,19,tzinfo=timezone.utc),'SOURCE_SAVED_START_ALREADY_REACHED')):
            with self.subTest(when=when),tempfile.TemporaryDirectory() as td:
                root=Path(td);self.seed(root);out=features.collect(root,now=when)
                self.assertEqual(out['new_feature_observations'],0)
                self.assertEqual(out['not_enrolled'][0]['reason'],reason)

    def test_future_source_or_freeze_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);stamp=self.seed(root)
            with self.assertRaisesRegex(ValueError,'observed after feature freeze'):
                features.collect(root,now=NOW-timedelta(seconds=1))
            features.collect(root,now=NOW)
            path=next((root/features.ROOT).glob('*.json'))
            with self.assertRaisesRegex(ValueError,'future-dated'):features.verify(path,base=root,now=NOW-timedelta(seconds=1))

    def test_invalid_existing_record_prevents_all_new_writes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.seed(root);features.collect(root,now=NOW)
            good=next((root/features.ROOT).glob('*.json'));before=good.read_bytes()
            bad=root/features.ROOT/'0022699998.json';bad.write_bytes(b'{}')
            with self.assertRaises((ValueError,KeyError)):features.collect(root,now=NOW)
            self.assertEqual(good.read_bytes(),before)
            self.assertEqual(len(list((root/features.ROOT).glob('*.json'))),2)

    def test_source_corruption_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);stamp=self.seed(root);features.collect(root,now=NOW)
            blob=root/features.nba.ROOT/'captures'/stamp/'nba_schedule.json.gz';blob.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):features.collect(root,now=NOW)

    def test_missing_protocol_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'frozen experiment'):features._reference(Path(td),NOW)

    def test_nonbijective_source_crosswalk_never_creates_duplicate_game_files(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);stamp=self.seed(root);snapshot=features._snapshot(root,stamp)
            snapshot['manifest']['report']['matched'].append(copy.deepcopy(snapshot['manifest']['report']['matched'][0]))
            with patch.object(features,'_snapshot',return_value=snapshot):
                out=features.collect(root,now=NOW)
            self.assertEqual(out['new_feature_observations'],0)
            self.assertTrue(all(r['reason']=='NON_BIJECTIVE_SOURCE_GAME_IDENTITY' for r in out['not_enrolled']))
            self.assertFalse((root/features.ROOT).exists())


if __name__=='__main__':unittest.main()
