import json
import tempfile
import unittest
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch

import sports_historical_benchmark as b
import sports_prospective_test as n
import sports_two_way_test as p


class TwoWayTests(unittest.TestCase):
    clock=b.utc('2026-10-11T16:00:00Z')
    config={'sport':'NHL','k':20,'home_offset':50,'result_delay_hours':12}

    def game(self,**edits):
        return {**{'game_id':'1','season':2026,'kickoff':(self.clock+timedelta(hours=3)).isoformat(),'home':'NYR','away':'VAN','home_name':'New York Rangers','away_name':'Vancouver Canucks','home_id':'3','away_id':'23','home_score':4,'away_score':3,'regular':True,'neutral':False,'completed':False,'state':'pre'},**edits}

    def event(self,g=None,**edits):
        g=g or self.game()
        return {**g,'event_id':'espn1','odds':[{'provider':'fixture','home_moneyline':-120,'away_moneyline':100}],**edits}

    def capture(self,root):
        capture=n.Capture(root/'capture')
        capture.retain('fixture.json',{'fixture':True},{'source_url':'https://example.com/scoreboard','retrieved_at':(self.clock-timedelta(minutes=1)).isoformat()})
        return capture

    def record(self,root,capture,games=None,events=None):
        games=games or [self.game()]
        events=events or [self.event(g) for g in games]
        model={'weights':[.1,.4],'frozen_at':(self.clock-timedelta(hours=1)).isoformat()}
        with patch.object(n,'now',return_value=self.clock):
            return p.record_forecasts(root,capture,[],games,events,model,self.config,{})

    def final(self,root,capture,game=None,event=None):
        g=game or self.game(completed=True,state='post')
        e=event or self.event(g)
        return p.settle(root,capture,[g],[e],'NHL')

    def test_matching_identity_time_uniqueness_and_venue(self):
        for edit in [{'home':'WRONG'},{'kickoff':(self.clock+timedelta(hours=4)).isoformat()},{'neutral':True}]:
            with self.subTest(edit=edit),self.assertRaises(ValueError):p.match(self.game(),[self.event(**edit)],'NHL')
        with self.assertRaises(ValueError):p.match(self.game(),[self.event(),self.event()],'NHL')

    def test_doubleheaders_require_exact_start(self):
        later=self.game(game_id='2',kickoff=(self.clock+timedelta(hours=7)).isoformat())
        self.assertEqual(p.match(later,[self.event(),self.event(later,event_id='espn2')],'MLB')['event_id'],'espn2')

    def test_nhl_strict_final_and_game_type(self):
        g={'id':1,'season':20262027,'gameType':2,'startTimeUTC':self.game()['kickoff'],'homeTeam':{'id':3,'abbrev':'NYR','score':4},'awayTeam':{'id':23,'abbrev':'VAN','score':3},'gameState':'OFF','gameScheduleState':'OK'}
        self.assertTrue(p.nhl_games({'games':[g]})[0]['completed'])
        self.assertFalse(p.nhl_games({'games':[{**g,'gameScheduleState':'PPD'}]})[0]['completed'])
        self.assertEqual(p.nhl_games({'games':[{**g,'gameType':1}]}),[])

    def test_mlb_suspended_and_tbd_not_final_or_eligible(self):
        g={'gamePk':1,'gameType':'L','season':'2026','gameDate':self.game()['kickoff'],'teams':{s:{'team':{'id':i,'name':s},'score':score} for s,i,score in [('home',3,6),('away',23,5)]},'status':{'abstractGameState':'Final','codedGameState':'F','detailedState':'Final'}}
        parse=lambda row:p.mlb_games({'dates':[{'games':[row]}]})[0]
        self.assertTrue(parse(g)['completed'])
        for detail in ['Suspended','Completed Early','Postponed']:
            self.assertFalse(parse({**g,'status':{**g['status'],'detailedState':detail}})['completed'])
        self.assertEqual(parse({**g,'status':{'abstractGameState':'Preview','detailedState':'Scheduled','startTimeTBD':True}})['state'],'in')

    def test_duplicate_resumption_uses_later_time(self):
        early=self.game(completed=True,kickoff=(self.clock-timedelta(days=10)).isoformat())
        late={**early,'kickoff':(self.clock-timedelta(days=1)).isoformat()}
        rows=p.unique_finals([early,late],self.clock)
        self.assertEqual(rows[0]['kickoff'],late['kickoff'])
        self.assertTrue(rows[0]['historical_resumption_ambiguous'])

    def test_conflicting_and_invalid_finals_rejected(self):
        g=self.game(completed=True,kickoff=(self.clock-timedelta(days=1)).isoformat())
        for rows in [[g,{**g,'home_score':99}],[{**g,'home_score':3}],[{**g,'home_score':True}],[{**g,'home_id':g['away_id']}]]:
            with self.subTest(rows=rows),self.assertRaises(ValueError):p.unique_finals(rows,self.clock)

    def test_current_and_future_scores_cannot_leak(self):
        target=self.game()
        before=p.pregame([],target,self.clock,self.config)
        after=p.pregame([self.game(completed=True,home_score=99)],{**target,'home_score':99},self.clock,self.config)
        self.assertEqual(before,after)

    def test_result_delay(self):
        g=self.game(completed=True,kickoff=(self.clock-timedelta(hours=11)).isoformat())
        self.assertEqual(p.pregame([g],self.game(),self.clock,self.config)[2],0)
        g['kickoff']=(self.clock-timedelta(hours=12)).isoformat()
        self.assertEqual(p.pregame([g],self.game(),self.clock,self.config)[2],1)

    def test_training_and_live_feature_recipe_agree(self):
        history=json.loads((p.ROOT/'nhl/history.json').read_text())[:81]
        target=history[-1]
        expected=p.feature_rows(history,self.config)[-1]['x']
        actual=p.pregame(history[:-1],target,b.utc(target['kickoff'])-timedelta(seconds=1),self.config)[0]
        self.assertEqual(actual,expected)

    def test_late_cutoff_rejected(self):
        with self.assertRaises(ValueError):p.pregame([],self.game(),b.utc(self.game()['kickoff']),self.config)

    def test_forecast_immutable_even_when_prices_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root)
            self.assertEqual(self.record(root,capture)[0],['1'])
            path=root/'predictions/1.json';before=path.read_bytes()
            self.assertEqual(self.record(root,capture,events=[self.event(odds=[])])[0],[])
            self.assertEqual(before,path.read_bytes())

    def test_quote_timestamp_belongs_to_matching_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root)
            observed=(self.clock-timedelta(seconds=15)).isoformat()
            self.record(root,capture,events=[self.event(market_observed_at=observed)])
            self.assertEqual(json.loads((root/'predictions/1.json').read_text())['market_observed_at'],observed)

    def test_all_games_enrolled_without_cap_or_prices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root)
            games=[self.game(game_id=str(i),kickoff=(self.clock+timedelta(hours=3,seconds=i)).isoformat()) for i in range(110)]
            events=[self.event(g,event_id='e'+g['game_id'],odds=[]) for g in games]
            self.assertEqual(len(self.record(root,capture,games,events)[0]),110)
            self.assertIsNone(json.loads((root/'predictions/0.json').read_text())['market'])

    def test_started_and_future_source_games_not_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root)
            started=self.game(kickoff=self.clock.isoformat())
            self.assertEqual(self.record(root,capture,[started],[self.event(started)])[0],[])
            capture.evidence[0]['retrieved_at']=(self.clock+timedelta(seconds=1)).isoformat()
            new,excluded=self.record(root,capture)
            self.assertEqual(new,[]);self.assertIn('Future',excluded[0]['reason'])

    def test_ot_shootout_or_extra_inning_final_is_two_way(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root);self.record(root,capture)
            self.assertEqual(self.final(root,capture),(['1'],[]))
            result=json.loads((root/'results/1.json').read_text())
            self.assertEqual(result['outcome'],'home');self.assertEqual(set(result['scores']),{'model','fixed_elo','market'})
            self.assertEqual(self.final(root,capture),([],[]))

    def test_unverified_or_disputed_finals_stay_pending(self):
        for edits in [{'completed':False},{'state':'in'},{'away_score':8},{'event_id':'other'}]:
            with self.subTest(edits=edits),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);capture=self.capture(root);self.record(root,capture)
                g=self.game(completed=True,state='post')
                self.assertEqual(self.final(root,capture,g,self.event(g,**edits))[0],[])
                self.assertFalse((root/'results/1.json').exists())

    def test_nhl_final_time_revision_keeps_all_other_guards(self):
        g=self.game(completed=True,state='post')
        revised=(b.utc(g['kickoff'])+timedelta(minutes=15)).isoformat()
        cases=[{'event_id':'other'},{'home':'WRONG'},{'neutral':True},
               {'away_score':8},{'completed':False},{'state':'in'},
               {'kickoff':(b.utc(g['kickoff'])+timedelta(minutes=15,seconds=1)).isoformat()}]
        for edit in cases:
            with self.subTest(edit=edit),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);capture=self.capture(root);self.record(root,capture)
                e=self.event(g,kickoff=revised,**{k:v for k,v in edit.items() if k!='kickoff'})
                if 'kickoff' in edit:e['kickoff']=edit['kickoff']
                self.assertEqual(self.final(root,capture,g,e)[0],[])
                self.assertFalse((root/'results/1.json').exists())
        with self.assertRaises(ValueError):p.match_final(g,[self.event(g),self.event(g)],'NHL',self.event(g))
        # A revised official time is still a different saved forecast identity.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root);self.record(root,capture)
            changed={**g,'kickoff':revised}
            self.assertEqual(self.final(root,capture,changed,self.event(changed))[0],[])

    def test_time_revision_remains_ineligible_for_enrollment_and_mlb(self):
        g=self.game();e=self.event(g,kickoff=(b.utc(g['kickoff'])+timedelta(minutes=15)).isoformat())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root)
            new,excluded=self.record(root,capture,[g],[e])
            self.assertEqual(new,[]);self.assertTrue(excluded)
        with self.assertRaises(ValueError):p.match_final(g,[e],'MLB',e)

    def test_saved_nhl_time_revisions_settle_from_archived_evidence(self):
        league=p.ROOT/'nhl'
        manifest=json.loads((league/'captures/20261014T115856760081Z/manifest.json').read_text())
        sources=[s for s in manifest['sources'] if '/schedule/2026-10-13' in s['source_url'] or 'scoreboard?dates=20261013' in s['source_url']]
        for source in sources:self.assertEqual(b.sha256(Path(source['path']).read_bytes()),source['sha256'])
        games=json.loads(Path(sources[0]['path']).read_text())
        events=json.loads(Path(sources[1]['path']).read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root);capture.evidence=sources
            originals={}
            for identifier in ['2026020100','2026020105']:
                originals[identifier]=(league/'predictions'/(identifier+'.json')).read_bytes()
                path=root/'predictions'/(identifier+'.json');path.parent.mkdir(exist_ok=True);path.write_bytes(originals[identifier])
                pred=json.loads(originals[identifier]);game=next(g for g in games if g['game_id']==identifier)
                with self.assertRaises(ValueError):p.match(game,events,'NHL')
                self.assertEqual(p.match_final(game,events,'NHL',pred)['event_id'],pred['event_id'])
            new,errors=p.settle(root,capture,games,events,'NHL')
            self.assertEqual(set(new),set(originals));self.assertEqual(errors,[])
            for identifier,original in originals.items():
                self.assertEqual((root/'predictions'/(identifier+'.json')).read_bytes(),original)
                result=json.loads((root/'results'/(identifier+'.json')).read_text())
                self.assertEqual(result['outcome'],'away')
                self.assertEqual(result['match_verification']['start_time_difference_seconds'],900)
                self.assertEqual(result['match_verification']['method'],'nhl_saved_event_bounded_start_time')
            self.assertEqual(p.settle(root,capture,games,events,'NHL'),([],[]))

    def test_tampered_and_late_predictions_stay_pending(self):
        for edit in [{'model':{'home':.99,'away':.01}},{'recorded_at':self.game()['kickoff']},{'generated_at':self.game()['kickoff']}]:
            with self.subTest(edit=edit),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);capture=self.capture(root);self.record(root,capture)
                path=root/'predictions/1.json';data=json.loads(path.read_text());data.update(edit)
                # Even a rehashed late forecast is not accepted.
                if 'model' not in edit:
                    data.pop('sha256');data['sha256']=b.sha256(b.canonical(data))
                n.write_json(path,data)
                new,errors=self.final(root,capture)
                self.assertEqual(new,[]);self.assertTrue(errors)

    def test_no_market_scores_are_not_counted_as_paired(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root);self.record(root,capture,events=[self.event(odds=[])])
            self.final(root,capture)
            summary=p.report(root,'NHL')
            self.assertEqual(summary['settled'],1);self.assertEqual(summary['paired_games'],0)
            self.assertIsNone(summary['paired_metrics']['market']['brier'])

    def test_one_league_failure_does_not_skip_other(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(p,'ROOT',Path(tmp)),patch.object(p,'run_sport',side_effect=[RuntimeError('fixture failure'),{'sport':'MLB'}]) as collect:
            with self.assertRaises(RuntimeError),patch('builtins.print'):p.run()
            self.assertEqual([c.args[0] for c in collect.call_args_list],['NHL','MLB'])
            self.assertFalse(json.loads(next((Path(tmp)/'nhl/errors').glob('*.json')).read_text())['collection_completed'])

    def test_actual_frozen_assets_and_initial_forecasts(self):
        protocol=json.loads((p.ROOT/'protocol.json').read_text())
        for name,digest in json.loads((p.ROOT/'frozen_assets.json').read_text()).items():
            self.assertEqual(b.sha256((p.ROOT/name).read_bytes()),digest)
        for sport,ids in [('nhl',['2026020084','2026020085','2026020086']),('mlb',['849809'])]:
            model=json.loads((p.ROOT/sport/'model.json').read_text());history=json.loads((p.ROOT/sport/'history.json').read_text())
            self.assertEqual(model['history_sha256'],b.sha256(b.canonical(history)))
            self.assertEqual(model['protocol_sha256'],b.sha256(b.canonical(protocol)))
            self.assertEqual(len(model['weights']),2)
            for identifier in ids:
                d=json.loads((p.ROOT/sport/'predictions'/(identifier+'.json')).read_text());digest=d.pop('sha256')
                self.assertEqual(digest,b.sha256(b.canonical(d)))
                self.assertEqual(d['model_sha256'],b.sha256(b.canonical(model)))
                self.assertLess(b.utc(model['frozen_at']),b.utc(d['generated_at']))
                self.assertLessEqual(b.utc(d['generated_at']),b.utc(d['recorded_at']))
                self.assertLess(b.utc(d['recorded_at']),b.utc(d['kickoff']))
                self.assertTrue(d['NO_BET']);self.assertEqual(d['actual_wagers'],0)
                self.assertFalse(d['availability']['effect_enabled'])
                for source in d['source_snapshots']:
                    self.assertLessEqual(b.utc(source['retrieved_at']),b.utc(d['generated_at']))
                    self.assertEqual(b.sha256(Path(source['path']).read_bytes()),source['sha256'])

    def test_models_reproduce_from_frozen_training_recipe(self):
        protocol=json.loads((p.ROOT/'protocol.json').read_text())
        for sport in ['NHL','MLB']:
            root=p.ROOT/sport.lower();history=json.loads((root/'history.json').read_text());saved=json.loads((root/'model.json').read_text())
            refit=p.fit_model(history,protocol[sport],protocol)
            self.assertEqual(refit['training_games'],saved['training_games'])
            for actual,expected in zip(refit['weights'],saved['weights']):self.assertAlmostEqual(actual,expected,places=12)


if __name__=='__main__':unittest.main()
