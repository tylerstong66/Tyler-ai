import copy
import json
import unittest
from unittest.mock import patch

import app_v2_19_3_33 as v
from sports_betting import SportsLedger, digest
from sports_mlb_paper import MlbPublicFeed, MlbPaperTrial
from sports_paper_trial import PaperTrial, PAPER_PREDICTIONS, PAPER_RESULTS
from sports_paper_evidence import (EvidenceNflTrial, EvidenceNhlTrial, starter_reports,
    goalie_games, bounded_forecast, evidence_facts)
from sports_paper_dashboard import comparison, FinalCollector, dashboard_html
from test_v2_18_skill_lab import MemoryStore
from test_v2_19_3_31_sports_paper import FakeFeed, game, forecast, NOW
from test_v2_19_3_32_sports_nhl import game as nhl_game, forecast as nhl_forecast


class EvidenceTests(unittest.TestCase):
    def goalie(self):
        g=nhl_game();g['event_start']='2026-10-10T23:00:00Z'
        row={'date':'2026-10-10','time':'19:00', **{s+'TeamName':g['teams'][s]['name'] for s in ('home','away')},
            'homeGoalieName':'A Goalie','homeNewsStrengthName':'Confirmed','homeNewsDetails':'Goalie will start Saturday vs. the Rangers.',
            'homeNewsCreatedAt':'2026-10-10T14:00:00Z','homeNewsSourceUrl':'https://x.com/reporter/status/123'}
        return g,row

    def test_dated_game_specific_report_is_relayed_not_independently_verified(self):
        g,row=self.goalie();r=starter_reports(g,[row],'2026-10-10T18:00:00Z')
        self.assertEqual(r['home']['status'],'reported_confirmed')
        self.assertFalse(r['home']['primary_report_independently_retrieved'])
        self.assertEqual(r['away']['status'],'unconfirmed')

    def test_recycled_future_likely_wrong_opponent_and_untrusted_url_are_unconfirmed(self):
        g,row=self.goalie()
        for update in [{'homeNewsCreatedAt':'2026-10-08T14:00:00Z'}, {'homeNewsCreatedAt':'2026-10-10T20:00:00Z'},
            {'homeNewsStrengthName':'Likely'}, {'homeNewsDetails':'Goalie will start vs. the Flyers.'},
            {'homeNewsSourceUrl':'https://attacker.example/report'}, {'homeNewsDetails':'Goalie is projected vs. the Rangers.'}]:
            with self.subTest(update=update):
                self.assertEqual(starter_reports(g,[{**row,**update}],'2026-10-10T18:00:00Z')['home']['status'],'unconfirmed')

    def test_starter_matching_rejects_ambiguity_wrong_time_and_wrong_team(self):
        g,row=self.goalie()
        for rows in [[row,row],[{**row,'time':'20:00'}],[{**row,'awayTeamName':'Other Team'}]]:
            with self.assertRaisesRegex(ValueError,'uniquely'):starter_reports(g,rows,'2026-10-10T18:00:00Z')

    def test_publisher_script_is_parsed_as_data_and_not_executed(self):
        _,row=self.goalie();node=['$','$L2',None,{'initialData':{'games':[row]}}]
        payload=json.dumps([1,'24:'+json.dumps(node)])
        html='<script>self.__next_f.push('+payload+')</script><script>bad()</script>'
        self.assertEqual(goalie_games(html),[row])
        with self.assertRaises(ValueError):goalie_games(html+html)

    def test_free_claims_invalid_ids_duplicates_and_invalid_probabilities_are_rejected(self):
        facts=evidence_facts(game());raw={'probabilities':forecast()['probabilities'],'fact_ids':['market']}
        result=bounded_forecast(raw,facts,'NFL');self.assertIn('Observed two-way prices',result['rationale'])
        for bad in [{**raw,'rationale':'Elite offense'}, {**raw,'fact_ids':['offense']}, {**raw,'fact_ids':['market','market']},
                    {**raw,'probabilities':{'home':float('nan'),'away':.4,'tie':.01}}]:
            with self.assertRaises(ValueError):bounded_forecast(bad,facts,'NFL')

    def test_stats_require_retrieved_source_valid_numeric_sample_and_no_starter_assumption(self):
        g=nhl_game();g['official_goalie_comparison']={'contextSeason':20262027,'homeTeam':{'teamTotals':{'gamesPlayed':3,'gaa':2.5,'savePctg':.92}}}
        self.assertNotIn('home_goaltending',[f['id'] for f in evidence_facts(g)])
        g['evidence']['official_game']=g['evidence']['event_market_injuries']
        f=next(f for f in evidence_facts(g) if f['id']=='home_goaltending');self.assertIn('3 games',f['text']);self.assertIn('not starter confirmation',f['text'])
        g['official_goalie_comparison']['homeTeam']['teamTotals']['savePctg']=True
        self.assertNotIn('home_goaltending',[f['id'] for f in evidence_facts(g)])


