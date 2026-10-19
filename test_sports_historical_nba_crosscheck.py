"""NBA result joins replay raw originals with each game's actual observation time."""
from datetime import timedelta
from pathlib import Path
import json
import tempfile
import unittest

import sports_expansion_historical_capture as history
import sports_nba_historical_owned as owned
import sports_historical_nba_crosscheck as check
import sports_nba_final_receipts as finals
from test_sports_nba_historical_owned import original,NOW
from test_sports_nba_official_schedule_audit import espn_event


class HistoricalNbaCrosscheckTests(unittest.TestCase):
    def repeat_fixture(self, *, second_hours=48, offset_minutes=0):
        import sports_nba_official_schedule_audit as nba
        obj=json.loads(original());games=obj['leagueSchedule']['gameDates'][0]['games']
        second={**games[0], 'gameId':'0022499999',
                'gameDateTimeUTC':(check.source.utc(games[0]['gameDateTimeUTC'])+
                                   timedelta(hours=second_hours)).isoformat()}
        games.append(second)
        official=nba.official_games(json.dumps(obj).encode())
        provider={'401234567':{'espn_game_id':'401234567','home_tricode':'NYK','away_tricode':'BOS',
            'home_team_id':'18','away_team_id':'2','season_stage':2,'provider_completed':True,
            'home_score':106,'away_score':104,
            'scheduled_start_utc':(check.source.utc(games[0]['gameDateTimeUTC'])+
                                   timedelta(minutes=offset_minutes)).isoformat()}}
        return official,provider

    def test_opt_in_repeat_fixtures_require_exact_tipoff_and_preserve_v1(self):
        official,provider=self.repeat_fixture()
        def run(**kwargs):
            return finals.classify(official,provider,nba_observed_at=NOW.isoformat(),
                                   espn_observed_at=NOW.isoformat(),**kwargs)
        self.assertEqual(run()['pending'][0]['reason'],'AMBIGUOUS_NBA_IDENTITY')
        out=run(exact_tipoff_identity=True)
        self.assertEqual(out['two_source_final_agreements'],1)
        self.assertEqual(out['corroborated_research_only'][0]['nba_game_id'],'0022400000')
        self.assertEqual(run()['pending'][0]['reason'],'AMBIGUOUS_NBA_IDENTITY')

    def test_exact_policy_never_resolves_near_duplicates_or_uses_nearest(self):
        for kwargs in ({'second_hours':0},{'second_hours':0.25},{'offset_minutes':1},
                       {'offset_minutes':31}):
            with self.subTest(kwargs=kwargs):
                official,provider=self.repeat_fixture(**kwargs)
                out=finals.classify(official,provider,nba_observed_at=NOW.isoformat(),
                                   espn_observed_at=NOW.isoformat(),exact_tipoff_identity=True)
                self.assertEqual(out['two_source_final_agreements'],0)

    def test_exact_policy_never_selects_by_scores_or_reuses_official_game(self):
        official,provider=self.repeat_fixture()
        provider['401234567']['home_score']=107
        out=finals.classify(official,provider,nba_observed_at=NOW.isoformat(),
                           espn_observed_at=NOW.isoformat(),exact_tipoff_identity=True)
        self.assertEqual(out['pending'][0]['reason'],'CONFLICTING_FINAL_SCORES_NO_GRADE')
        provider['401234567']['home_score']=106
        provider['401234568']={**provider['401234567'],'espn_game_id':'401234568'}
        out=finals.classify(official,provider,nba_observed_at=NOW.isoformat(),
                           espn_observed_at=NOW.isoformat(),exact_tipoff_identity=True)
        self.assertEqual(out['two_source_final_agreements'],0)
        self.assertEqual({x['reason'] for x in out['pending']},{'NON_BIJECTIVE_GAME_IDENTITY'})

    def test_historical_policy_version_and_guards_are_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(td)
            old=check.build(td,now=NOW)
            new=check.build(td,now=NOW,exact_tipoff_identity=True)
            self.assertEqual(old['schema'],'tyler-historical-nba-source-crosscheck-v1')
            self.assertEqual(new['schema'],'tyler-historical-nba-exact-tipoff-crosscheck-v2')
            self.assertEqual(new['game_identity_policy'],'EXACT_UTC_TIPOFF_UNIQUE_WITHIN_30_MINUTES')
            self.assertEqual(old['corroborated_research_only'],new['corroborated_research_only'])
            for key in ('training_allowed','model_training_enabled','historical_evaluation_enabled',
                        'forecasting_enabled','promotion_allowed','source_scope_complete'):
                self.assertIs(new[key],False)

    def seed(self,root,*,score=106,code='NY',official=True):
        if official:owned.capture(lambda _:original(),base=root,now=NOW)
        plan={sport:{split:[bounds[0]] for split,bounds in splits.items()}
              for sport,splits in history.SEASONS.items()}
        def fetch(url):
            events=[]
            if 'basketball/nba' in url:
                e=espn_event();e['date']='2024-10-22T19:00:00Z'
                e['status']['type']={'state':'post','completed':True}
                teams=e['competitions'][0]['competitors'];teams[0]['score']=str(score);teams[1]['score']='104'
                teams[0]['team']['abbreviation']=code;events.append(e)
            return json.dumps({'events':events,'count':len(events)}).encode()
        history.capture(fetch,base=root,now=NOW-timedelta(hours=1),per_league=1,date_plan=plan)

    def test_original_season_and_day_receipts_produce_research_agreement(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(td);out=check.build(td,now=NOW)
            self.assertEqual(out['two_source_final_agreements'],1)
            row=out['corroborated_research_only'][0]
            self.assertEqual(row['nba_game_id'],'0022400000')
            self.assertEqual(row['espn_receipts'][0]['source_date'],'2024-10-22')
            self.assertEqual(row['espn_source_observed_at_utc'],(NOW-timedelta(hours=1)).isoformat())
            self.assertEqual(row['corroboration_available_at_utc'],NOW.isoformat())
            self.assertFalse(out['training_allowed']);self.assertFalse(out['forecasting_enabled'])
            self.assertTrue(out['NO_BET']);self.assertEqual(out['actual_wagers'],0)

    def test_unsupported_teams_and_conflicting_scores_are_pending(self):
        for kwargs,reason in (({'code':'STARS'},'UNSUPPORTED_NBA_TEAM_CODES'),
                              ({'score':107},'CONFLICTING_FINAL_SCORES_NO_GRADE'),
                              ({'official':False},'NO_ARCHIVED_INDEPENDENT_NBA_SEASON')):
            with self.subTest(reason=reason),tempfile.TemporaryDirectory() as td:
                self.seed(td,**kwargs);out=check.build(td,now=NOW)
                self.assertEqual(out['two_source_final_agreements'],0)
                self.assertEqual(out['pending'][0]['reason'],reason)

    def test_per_game_time_cannot_borrow_a_later_unrelated_observation(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(td);out=check.build(td,now=NOW)
            r=out['corroborated_research_only'][0]
            official=owned.verify(td,'train',now=NOW)['parsed_nba_games']
            provider={'401234567':{'espn_game_id':'401234567','home_tricode':'NYK','away_tricode':'BOS',
                        'home_team_id':'18','away_team_id':'2','season_stage':2,'provider_completed':True,
                        'home_score':106,'away_score':104,'scheduled_start_utc':r['espn_scheduled_start_utc']}}
            report=finals.classify(official,provider,nba_observed_at=NOW.isoformat(),
                                  espn_observed_by_game={'401234567':r['espn_scheduled_start_utc']})
            self.assertEqual(report['pending'][0]['reason'],'FINAL_OBSERVED_AT_OR_BEFORE_SAVED_START')
            for times in ({},{'wrong':NOW.isoformat()}):
                with self.assertRaises(ValueError):
                    finals.classify(official,provider,nba_observed_at=NOW.isoformat(),espn_observed_by_game=times)
            with self.assertRaises(ValueError):
                finals.classify(official,provider,nba_observed_at=NOW.isoformat(),
                                espn_observed_at=NOW.isoformat(),espn_observed_by_game={'401234567':NOW.isoformat()})


if __name__=='__main__':unittest.main()
