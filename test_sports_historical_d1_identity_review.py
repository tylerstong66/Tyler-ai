"""Identity review packets are repeated metadata evidence, never active aliases."""
import copy
from datetime import datetime,timezone,timedelta
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

import sports_historical_d1_identity_review as review
from test_sports_ncaa_espn_identity import official_game,espn_game


def fixtures():
    ncaa={};espn={}
    for year,split in ((2024,'train'),(2025,'validation')):
        ncaa[split]=[];espn[split]=[]
        for i,opponent in enumerate(('Duke','Kansas')):
            common={'game_id':f'{year}{i}','start_utc':f'{year}-11-05T0{i}:00:00Z',
                    'receipts':[{'receipt_sha256':'a'*64,'response_sha256':'b'*64}]}
            ncaa[split].append({**common,'home':{'school':'Penn St.','seoname':'penn-state'},
                                'away':{'school':opponent,'seoname':opponent.lower()}})
            espn[split].append({**common,'game_id':f'401{year}{i}',
                                'home':{'school':'Penn State','team_id':'213'},
                                'away':{'school':opponent,'team_id':str(100+i)}})
    return ncaa,espn


class D1IdentityReviewTests(unittest.TestCase):
    def test_repeated_exact_anchors_in_both_splits_produce_review_only_evidence(self):
        n,e=fixtures();before=copy.deepcopy((n,e));out=review.propose(n,e)
        self.assertEqual(out['candidate_institutions'],1)
        candidate=out['candidate_proposals'][0]
        for split in ('train','validation'):self.assertEqual(len(candidate['evidence'][split]),2)
        self.assertTrue(candidate['review_required'])
        for key in ('alias_activation_allowed','institutional_identity_certified','division_one_membership_verified'):
            self.assertIs(candidate[key],False)
        self.assertEqual(out['runtime_aliases_added'],0)
        self.assertFalse(out['score_or_outcome_used_for_identity'])
        self.assertEqual((n,e),before)

    def test_no_fuzzy_opponent_or_nearest_time_matching(self):
        for kind in ('opponent','time','orientation'):
            with self.subTest(kind=kind):
                n,e=fixtures()
                if kind=='opponent':e['train'][0]['away']['school']='Dukee'
                elif kind=='time':e['train'][0]['start_utc']='2024-11-05T00:01:00Z'
                else:e['train'][0]['home'],e['train'][0]['away']=e['train'][0]['away'],e['train'][0]['home']
                self.assertEqual(review.propose(n,e)['candidate_institutions'],0)

    def test_repeated_receipt_cannot_supply_a_second_game_or_opponent(self):
        for kind in ('same_game','same_opponent','missing_split'):
            with self.subTest(kind=kind):
                n,e=fixtures()
                if kind=='same_game':n['train']=[n['train'][0]];e['train']=[e['train'][0]]*2
                elif kind=='same_opponent':
                    n['train'][1]['away']['school']='Duke';e['train'][1]['away']['school']='Duke'
                else:n['validation']=[];e['validation']=[]
                self.assertEqual(review.propose(n,e)['candidate_institutions'],0)

    def test_duplicate_candidate_or_reused_game_id_never_becomes_proposal(self):
        for kind in ('ambiguous','reused'):
            with self.subTest(kind=kind):
                n,e=fixtures()
                if kind=='ambiguous':n['train'].append(copy.deepcopy(n['train'][0]))
                else:
                    duplicate=copy.deepcopy(e['train'][0]);duplicate['game_id']='401999999'
                    e['train'].append(duplicate)
                self.assertEqual(review.propose(n,e)['candidate_institutions'],0)

    def test_changed_slug_team_id_or_multiple_name_targets_stays_excluded(self):
        for key,value in (('seoname','other-school'),('team_id','999'),('school','Pennsylvania State')):
            with self.subTest(key=key):
                n,e=fixtures()
                for game in (n if key=='seoname' else e)['validation']:game['home'][key]=value
                self.assertEqual(review.propose(n,e)['candidate_institutions'],0)

    def test_scores_outcomes_and_input_order_cannot_change_proposals(self):
        n,e=fixtures();expected=review.propose(n,e)
        for groups in (n,e):
            for split,rows in groups.items():
                for row in rows:row['home_score']=999;row['winner']='away'
                groups[split]=list(reversed(rows))
        self.assertEqual(review.propose(n,e),expected)

    def test_both_source_content_seals_precede_any_read(self):
        with patch.object(review.original_seal,'verify') as old, \
             patch.object(review.independent_seal,'verify',side_effect=ValueError('changed')) as new, \
             patch.object(review,'_read') as read:
            with self.assertRaises(ValueError):review.build()
            old.assert_called_once();new.assert_called_once();read.assert_not_called()

    def test_source_game_ids_cannot_cross_season_splits(self):
        for provider in ('ncaa','espn'):
            n,e=fixtures();games=n if provider=='ncaa' else e
            games['validation'][0]['game_id']=games['train'][0]['game_id']
            with self.assertRaisesRegex(ValueError,'crosses season splits'):review.propose(n,e)

    def test_raw_source_reader_links_original_hashes_without_changing_files(self):
        now=datetime(2026,10,19,tzinfo=timezone.utc)
        plan={league:{split:[bounds[0]] for split,bounds in parts.items()}
              for league,parts in review.history.SEASONS.items()}
        days=plan['NCAAM_D1']
        with tempfile.TemporaryDirectory() as td, \
             patch.object(review.owned,'DATES',days), \
             patch.object(review.history,'dates_by_league',return_value=plan):
            root=Path(td)
            def ncaa_fetch(url):
                year=2024 if '2024' in url else 2025
                day=days['train' if year==2024 else 'validation'][0]
                at=datetime.fromisoformat(day).replace(hour=12,tzinfo=timezone.utc)
                games=[]
                for i,opponent in enumerate(('Duke','Kansas')):
                    g=official_game(when=int((at+timedelta(hours=i)).timestamp()),home='Penn St.',away=opponent)
                    g['contestId']=str(year*10+i);g['startDate']=at.strftime('%m/%d/%Y')
                    for team in g['teams']:team['seoname']='penn-state' if team['isHome'] else opponent.lower()
                    games.append(g)
                return json.dumps({'data':{'contests':games}}).encode()
            for split in ('train','validation'):review.owned.capture(ncaa_fetch,base=root,split=split,now=now,per_run=1)
            def espn_fetch(url):
                events=[]
                if 'mens-college-basketball' in url:
                    year=2024 if '2024' in url else 2025
                    day=days['train' if year==2024 else 'validation'][0]
                    at=datetime.fromisoformat(day).replace(hour=12,tzinfo=timezone.utc)
                    for i,opponent in enumerate(('Duke','Kansas')):
                        event=espn_game(start=(at+timedelta(hours=i)).isoformat(),home='Penn State',away=opponent)
                        event['id']=str(401000000+year*10+i);events.append(event)
                return json.dumps({'count':len(events),'events':events}).encode()
            for _ in range(2):review.history.capture(espn_fetch,base=root,now=now,per_league=1,date_plan=plan)
            before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
            ns={};es={}
            for split in ('train','validation'):ns[split],es[split]=review._read(root,split,now,set())
            out=review.propose(ns,es)
            self.assertEqual(out['candidate_institutions'],1)
            self.assertEqual(before,{p:p.read_bytes() for p in root.rglob('*') if p.is_file()})
            blob=next((root/review.owned.ROOT/'train').glob('*.json.gz'));blob.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):review._read(root,'train',now,set())


if __name__=='__main__':unittest.main()
