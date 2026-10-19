"""Only original future NBA Cup TBD slots enter the explicit quarantine."""
from datetime import datetime,timezone
from pathlib import Path
import copy
import gzip
import json
import tempfile
import unittest

import sports_nba_schedule_slots as slots
import sports_nba_official_schedule_audit as nba
import sports_nba_schedule_receipts as receipts
import sports_nba_final_receipts as finals
import test_sports_nba_official_schedule_audit as fixtures

NOW=datetime(2026,10,17,13,tzinfo=timezone.utc)


def original():
    obj=json.loads(fixtures.official_games())
    schedule=obj['leagueSchedule'];schedule.update(leagueId='00',seasonYear='2026-27')
    games=schedule['gameDates'][0]['games']
    for i,game in enumerate(games):game['gameId']=f'00226{i:05d}'
    team={'teamId':0,'teamName':None,'teamCity':None,'teamTricode':None,'teamSlug':None,'score':0}
    games.append({'gameId':'0022699999','gameStatus':1,'gameDateTimeUTC':'2026-12-04T05:00:00Z',
                  'homeTeam':copy.deepcopy(team),'awayTeam':copy.deepcopy(team),
                  'gameLabel':'Emirates NBA Cup','gameSubLabel':'Quarterfinal'})
    return obj


class NbaFutureSlotTests(unittest.TestCase):
    def test_legacy_parser_stays_strict_and_original_slot_never_becomes_identity(self):
        raw=json.dumps(original()).encode();before=raw
        with self.assertRaises(ValueError):nba.official_games(raw)
        known,quarantined=slots.parse(raw,observed_at=NOW.isoformat())
        self.assertEqual(len(known),126);self.assertEqual(len(quarantined),1)
        self.assertFalse(quarantined[0]['eligible_for_identity_match'])
        self.assertFalse(quarantined[0]['eligible_for_result_agreement'])
        self.assertNotIn(quarantined[0]['nba_game_id'],{x['nba_game_id'] for x in known})
        self.assertEqual(raw,before)

    def test_partial_known_teams_unknown_competitions_or_nonfuture_slots_fail(self):
        for kind in ('known_away','ordinary_game','wrong_round','past','bool_status','final','nonzero_score'):
            with self.subTest(kind=kind):
                obj=original();slot=obj['leagueSchedule']['gameDates'][0]['games'][-1]
                if kind=='known_away':slot['awayTeam']={'teamId':1610612738,'teamTricode':'BOS'}
                elif kind=='ordinary_game':slot['gameLabel']='Regular Season'
                elif kind=='wrong_round':slot['gameSubLabel']='Unknown'
                elif kind=='past':slot['gameDateTimeUTC']='2026-10-16T19:00:00Z'
                elif kind=='bool_status':slot['gameStatus']=True
                elif kind=='final':slot['gameStatus']=3
                else:slot['homeTeam']['score']=1
                with self.assertRaises(ValueError):slots.parse(json.dumps(obj).encode(),observed_at=NOW.isoformat())

    def test_duplicate_ids_invalid_siblings_and_wrong_seasons_fail_whole_response(self):
        for kind in ('duplicate','sibling','season','league','future_final'):
            with self.subTest(kind=kind):
                obj=original();schedule=obj['leagueSchedule'];games=schedule['gameDates'][0]['games']
                if kind=='duplicate':games[-1]['gameId']=games[0]['gameId']
                elif kind=='sibling':games[0]['homeTeam']['teamTricode']='BOS'
                elif kind=='season':schedule['seasonYear']='2025-26'
                elif kind=='league':schedule['leagueId']='10'
                else:
                    games[0]['gameStatus']=3;games[0]['homeTeam']['score']=106;games[0]['awayTeam']['score']=104
                with self.assertRaises(ValueError):slots.parse(json.dumps(obj).encode(),observed_at=NOW.isoformat())

    def capture(self,root):
        fixtures.NbaOfficialCorroborationTests().espn_root(root)
        raw=json.dumps(original()).encode()
        saved=nba.run(lambda _:raw,base=root,now=NOW,quarantine_future_cup_slots=True)
        return saved,NOW.strftime('%Y%m%dT%H%M%S%fZ'),raw

    def test_original_v2_receipt_and_final_reader_replay_without_grading_slots(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);saved,stamp,raw=self.capture(root)
            self.assertEqual(saved['report']['strict_schedule_correlated'],1)
            self.assertEqual(saved['nba_known_game_count'],126)
            blob=root/nba.ROOT/'captures'/stamp/'nba_schedule.json.gz'
            self.assertEqual(gzip.decompress(blob.read_bytes()),raw)
            self.assertEqual(receipts.verify(root,stamp)['quarantined_future_cup_slots'],1)
            out=finals.build(root,stamp)
            self.assertEqual(out['two_source_final_agreements'],0)
            self.assertEqual(out['nba_quarantined_future_slot_ids'],['0022699999'])
            self.assertFalse(out['forecasting_enabled']);self.assertTrue(out['NO_BET'])

    def test_quarantine_tampering_cannot_promote_an_unknown_opponent(self):
        for kind in ('remove','promote','count','crosswalk'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
                root=Path(td);saved,stamp,_=self.capture(root)
                if kind=='remove':saved['quarantined_future_cup_slots']=[]
                elif kind=='promote':saved['quarantined_future_cup_slots'][0]['eligible_for_identity_match']=True
                elif kind=='count':saved['nba_known_game_count']+=1
                else:saved['report']['strict_schedule_correlated']+=1
                path=root/nba.ROOT/'captures'/stamp/'manifest.json';path.write_text(json.dumps(saved))
                with self.assertRaises(ValueError):receipts.verify(root,stamp)

    def test_v2_research_flags_source_timestamp_and_original_digest_are_required(self):
        for key,value in (('actual_wagers',False),('promotion_allowed',True),
                          ('model_training_enabled',True),('source_scope_complete',True),
                          ('nba_official_source_url','https://example.com'),
                          ('created_at_utc','2026-10-17T14:00:00Z'),('nba_raw_sha256','a'*64)):
            with self.subTest(key=key),tempfile.TemporaryDirectory() as td:
                root=Path(td);saved,stamp,_=self.capture(root);saved[key]=value
                (root/nba.ROOT/'captures'/stamp/'manifest.json').write_text(json.dumps(saved))
                with self.assertRaises(ValueError):receipts.verify(root,stamp)

    def test_failed_parse_leaves_no_partial_source_archive(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);fixtures.NbaOfficialCorroborationTests().espn_root(root)
            obj=original();obj['leagueSchedule']['gameDates'][0]['games'][-1]['gameStatus']=3
            with self.assertRaises(ValueError):
                nba.run(lambda _:json.dumps(obj).encode(),base=root,now=NOW,quarantine_future_cup_slots=True)
            self.assertFalse((root/nba.ROOT).exists())


if __name__=='__main__':unittest.main()