class CohortAndMetricsTests(unittest.TestCase):
    def setUp(self):
        self.store=MemoryStore();self.now=NOW;self.feed=FakeFeed()
        self.ledger=SportsLedger(self.store.get_rows,self.store.save_row,lambda:self.now)
        self.old=PaperTrial(self.ledger,self.feed,lambda g:forecast(),'fixed',lambda:{'version':1})
        self.new=EvidenceNflTrial(self.ledger,self.feed,lambda g:forecast(),'fixed',lambda:{'version':1})

    def final(self,tie=False):
        self.now='2026-10-11T18:00:00Z';self.feed.data.update(state='post',completed=True)
        self.feed.data['teams']['home']['score']='24';self.feed.data['teams']['away']['score']='24' if tie else '17'

    def test_same_game_shadow_cohort_does_not_rewrite_original(self):
        old=self.old.analyze('401872981');encoded=self.store.rows[0]['memories']
        new=self.new.analyze('401872981');self.assertEqual(new['cohort'],'nfl-evidence-paper-v2')
        self.assertEqual(self.store.rows[0]['memories'],encoded);self.assertNotEqual(old['paper_prediction_id'],new['paper_prediction_id'])
        self.final();self.new.settle(new['paper_prediction_id']);self.assertEqual(len(self.ledger._records(PAPER_RESULTS)),0)

    def test_paired_market_brier_conditions_nfl_on_no_tie(self):
        r=self.new.analyze('401872981');self.final();self.new.settle(r['paper_prediction_id']);c=comparison(self.new)
        self.assertEqual(c['paired_priced_count'],1);self.assertEqual(c['paired_favorite_accuracy'],1)
        self.assertAlmostEqual(c['paired_tyler_brier'],2*(1-.6/.99)**2)
        self.assertAlmostEqual(c['paired_favorite_hypothetical_roi'],.8)
        self.assertEqual(c['actual_wager_amount'],0)

    def test_tie_is_push_in_full_report_and_excluded_from_conditional_baselines(self):
        r=self.new.analyze('401872981');self.final(True);self.new.settle(r['paper_prediction_id'])
        c=comparison(self.new);self.assertEqual(c['excluded_tie_count'],1);self.assertEqual(c['paired_priced_count'],0)
        self.assertIsNone(c['paired_tyler_brier']);self.assertEqual(self.new.report()['hypothetical_flat_unit_roi'],0)

    def test_unpriced_final_has_accuracy_but_no_invented_market_baseline(self):
        self.feed.data['moneyline_quote']=None;r=self.new.analyze('401872981');self.final();self.new.settle(r['paper_prediction_id'])
        c=comparison(self.new);self.assertEqual(c['tyler_pick_accuracy'],1);self.assertEqual(c['paired_priced_count'],0)

    def test_changed_prediction_hash_fails_baseline_linkage(self):
        r=self.new.analyze('401872981');self.final();self.new.settle(r['paper_prediction_id'])
        changed=copy.deepcopy(r);changed['forecast']['probabilities']['home']=.8
        with patch.object(self.new,'records',return_value=[changed]),self.assertRaisesRegex(RuntimeError,'integrity'):comparison(self.new)

    def test_collector_is_idempotent_skips_future_and_never_calls_model(self):
        r=self.new.analyze('401872981');collector=FinalCollector({'NFL':self.new},lambda:self.now)
        self.new.forecast_fn=lambda g:self.fail('Collector must never generate forecasts')
        self.assertEqual(collector.collect()['checked'],0)
        self.final();self.assertEqual(collector.collect()['new_results'],1)
        self.assertEqual(collector.collect()['new_results'],0);self.assertEqual(len(self.ledger._records(self.new.result_category)),1)

    def test_collector_continues_after_feed_error_and_treats_nonfinal_as_pending(self):
        self.old.analyze('401872981');self.new.analyze('401872981');self.final()
        with patch.object(self.old,'settle',side_effect=RuntimeError('network')):
            c=FinalCollector({'old':self.old,'new':self.new},lambda:self.now).collect()
        self.assertEqual(c['errors'],1);self.assertEqual(c['new_results'],1)
        self.feed.data['completed']=False
        c=FinalCollector({'old':self.old},lambda:self.now).collect();self.assertEqual(c['errors'],0);self.assertEqual(c['counts']['old']['pending'],1)

    def test_sourced_nhl_settles_in_own_category_using_pinned_official_id(self):
        self.now='2026-10-09T20:00:00Z';g=nhl_game()
        class Feed:
            def pregame(_,identifier):return copy.deepcopy(g)
            def final_game(_,record):
                self.assertEqual(record['snapshot']['official_game_id'],'2026020067')
                f=copy.deepcopy(g);f.update(state='post',completed=True)
                f['teams']['home']['score']=3;f['teams']['away']['score']=1;return f
        t=EvidenceNhlTrial(self.ledger,Feed(),lambda g:nhl_forecast(),'fixed',lambda:{'version':1})
        r=t.analyze(g['event_id']);self.now='2026-10-10T04:00:00Z';t.settle(r['paper_prediction_id'])
        self.assertEqual(t.report()['settled_in_window'],1);self.assertEqual(self.ledger._records('sports_nhl_paper_result'),[])


