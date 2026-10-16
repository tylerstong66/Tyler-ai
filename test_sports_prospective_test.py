import copy
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from dataclasses import replace
import sports_prospective_test as p
import sports_historical_benchmark as b
import sports_efficiency_candidate as c


class ProspectiveWeekUncertaintyTests(unittest.TestCase):
    def rows(self, blocks):
        return [
            {"week": f"2026/{i}", "model_brier": 0.3 + 0.03 * i,
             "market_brier": 0.6 - 0.01 * i}
            for i in range(blocks)
        ]

    def test_empty_is_unavailable(self):
        self.assertIsNone(p.prospective_week_block_uncertainty([]))

    def test_one_two_and_four_week_blocks_withhold_confidence_interval(self):
        for blocks in (1, 2, 4):
            with self.subTest(blocks=blocks):
                records=self.rows(blocks)
                result=p.prospective_week_block_uncertainty(records)
                self.assertEqual(result["blocks"],blocks)
                self.assertEqual(result["minimum_blocks"],5)
                self.assertIsNone(result["approximate_95_percent_interval"])
                self.assertEqual(result["draws"],0)
                self.assertEqual(result["uncertainty_status"],"insufficient_blocks")
                expected=sum(v["model_brier"]-v["market_brier"]
                             for v in records)/len(records)
                self.assertAlmostEqual(result["mean_model_minus_market"],expected)

    def test_five_week_blocks_unlock_only_descriptive_interval(self):
        records=self.rows(5)
        result=p.prospective_week_block_uncertainty(records)
        expected=b.week_bootstrap(records)
        self.assertEqual(result["approximate_95_percent_interval"],
                         expected["approximate_95_percent_interval"])
        self.assertEqual(result["blocks"],5)
        self.assertEqual(result["minimum_blocks"],5)
        self.assertEqual(result["uncertainty_status"],"available_descriptive")
        self.assertIn("not",result["limitation"])


class ProspectiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history=b.read_games('benchmarks/nfl_independent_v1/games_2010_2025.csv',last=2024)
        cls.stats=c.read_stats('benchmarks/nfl_efficiency_v2/team_stats_2010_2024.csv',cls.history)
        cls.v2=json.loads(Path('benchmarks/nfl_efficiency_v2/run_2026_10_11/model.json').read_text())
        cls.v1=json.loads(Path('benchmarks/nfl_independent_v1/run_2026_10_11/model.json').read_text())
        cls.clock=b.utc('2026-10-11T15:30:00Z')
        cls.target=replace(cls.history[-1],identifier='future',season=2026,week=5,game_type='REG',kickoff=cls.clock+timedelta(hours=2))

    def event(self,game=None):
        g=game or self.target
        return {'event_id':'123','home':g.home,'away':g.away,'kickoff':g.kickoff.isoformat(),'neutral':g.neutral,'state':'pre','completed':False,'home_score':0,'away_score':0,'odds':[{'provider':'test','home_moneyline':-120,'away_moneyline':100}]}

    def capture(self,root):
        capture=p.Capture(root/'capture')
        capture.retain('espn.json',{'test_fixture':True},{'source_url':'https://example.com/scoreboard','retrieved_at':(self.clock-timedelta(minutes=1)).isoformat()})
        return capture

    def test_exact_event_identity_and_venue(self):
        for edits in [{'home':'WRONG'},{'kickoff':(self.target.kickoff+timedelta(minutes=1)).isoformat()},{'neutral':not self.target.neutral}]:
            with self.subTest(edits=edits),self.assertRaises(ValueError):p.match_event(self.target,[{**self.event(),**edits}])
        with self.assertRaises(ValueError):p.match_event(self.target,[self.event(),self.event()])

    def test_current_target_scores_never_change_features(self):
        a=p.pregame_features(self.history,self.stats,self.target,self.clock.isoformat())
        b_=p.pregame_features(self.history,self.stats,replace(self.target,home_score=99,away_score=2),self.clock.isoformat())
        self.assertEqual(a['x'],b_['x'])

    def test_future_history_is_not_consumed(self):
        a=p.pregame_features(self.history,self.stats,self.target,self.clock.isoformat())
        b_=p.pregame_features(self.history+[replace(self.target,home_score=99)],self.stats,self.target,self.clock.isoformat())
        self.assertEqual(a['x'],b_['x'])

    def test_recent_final_does_not_require_not_yet_eligible_efficiency_stats(self):
        recent=replace(self.target,identifier='recent',kickoff=self.clock-timedelta(hours=30),home_score=24,away_score=17)
        actual=p.pregame_features(self.history+[recent],self.stats,self.target,self.clock.isoformat())
        original=p.pregame_features(self.history,self.stats,self.target,self.clock.isoformat())
        self.assertEqual(actual['x'][5:],original['x'][5:])
        self.assertEqual(actual['prior_results_used'],original['prior_results_used']+1)

    def test_same_history_features_match_frozen_recipe(self):
        g=self.history[100]
        cutoff=g.kickoff-timedelta(seconds=1)
        actual=p.pregame_features(self.history[:100],self.stats,g,cutoff.isoformat())
        expected=c.features(self.history[:101],self.stats)[-1]
        self.assertEqual(actual['x'],expected['x'])

    def test_late_cutoff_rejected(self):
        with self.assertRaises(ValueError):p.pregame_features(self.history,self.stats,self.target,self.target.kickoff.isoformat())

    def test_freeze_once_and_preserve_hash(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(p,'now',return_value=self.clock):
            root=Path(tmp);capture=self.capture(root)
            new=p.forecast(root,capture,self.history,self.stats,[self.target],[self.event()],self.v2,self.v1,{})
            self.assertEqual(new,['future']);path=root/'predictions/future.json';before=path.read_bytes()
            self.assertEqual(p.forecast(root,capture,self.history,self.stats,[self.target],[self.event()],self.v2,self.v1,{}),[])
            self.assertEqual(path.read_bytes(),before)
            d=json.loads(before);digest=d.pop('sha256');self.assertEqual(digest,b.sha256(b.canonical(d)))
            self.assertEqual(d['actual_wagers'],0)
            for model in ['v2','v1']:self.assertAlmostEqual(sum(d[model].values()),1)

    def test_started_games_are_excluded(self):
        game=replace(self.target,kickoff=self.clock-timedelta(minutes=1))
        with tempfile.TemporaryDirectory() as tmp,patch.object(p,'now',return_value=self.clock):
            root=Path(tmp);capture=self.capture(root)
            self.assertEqual(p.forecast(root,capture,self.history,self.stats,[game],[self.event(game)],self.v2,self.v1,{}),[])
            log=json.loads((capture.folder/'enrollment.json').read_text())
            self.assertEqual(log['excluded'][0]['reason'],'already_started')

    def test_source_after_generation_is_excluded(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(p,'now',return_value=self.clock):
            root=Path(tmp);capture=self.capture(root);capture.evidence[0]['retrieved_at']=(self.clock+timedelta(seconds=1)).isoformat()
            self.assertEqual(p.forecast(root,capture,self.history,self.stats,[self.target],[self.event()],self.v2,self.v1,{}),[])

    def prepare_prediction(self,root,capture):
        with patch.object(p,'now',return_value=self.clock):p.forecast(root,capture,self.history,self.stats,[self.target],[self.event()],self.v2,self.v1,{})

    def test_final_requires_both_sources_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root);self.prepare_prediction(root,capture)
            game=replace(self.target,home_score=24,away_score=20)
            event={**self.event(),'state':'post','completed':True,'home_score':24,'away_score':20}
            self.assertEqual(p.settle(root,capture,[self.event()],[game]),([],[]))
            new,errors=p.settle(root,capture,[{**event,'away_score':21}],[game]);self.assertFalse(new);self.assertTrue(errors)
            new,errors=p.settle(root,capture,[event],[game]);self.assertEqual(new,['future']);self.assertFalse(errors)
            result=(root/'results/future.json').read_bytes()
            self.assertEqual(p.settle(root,capture,[event],[game]),([],[]))
            self.assertEqual((root/'results/future.json').read_bytes(),result)
            summary=p.report(root);self.assertEqual(summary['settled'],1);self.assertEqual(summary['paired_priced_decisive_games'],1)

    def test_changed_prediction_cannot_be_graded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root);self.prepare_prediction(root,capture)
            path=root/'predictions/future.json';d=json.loads(path.read_text());d['v2']['home']=.99;p.write_json(path,d)
            game=replace(self.target,home_score=24,away_score=20)
            event={**self.event(),'state':'post','completed':True,'home_score':24,'away_score':20}
            new,errors=p.settle(root,capture,[event],[game]);self.assertFalse(new);self.assertIn('hash mismatch',errors[0]['reason'])

    def test_rescheduled_final_stays_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root);self.prepare_prediction(root,capture)
            game=replace(self.target,kickoff=self.target.kickoff+timedelta(days=1),home_score=24,away_score=20)
            event={**self.event(game),'state':'post','completed':True,'home_score':24,'away_score':20}
            new,errors=p.settle(root,capture,[event],[game])
            self.assertFalse(new);self.assertIn('saved prediction',errors[0]['reason'])

    def test_tie_keeps_full_scores_and_excludes_two_way_market(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);capture=self.capture(root);self.prepare_prediction(root,capture)
            game=replace(self.target,home_score=20,away_score=20)
            event={**self.event(),'state':'post','completed':True,'home_score':20,'away_score':20}
            p.settle(root,capture,[event],[game]);summary=p.report(root)
            self.assertEqual(summary['paired_priced_decisive_games'],0)
            self.assertIsNotNone(summary['full_three_outcome_metrics']['v2']['full_brier'])

    def test_official_report_preserves_qb_designation_not_starter(self):
        source={'source_url':'https://www.nfl.com/news/test','retrieved_at':self.clock.isoformat(),'sha256':'a'*64}
        g=replace(self.target,home='ATL',away='BAL')
        article={'@type':'NewsArticle','headline':'NFL Week 5 injury report','dateModified':'2026-10-10T10:00:00Z','articleBody':'RAVENS\nOUT: QB Lamar Jackson (ankle)\nFALCONS\nQUESTIONABLE: LT Jake Matthews (groin)'}
        html='<script type="application/ld+json">'+json.dumps(article)+'</script>'
        result=p.extract_injuries(html,source,g)
        qb=next(r for r in result['observations'] if r['position']=='QB')
        self.assertEqual(qb['status'],'out')
        self.assertEqual(result['confirmed_starting_qb']['away'],'unknown')
        self.assertFalse(result['injury_effect_enabled'])
        self.assertEqual(p.extract_injuries(html,source,replace(g,week=6))['coverage'],'unknown')

    def test_market_normalization(self):
        self.assertAlmostEqual(p.binary_market([{'home_moneyline':-100,'away_moneyline':100}])['conditional_home_probability'],.5)

    def test_unverified_injury_publications_keep_effects_explicitly_disabled(self):
        source={'source_url':'https://www.nfl.com/news/test','retrieved_at':self.clock.isoformat(),'sha256':'a'*64}
        article={'@type':'NewsArticle','headline':'NFL Week 5 injury report','dateModified':'2026-10-10T10:00:00Z','articleBody':'EAGLES\nOUT: QB Example Player (ankle)'}
        cases=[('', 'official publication metadata unavailable'),
               ({**article,'headline':'NFL Week 6 injury report'}, 'report week mismatch'),
               ({**article,'dateModified':'2025-10-10T10:00:00Z'}, 'publication not verified for season'),
               ({**article,'dateModified':'2026-10-12T10:00:00Z'}, 'publication not verified for season'),
               ({**article,'dateModified':None}, 'publication not verified for season')]
        for data,reason in cases:
            with self.subTest(reason=reason,data=data):
                html='<script type="application/ld+json">'+json.dumps(data)+'</script>' if data else ''
                availability=p.extract_injuries(html,source,self.target)
                self.assertEqual(availability['coverage'],'unknown')
                self.assertEqual(availability['observations'],[])
                self.assertEqual(availability['reason'],reason)
                self.assertIs(availability['injury_effect_enabled'],False)

    def test_real_artifacts_were_all_pre_kickoff_and_hash_valid(self):
        files=list(p.ROOT.glob('predictions/*.json'));self.assertGreaterEqual(len(files),12)
        for path in files:
            d=json.loads(path.read_text());digest=d.pop('sha256')
            self.assertEqual(digest,b.sha256(b.canonical(d)))
            self.assertLess(b.utc(d['recorded_at']),b.utc(d['kickoff']))
            self.assertLess(b.utc(d['generated_at']),b.utc(d['kickoff']))
            self.assertEqual(d['v2_model_sha256'],b.sha256(b.canonical(self.v2)))
            for s in d['source_snapshots']:self.assertLessEqual(b.utc(s['retrieved_at']),b.utc(d['generated_at']))
            if digest=='ff7e1ac7c355589e75e00c7acce782a2a26600447910716f90b5e5aa698318b1':
                # Preserve this exact pre-fix artifact; every new artifact must
                # carry the explicit flag, including all unknown-coverage paths.
                self.assertEqual(d['game_id'],'2026_06_SEA_DEN')
                self.assertEqual(d['availability'],{'coverage':'unknown','observations':[],
                                                  'reason':'publication not verified for season'})
            else:
                self.assertIs(d['availability']['injury_effect_enabled'],False)


if __name__=='__main__':unittest.main()
