"""D1 original source archives enforce season, day, chronology and immutability."""
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json
import tempfile
import unittest

import sports_ncaa_d1_historical_owned as owned
from test_sports_ncaa_espn_identity import official_game

NOW = datetime(2026,10,18,tzinfo=timezone.utc)


def fetch(url):
    variables=json.loads(parse_qs(urlparse(url).query)['variables'][0])
    at=datetime.strptime(variables['contestDate'],'%Y/%m/%d').replace(hour=19,tzinfo=timezone.utc)
    game=official_game(when=int(at.timestamp()),home='Duke',away='Kansas',final=True)
    game['contestId']=at.strftime('%Y%m%d')
    game['startDate']=at.strftime('%m/%d/%Y')
    return json.dumps({'data':{'contests':[game]}}).encode()


class D1HistoricalOwnedTests(unittest.TestCase):
    def test_actual_day_scope_receipts_replay_and_never_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            first=owned.capture(fetch,base=root,now=NOW,per_run=1)
            self.assertEqual((first['split'],first['new_source_days']),('train',1))
            saved=owned.verify(root,'train','2024-11-04',now=NOW)
            self.assertEqual(saved['parsed_ncaa_games'][0]['home_name'],'Duke')
            p=root/owned.ROOT/'train'/'2024-11-04.receipt.json';before=p.read_bytes()
            next_run=owned.capture(fetch,base=root,now=NOW,per_run=1)
            self.assertEqual(next_run['retained_source_days'],2)
            self.assertEqual(p.read_bytes(),before)
            self.assertFalse(saved['forecasting_enabled'])
            self.assertFalse(saved['official_result_grading_enabled'])

    def test_training_index_completes_before_automatic_validation_acquisition(self):
        with tempfile.TemporaryDirectory() as td:
            for _ in range(8):
                last=owned.capture(fetch,base=td,now=NOW)
            self.assertEqual(last['split'],'train')
            self.assertEqual(last['retained_source_days'],len(owned.DATES['train']))
            validation=owned.capture(fetch,base=td,now=NOW,per_run=1)
            self.assertEqual((validation['split'],validation['new_source_days']),('validation',1))
            self.assertFalse(validation['model_training_enabled'])

    def test_invalid_second_response_does_not_write_partial_day_batch(self):
        with tempfile.TemporaryDirectory() as td:
            calls=0
            def source(url):
                nonlocal calls
                calls+=1
                return fetch(url) if calls==1 else b'{"errors":["unavailable"]}'
            with self.assertRaises(ValueError):
                owned.capture(source,base=td,now=NOW,per_run=2)
            self.assertFalse((Path(td)/owned.ROOT).exists())

    def test_unicode_historical_tipoff_epoch_rejected_before_write(self):
        def invalid(url):
            original = json.loads(fetch(url))
            game = original['data']['contests'][0]
            game['startTimeEpoch'] = str(game['startTimeEpoch']).translate(
                str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩'))
            return json.dumps(original).encode()
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, 'kickoff identity'):
                owned.capture(invalid, base=td, now=NOW, per_run=1)
            self.assertFalse((Path(td)/owned.ROOT).exists())

    def test_modified_retained_bytes_block_new_fetch(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);owned.capture(fetch,base=root,now=NOW,per_run=1)
            (root/owned.ROOT/'train'/'2024-11-04.json.gz').write_bytes(b'bad')
            with self.assertRaises(ValueError):
                owned.capture(lambda _: self.fail('No network after corruption'),base=root,now=NOW)

    def test_future_dates_and_invalid_scope_fail_before_fetch(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'not closed'):
                owned.capture(lambda _: self.fail('No future-day request'),base=td,
                              now=datetime(2024,11,3,tzinfo=timezone.utc))
        for kwargs in ({'per_run':21},{'per_run':False},{'split':'../wrong'}):
            with self.assertRaises(ValueError):
                owned.capture(fetch,**kwargs)


if __name__=='__main__':
    unittest.main()