def mlb_data():
    return {'gamePk':849831,'gameData':{'game':{'type':'D'},'datetime':{'dateTime':'2026-10-11T00:00:00Z'},
        'status':{'abstractGameState':'Preview','codedGameState':'S','detailedState':'Scheduled'},
        'teams':{'home':{'id':114,'name':'home'},'away':{'id':145,'name':'away'}},
        'probablePitchers':{'home':{'id':123,'fullName':'Probable Pitcher'}}},
        'liveData':{'boxscore':{'teams':{'home':{'battingOrder':[],'players':{}},'away':{'battingOrder':[],'players':{}}}},
            'linescore':{'teams':{'home':{'runs':3},'away':{'runs':1}}}}}


class MlbTests(unittest.TestCase):
    def setUp(self):
        self.data=mlb_data();self.g=game();self.g['event_start']='2026-10-11T00:00:00Z'
        self.schedule={'dates':[{'games':[{'gamePk':849831,'gameDate':self.g['event_start'],'teams':{s:{'team':t} for s,t in self.data['gameData']['teams'].items()}}]}]}
        self.calls=[];self.feed=MlbPublicFeed(now_fn=lambda:NOW)
        def fetch(url,params=None,text=False):
            self.calls.append(url);data=self.schedule if url.endswith('/schedule') else self.data
            return copy.deepcopy(data),{'source_url':url,'retrieved_at':NOW,'response_sha256':digest(data)}
        self.feed._fetch=fetch

    def test_probable_pitcher_not_starter_and_roster_not_lineup(self):
        g=self.feed.official(copy.deepcopy(self.g));self.assertEqual(g['probable_pitchers']['home']['fullName'],'Probable Pitcher')
        self.assertIsNone(g['published_lineups']['home']);self.assertFalse(g['completed'])
        self.assertIn('probable does not mean confirmed',next(f['text'] for f in evidence_facts(g) if f['id']=='home_pitcher'))

    def test_doubleheader_requires_unique_team_and_time_match(self):
        self.schedule['dates'][0]['games']*=2
        with self.assertRaisesRegex(ValueError,'uniquely'):self.feed.official(copy.deepcopy(self.g))

    def test_wrong_id_team_start_or_exhibition_is_rejected(self):
        for change in [lambda d:d.update(gamePk=99),lambda d:d['gameData']['teams']['home'].update(name='other'),
            lambda d:d['gameData']['datetime'].update(dateTime='2026-10-11T01:00:00Z'),lambda d:d['gameData']['game'].update(type='S')]:
            self.data=mlb_data();change(self.data)
            with self.assertRaises(ValueError):self.feed.official(copy.deepcopy(self.g), '849831')

    def test_postponed_suspended_cancelled_and_completed_early_remain_nonfinal(self):
        for state in ['Postponed','Suspended','Cancelled','Completed Early']:
            self.data['gameData']['status']={'abstractGameState':'Final','codedGameState':'F','detailedState':state}
            self.assertFalse(self.feed.official(copy.deepcopy(self.g),'849831')['completed'])
        self.data['gameData']['status']['detailedState']='Final';self.assertTrue(self.feed.official(copy.deepcopy(self.g),'849831')['completed'])

    def test_exactly_nine_distinct_published_hitters_required(self):
        box=self.data['liveData']['boxscore']['teams']['home'];box.update(battingOrder=list(range(1,10)),players={'ID'+str(i):{'person':{'fullName':'Hitter '+str(i)}} for i in range(1,10)})
        self.assertEqual(len(self.feed.official(copy.deepcopy(self.g),'849831')['published_lineups']['home']),9)
        box['battingOrder'][-1]=1;self.assertIsNone(self.feed.official(copy.deepcopy(self.g),'849831')['published_lineups']['home'])

    def test_mlb_final_pins_official_id_appends_result_and_preserves_forecast(self):
        now=[NOW];store=MemoryStore();ledger=SportsLedger(store.get_rows,store.save_row,lambda:now[0])
        g=self.feed.official(copy.deepcopy(self.g));self.feed.pregame=lambda _:copy.deepcopy(g)
        trial=MlbPaperTrial(ledger,self.feed,lambda _:nhl_forecast(),'fixed',lambda:{'version':1})
        r=trial.analyze(g['event_id']);original=store.rows[0]['memories'];self.calls=[]
        self.data['gameData']['status']={'abstractGameState':'Final','codedGameState':'F','detailedState':'Final'};now[0]='2026-10-11T04:00:00Z'
        trial.settle(r['paper_prediction_id']);self.assertEqual(store.rows[0]['memories'],original);self.assertEqual(len(self.calls),1)
        self.assertIn('/849831/feed/live',self.calls[0]);self.assertEqual(trial.report()['sport'],'MLB')


