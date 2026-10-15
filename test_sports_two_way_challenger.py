import gzip
import json
import math
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import sports_two_way_challenger as c
import sports_two_way_test as live
import sports_historical_benchmark as b


class ChallengerTests(unittest.TestCase):
    config={'sport':'NHL','k':20,'home_offset':50,'result_delay_hours':12}

    def game(self, identifier, season, kickoff, win=True, **extra):
        return {'game_id':identifier,'season':season,'kickoff':kickoff,'home_id':'h','away_id':'a',
                'home':'H','away':'A','home_score':3 if win else 1,'away_score':2,
                'neutral':False,'regular':True,'completed':True,**extra}

    def history(self):
        return [self.game(str(i),2024,f'2024-01-{i+1:02d}T12:00:00Z',i%3==0) for i in range(12)]+[
            self.game('v1',2025,'2025-01-01T12:00:00Z'),
            self.game('v2',2025,'2025-01-01T23:00:00Z'),
            self.game('v3',2025,'2025-01-02T12:00:00Z')]

    def protocol(self):
        return {'training_season':2024,'validation_season':2025,'l2_penalty':.01,'limitations':['development only']}

    def test_validation_outcomes_never_fit_weights_or_change_own_probability(self):
        games=self.history();a,ra=c.compare(games,self.config,self.protocol())
        games[-1]['home_score']=0
        z,rz=c.compare(games,self.config,self.protocol())
        self.assertEqual(a['models_fit_on_training_only'],z['models_fit_on_training_only'])
        self.assertEqual(ra[-1]['home_probability'],rz[-1]['home_probability'])
        self.assertNotEqual(ra[-1]['scores'],rz[-1]['scores'])

    def test_delayed_validation_results_and_venue_follow_live_recipe(self):
        games=self.history();games[-1]['neutral']=True
        _,rows=c.compare(games,self.config,self.protocol())
        self.assertEqual(rows[0]['features'],rows[1]['features'])
        self.assertNotEqual(rows[1]['features'],rows[2]['features'])
        for row in rows:
            target=next(g for g in games if g['game_id']==row['game_id'])
            x,p,_=live.pregame(games,target,b.utc(row['simulated_cutoff']),self.config)
            self.assertEqual(x,row['features'])
            self.assertAlmostEqual(p,row['home_probability']['fixed_elo'])

    def test_wrong_seasons_unfinished_overlapping_training_and_bad_finals_fail(self):
        for field,value in [('season',2026),('completed',False),('home_score',True),('away_score',3)]:
            games=self.history();games[0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):c.partition(games,self.config)
        games=self.history();games[0]['kickoff']='2025-01-01T06:00:00Z'
        with self.assertRaisesRegex(ValueError,'eligible before'):c.partition(games,self.config)
        games=self.history();games.append({**games[0],'home_score':99})
        with self.assertRaisesRegex(ValueError,'Conflicting'):c.partition(games,self.config)

    def test_ambiguous_resumptions_excluded_without_mutating_inputs(self):
        games=self.history();games.append({**games[0],'kickoff':'2024-01-02T12:00:00Z'})
        before=deepcopy(games)
        training,_,excluded=c.partition(games,self.config)
        self.assertEqual(games,before)
        self.assertNotIn('0',[r['data']['game_id'] for r in training])
        self.assertEqual(excluded,[{'game_id':'0','season':2024,'reason':'ambiguous_resumption'}])

    def test_calibration_optimizer_satisfies_gradient_and_improves_objective(self):
        training,_,_=c.partition(self.history(),self.config)
        fit=c.fit_calibration(training,.01);weights=fit['weights']
        self.assertTrue(fit['converged'])
        self.assertLess(c.calibration_objective(training,weights,.01),c.calibration_objective(training,[0,1],.01))
        for j in range(2):
            plus=weights[:];minus=weights[:];plus[j]+=1e-5;minus[j]-=1e-5
            gradient=(c.calibration_objective(training,plus,.01)-c.calibration_objective(training,minus,.01))/2e-5
            self.assertAlmostEqual(gradient,0,places=6)
        for penalty in [0,-1,float('nan')]:
            with self.assertRaises(ValueError):c.fit_calibration(training,penalty)
        training[0]['calibration_x']=[1,math.inf]
        with self.assertRaises(ValueError):c.fit_calibration(training,.01)

    def test_corrupt_input_and_attempt_to_add_2026_source_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/c.ROOT;root.mkdir(parents=True)
            protocol=json.loads((c.ROOT/'protocol.json').read_text())
            (root/'protocol.json').write_text(json.dumps(protocol))
            for path in protocol['files_sha256']:
                dest=base/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(Path(path).read_bytes())
            target=base/live.ROOT/'nhl/history.json';target.write_text('[]')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):c.evaluate(base)
            protocol['files_sha256']['benchmarks/two_way_prospective/nhl/observed_history.json']='bad'
            (root/'protocol.json').write_text(json.dumps(protocol))
            with self.assertRaisesRegex(ValueError,'Only pinned'):c.evaluate(base)

    def test_reports_reproduce_and_no_live_assets_changed(self):
        paths=[p for p in live.ROOT.rglob('*') if p.is_file()]
        before={str(p):b.sha256(p.read_bytes()) for p in paths}
        reports,scores=c.evaluate()
        self.assertEqual(before,{str(p):b.sha256(p.read_bytes()) for p in paths})
        for data in reports:
            name=data['sport'].lower()
            self.assertEqual(data,json.loads((c.ROOT/(name+'_report.json')).read_text()))
            self.assertEqual(scores[data['sport']],json.loads(gzip.decompress((c.ROOT/(name+'_scores.json.gz')).read_bytes())))
            self.assertEqual(data['selected_development_candidate'],min(c.CANDIDATES,key=lambda n:data['metrics'][n]['mean']['log_loss']))
            self.assertFalse(data['promotion_allowed']);self.assertTrue(data['NO_BET']);self.assertEqual(data['actual_wagers'],0)
            self.assertGreater(data['training']['games'],1200)
        self.assertEqual(c.render(reports),(c.ROOT/'README.md').read_text())


if __name__=='__main__':unittest.main()
