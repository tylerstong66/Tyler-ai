"""Pinned original NBA seasons never become forecasts or silently change."""
from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile
import unittest

import sports_nba_historical_owned as owned
from test_sports_nba_official_schedule_audit import official_games

NOW=datetime(2026,10,18,tzinfo=timezone.utc)


def original(split='train'):
    year=owned.YEARS[split]
    obj=json.loads(official_games((f'{year}-10-22T19:00:00Z',)))
    schedule=obj['leagueSchedule'];schedule.update(leagueId='00',seasonYear=owned.season(split))
    for i,game in enumerate(schedule['gameDates'][0]['games']):
        game['gameId']=f'002{year%100:02d}{i:05d}'
        game['gameDateTimeUTC']=f'{year}-10-22T19:00:00Z' if i==0 else f'{year}-11-02T19:00:00Z'
        game.update(gameStatus=3,postponedStatus='N')
        game['homeTeam']['score']=106;game['awayTeam']['score']=104
    return json.dumps(obj).encode()


class NbaHistoricalOwnedTests(unittest.TestCase):
    def test_pinned_seasons_replay_unchanged_and_auto_advance(self):
        with tempfile.TemporaryDirectory() as td:
            def fetch(url): return original('train' if '2024-25' in url else 'validation')
            owned.capture(fetch,base=td,now=NOW)
            path=Path(td)/owned.ROOT/'train'/'2024-25.receipt.json';before=path.read_bytes()
            saved=owned.verify(td,'train',now=NOW)
            self.assertEqual(len(saved['parsed_nba_games']),126)
            self.assertFalse(saved['model_training_enabled']);self.assertTrue(saved['NO_BET'])
            self.assertEqual(owned.capture(fetch,base=td,now=NOW)['split'],'validation')
            self.assertEqual(owned.capture(lambda _:self.fail('No refetch'),base=td,now=NOW)['new_source_seasons'],0)
            self.assertEqual(before,path.read_bytes())

    def test_corrupt_retained_source_prevents_new_network_request(self):
        with tempfile.TemporaryDirectory() as td:
            owned.capture(lambda _:original(),base=td,now=NOW)
            (Path(td)/owned.ROOT/'train'/'2024-25.json.gz').write_bytes(b'bad')
            with self.assertRaises(ValueError):
                owned.capture(lambda _:self.fail('No request after corruption'),base=td,now=NOW)

    def test_wrong_season_or_future_source_never_writes(self):
        for kind in ('season','league','game_id','game_date'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                obj=json.loads(original());s=obj['leagueSchedule'];g=s['gameDates'][0]['games'][0]
                if kind=='season':s['seasonYear']='2025-26'
                if kind=='league':s['leagueId']='10'
                if kind=='game_id':g['gameId']='0022500000'
                if kind=='game_date':g['gameDateTimeUTC']='2025-10-22T19:00:00Z'
                with self.assertRaises(ValueError):owned.capture(lambda _:json.dumps(obj).encode(),base=td,now=NOW)
                self.assertFalse((Path(td)/owned.ROOT).exists())
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'not closed'):
                owned.capture(lambda _:self.fail('No open season request'),base=td,
                              now=datetime(2025,6,22,tzinfo=timezone.utc))

    def test_receipt_guard_hash_and_future_observation_fail_closed(self):
        for field,value in (('NO_BET',False),('actual_wagers',False),
                            ('recorded_at_utc','2027-01-01T00:00:00Z'),
                            ('original_response_sha256','0'*64)):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as td:
                owned.capture(lambda _:original(),base=td,now=NOW)
                p=Path(td)/owned.ROOT/'train'/'2024-25.receipt.json';obj=json.loads(p.read_bytes())
                obj[field]=value;p.write_text(json.dumps(obj))
                with self.assertRaises(ValueError):owned.verify(td,'train',now=NOW)


if __name__=='__main__':unittest.main()
