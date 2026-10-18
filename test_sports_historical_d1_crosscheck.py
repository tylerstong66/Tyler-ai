"""D1 original sources join independently and never count duplicate labels."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
import json
import tempfile
import unittest

import sports_ncaa_d1_historical_owned as owned
import sports_expansion_historical_capture as history
import sports_historical_fbs_crosscheck as check
from test_sports_ncaa_espn_identity import official_game, espn_game

NOW=datetime(2026,10,18,tzinfo=timezone.utc)
START=datetime(2024,11,5,0,30,tzinfo=timezone.utc)


class HistoricalD1CrosscheckTests(unittest.TestCase):
    def seed(self,root,*,school='Duke',espn_school='Duke',conflict=False,days=1):
        game=official_game(when=int(START.timestamp()),home=school,away='Kansas',final=True)
        game['startDate']='11/04/2024'
        raw=json.dumps({'data':{'contests':[game]}}).encode()
        owned.capture(lambda _:raw,base=root,now=NOW,per_run=days)
        plan={sport:{split:[bounds[0]] for split,bounds in splits.items()}
              for sport,splits in history.SEASONS.items()}
        def fetch(url):
            events=[]
            if 'basketball/mens-college-basketball' in url:
                event=espn_game(start=START.isoformat(),home=espn_school,away='Kansas',completed=True)
                if conflict:
                    event['competitions'][0]['competitors'][0]['score']='31'
                events.append(event)
            return json.dumps({'count':len(events),'events':events}).encode()
        history.capture(fetch,base=root,now=NOW,per_league=1,date_plan=plan)

    def test_original_d1_archives_match_with_two_receipt_chains(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td));out=check.build(td,league='NCAAM_D1',now=NOW)
            self.assertEqual(out['schema'],'tyler-historical-d1-source-crosscheck-v1')
            self.assertEqual(out['two_source_final_agreements'],1)
            row=out['corroborated_research_only'][0]
            self.assertEqual(row['league'],'NCAAM_D1')
            self.assertEqual(row['ncaa_receipts'][0]['source_date'],'2024-11-04')
            self.assertFalse(out['training_allowed'])
            self.assertFalse(out['historical_evaluation_enabled'])

    def test_repeated_official_day_observations_never_double_count_game(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td),days=2);out=check.build(td,league='NCAAM_D1',now=NOW)
            self.assertEqual(out['ncaa_source_game_ids'],1)
            self.assertEqual(out['two_source_final_agreements'],1)
            self.assertEqual(len(out['corroborated_research_only'][0]['ncaa_receipts']),2)

    def test_tied_original_cannot_be_revived_by_another_day_valid_observation(self):
        with tempfile.TemporaryDirectory() as td:
            self.seed(Path(td))
            game=official_game(when=int(START.timestamp()),home='Duke',away='Kansas',final=True)
            game['startDate']='11/04/2024'
            for team in game['teams']:team['score']=0
            raw=json.dumps({'data':{'contests':[game]}}).encode()
            owned.capture(lambda _:raw,base=td,now=NOW,per_run=1)
            out=check.build(td,league='NCAAM_D1',now=NOW)
            self.assertEqual(out['two_source_final_agreements'],0)
            self.assertEqual(out['quarantined_ncaa_source_game_ids'],[str(game['contestId'])])
            q=out['quarantined_ncaa_source_observations'][0]
            self.assertEqual(q['reason'],'INVALID_TIED_NCAA_REPORTED_FINAL')
            self.assertEqual(q['source_receipt']['source_date'],'2024-11-05')
            self.assertFalse(q['eligible_for_result_agreement'])
            self.assertFalse(out['training_allowed'])

    def test_unknown_alias_and_conflicting_scores_remain_excluded(self):
        for kwargs,reason in (({'school':'Penn St.','espn_school':'Penn State'},'NO_UNAMBIGUOUS_NCAA_GAME_ID'),
                              ({'conflict':True},'CONFLICTING_FINAL_SCORES_NO_GRADE')):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as td:
                self.seed(Path(td),**kwargs);out=check.build(td,league='NCAAM_D1',now=NOW)
                self.assertEqual(out['two_source_final_agreements'],0)
                self.assertEqual(out['pending'][0]['reason'],reason)


if __name__=='__main__':
    unittest.main()
