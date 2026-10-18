"""A tied reported final remains raw evidence and cannot become a label."""
from datetime import datetime,timezone
from pathlib import Path
import copy
import gzip
import json
import tempfile
import unittest

import sports_ncaa_d1_historical_owned as owned
import sports_ncaa_official_source as source
from test_sports_ncaa_d1_historical_owned import fetch,NOW


def original():
    raw=fetch(source.graph_url('NCAAM_D1',year=2024,day='2024-11-04'))
    obj=json.loads(raw);tied=copy.deepcopy(obj['data']['contests'][0]);tied['contestId']='99999'
    tied['teams'][0]['score']=0;tied['teams'][1]['score']=0
    obj['data']['contests'].append(tied)
    return obj


class D1SourceQuarantineTests(unittest.TestCase):
    def test_tied_final_archived_verbatim_but_excluded_from_valid_results(self):
        raw=json.dumps(original()).encode()
        with self.assertRaises(source.TiedNcaaFinalError):source.official_scoreboard(raw,'NCAAM_D1')
        with tempfile.TemporaryDirectory() as td:
            owned.capture(lambda _:raw,base=td,now=NOW,per_run=1)
            saved=owned.verify(td,'train','2024-11-04',now=NOW)
            self.assertEqual(saved['schema'],'tyler-ncaa-owned-d1-history-day-v2')
            self.assertEqual(len(saved['parsed_ncaa_games']),1)
            self.assertEqual(saved['quarantined_ncaa_contests'][0]['ncaa_game_id'],'99999')
            self.assertFalse(saved['quarantined_ncaa_contests'][0]['eligible_for_result_agreement'])
            blob=Path(td)/owned.ROOT/'train'/'2024-11-04.json.gz'
            self.assertEqual(gzip.decompress(blob.read_bytes()),raw)
            self.assertFalse(saved['model_training_enabled']);self.assertEqual(saved['actual_wagers'],0)
            self.assertEqual(owned.capture(fetch,base=td,now=NOW,per_run=1)['retained_source_days'],2)

    def test_other_malformed_records_and_duplicate_ids_still_fail_entire_batch(self):
        for issue in ('duplicate','missing_score','bad_identity','bad_day'):
            with self.subTest(issue=issue),tempfile.TemporaryDirectory() as td:
                obj=original();games=obj['data']['contests']
                if issue=='duplicate':games.append(copy.deepcopy(games[-1]))
                if issue=='missing_score':
                    invalid=copy.deepcopy(games[0]);invalid['contestId']='777';invalid['teams'][0]['score']=None
                    games.append(invalid)
                if issue=='bad_identity':games[-1]['teams'][1]['isHome']=True
                if issue=='bad_day':games[-1]['startTimeEpoch']=int(datetime(2025,11,4,tzinfo=timezone.utc).timestamp())
                with self.assertRaises(ValueError):
                    owned.capture(lambda _:json.dumps(obj).encode(),base=td,now=NOW,per_run=1)
                self.assertFalse((Path(td)/owned.ROOT).exists())

    def test_quarantine_cannot_be_removed_changed_or_promoted_on_replay(self):
        for issue in ('removed','promoted','score','id','legacy'):
            with self.subTest(issue=issue),tempfile.TemporaryDirectory() as td:
                raw=json.dumps(original()).encode();owned.capture(lambda _:raw,base=td,now=NOW,per_run=1)
                p=Path(td)/owned.ROOT/'train'/'2024-11-04.receipt.json';saved=json.loads(p.read_bytes())
                q=saved['quarantined_ncaa_contests'][0]
                if issue=='removed':saved['quarantined_ncaa_contests']=[]
                if issue=='promoted':q['eligible_for_result_agreement']=True
                if issue=='score':q['original_home_score']=1
                if issue=='id':q['ncaa_game_id']='777'
                if issue=='legacy':saved['schema']='tyler-ncaa-owned-d1-history-day-v1'
                p.write_text(json.dumps(saved))
                with self.assertRaises(ValueError):owned.verify(td,'train','2024-11-04',now=NOW)

    def test_bad_final_chronology_is_not_hidden_by_quarantine(self):
        raw=json.dumps(original()).encode()
        before=datetime(2024,11,4,18,tzinfo=timezone.utc)
        with self.assertRaises(ValueError):owned._parse_with_quarantine(raw,'train','2024-11-04',before)


if __name__=='__main__':unittest.main()
