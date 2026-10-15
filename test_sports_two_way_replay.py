import gzip
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import sports_two_way_replay as replay
import sports_two_way_test as live
import sports_historical_benchmark as b


class ReplayTests(unittest.TestCase):
    config={'sport':'NHL','k':20,'home_offset':50,'result_delay_hours':12}
    model={'training_season':2025,'frozen_at':'2026-10-11T12:00:00Z','weights':[.1,.4]}

    def game(self, identifier='1', kickoff='2026-10-09T10:00:00Z', **extra):
        return {'game_id':identifier,'season':2026,'kickoff':kickoff,'home':'H','away':'A',
                'home_id':'h','away_id':'a','home_score':3,'away_score':2,'neutral':False,
                'regular':True,'completed':True,'state':'post',**extra}

    def score(self, games, history=None):
        return replay.replay(history or [],games,self.model,self.config,2026)

    def test_scores_match_live_pregame_recipe_and_delay(self):
        games=[self.game(),self.game('2','2026-10-09T21:00:00Z'),self.game('3','2026-10-10T10:00:00Z')]
        _,rows=self.score(games)
        for row in rows:
            g=next(g for g in games if g['game_id']==row['game_id'])
            x,fixed,_=live.pregame(games,g,b.utc(row['simulated_cutoff']),self.config)
            self.assertEqual(row['features'],x)
            self.assertAlmostEqual(row['home_probability']['fixed_elo'],fixed)
        self.assertEqual(rows[0]['features'],rows[1]['features'])
        self.assertNotEqual(rows[1]['features'],rows[2]['features'])

    def test_current_result_cannot_change_its_features_or_probability(self):
        _,a=self.score([self.game()]);_,b_=self.score([self.game(home_score=0,away_score=20)])
        self.assertEqual(a[0]['features'],b_[0]['features'])
        self.assertEqual(a[0]['home_probability'],b_[0]['home_probability'])
        self.assertNotEqual(a[0]['scores'],b_[0]['scores'])

    def test_wrong_season_future_availability_and_unfinished_games_rejected(self):
        for edits in [{'season':2025},{'kickoff':'2026-10-11T00:00:00Z'},{'completed':False}]:
            with self.subTest(edits=edits),self.assertRaises(ValueError):self.score([self.game(**edits)])
        with self.assertRaises(ValueError):self.score([self.game()],history=[self.game('warmup')])

    def test_conflicting_duplicate_tied_or_invalid_finals_rejected(self):
        cases=[[self.game(),self.game()], [self.game(),self.game(home_score=99)],
               [self.game(home_score=2)], [self.game(home_score=True)]]
        for games in cases:
            with self.subTest(games=games),self.assertRaises(ValueError):self.score(games)

    def test_ambiguous_resumption_not_scored_and_sources_not_mutated(self):
        games=[self.game(historical_resumption_ambiguous=True),self.game('2','2026-10-10T10:00:00Z')]
        before=deepcopy(games);data,rows=self.score(games)
        self.assertEqual(games,before)
        self.assertEqual([r['game_id'] for r in rows],['2'])
        self.assertEqual(data['excluded'],[{'game_id':'1','reason':'ambiguous_resumption'}])
        self.assertTrue(data['NO_BET']);self.assertEqual(data['actual_wagers'],0)

    def test_corrupt_pinned_input_fails_closed_before_evaluation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/replay.ROOT;root.mkdir(parents=True)
            (base/'bad').write_text('changed')
            (root/'inputs.json').write_text(json.dumps({'files_sha256':{'bad':'wrong'}}))
            with self.assertRaisesRegex(ValueError,'hash mismatch'):replay.evaluate(base)

    def test_real_reports_reproduce_without_changing_any_live_artifacts(self):
        roots=[live.ROOT/'nhl',live.ROOT/'mlb']
        tracked=[p for root in roots for kind in ['predictions','results'] for p in (root/kind).glob('*.json')]
        before={str(p):b.sha256(p.read_bytes()) for p in tracked}
        reports,scores=replay.evaluate()
        self.assertEqual({str(p):b.sha256(p.read_bytes()) for p in tracked},before)
        self.assertEqual({d['sport']:d['scored'] for d in reports},{'NHL':83,'MLB':2451})
        for data in reports:
            saved=json.loads((replay.ROOT/(data['sport'].lower()+'_report.json')).read_text())
            self.assertEqual(data,saved)
            stored=json.loads(gzip.decompress((replay.ROOT/(data['sport'].lower()+'_scores.json.gz')).read_bytes()))
            self.assertEqual(scores[data['sport']],stored)
        self.assertIn('not a blind holdout',replay.render(reports))


if __name__=='__main__':unittest.main()