class AppTests(unittest.TestCase):
    def test_dashboard_and_chat_require_existing_authentication(self):
        client=v.app.test_client()
        self.assertEqual(client.get('/ui/paper-results').status_code,401)
        self.assertEqual(client.post('/ui/chat',json={'message':'sports paper collect finals'}).status_code,401)

    def test_authenticated_dashboard_escapes_feed_content_and_disables_cache(self):
        client=v.app.test_client()
        with client.session_transaction() as session:session['tyler_ui_authenticated']=True
        g=game();g['event']='<script>alert(1)</script>';store=MemoryStore();ledger=SportsLedger(store.get_rows,store.save_row,lambda:NOW)
        feed=FakeFeed();feed.data=g;t=PaperTrial(ledger,feed,lambda _:forecast(),'fixed',lambda:{'version':1});t.analyze(g['event_id'])
        with patch.dict(v.ALL_TRIALS,{'NFL original':t},clear=True):r=client.get('/ui/paper-results')
        self.assertEqual(r.status_code,200);self.assertNotIn('<script>alert(1)</script>',r.text);self.assertIn('&lt;script&gt;',r.text)
        self.assertEqual(r.headers['Cache-Control'],'no-store')

    def test_status_preserves_benchmark_and_exposes_only_aggregate_collection(self):
        s=v.status().get_json() if False else v.app.test_client().get('/status').get_json()
        self.assertEqual(s['version'],v.VERSION);self.assertEqual(v.HARNESS_VERSION,v.previous.HARNESS_VERSION)
        self.assertEqual(s['sports_paper_supported_sports'],['NFL','NHL','MLB']);self.assertFalse(s['sports_wager_execution_enabled'])
        self.assertNotIn('predictions',s['sports_paper_result_collector']);self.assertFalse(v.COLLECTOR.enabled)

    def test_unknown_sport_extra_args_and_url_event_id_cannot_fetch(self):
        for text in ['sports evidence paper analyze :: {"sport":"NBA","event_id":"401872981"}',
            'sports evidence paper analyze :: {"sport":"NFL","event_id":"https://evil.example"}',
            'sports evidence paper analyze :: {"sport":"NFL","event_id":"401872981","overwrite":true}']:
            with patch.object(v.FEED,'pregame',side_effect=AssertionError('Must not fetch')):
                payload,status=v.handle_message(text);self.assertEqual(status,409);self.assertFalse(payload['success'])

    def test_new_categories_protected_and_old_prediction_categories_unchanged(self):
        for t in v.EVIDENCE_TRIALS.values():self.assertIn(t.prediction_category,v.PROTECTED_CATEGORIES)
        self.assertEqual(v.PAPER_TRIAL.prediction_category,PAPER_PREDICTIONS)
        self.assertEqual(v.NHL_TRIAL.prediction_category,'sports_nhl_paper_prediction')


if __name__ == '__main__':unittest.main()
