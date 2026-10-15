"""Offline MLB shadow batch capture regression."""
import tempfile,copy,unittest,json
from pathlib import Path
from datetime import datetime,date,timedelta
from sports_mlb_prop_batch_capture import capture_current_day,ensure_publishable_before_events
from test_sports_mlb_prop_prospective import OfficialReader, START

class Stub(OfficialReader):
    def __init__(self):
        super().__init__()
        self.dupe=False
    def load(self,path,params=None,api_version="v1"):
        if path=="schedule":
            item={"gamePk":849810,"gameDate":START,
                  "status":{"abstractGameState":"Preview","detailedState":"Scheduled"}}
            items=[item,copy.deepcopy(item)] if self.dupe else [item]
            data={"dates":[{"games":items}]}
        elif path=="teams/119/roster":
            data={"roster":[{"person":{"id":700001,"fullName":"Home Hitter"},
                             "position":{"abbreviation":"1B"}}]}
        elif path=="people/700001/stats":
            year=params["season"]
            rows=[{"date":(date(year,6,1)+timedelta(days=i)).isoformat(),
                   "season":str(year),"gameType":"R","game":{"gamePk":year*100000+i},
                   "player":{"id":700001},"team":{"id":119},
                   "stat":{"atBats":4,"hits":i%2,"homeRuns":0,"plateAppearances":4}}
                  for i in range(40)]
            data={"stats":[{"type":{"displayName":"gameLog"},
                           "group":{"displayName":"hitting"},"splits":rows}]}
        else:
            return super().load(path,params,api_version)
        receipt={"source_url":"https://statsapi.mlb.com/api/v1/"+path,
                 "retrieved_at":self.now.isoformat()}
        self.audit.append(receipt)
        return copy.deepcopy(data),receipt

class Tests(unittest.TestCase):
    def test_fixed_roster_prediction_and_no_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            r=Stub()
            result=capture_current_day(reader=r,root=d,per_side=1)
            self.assertEqual(result["new_frozen_predictions"],2)
            self.assertEqual(result["wagers"],0)
            self.assertTrue(ensure_publishable_before_events(
                result["records"],now="2026-10-15T19:00:00Z"))
            a={p.name:p.read_text() for p in (Path(d)/"predictions").glob("*.json")}
            retry=capture_current_day(reader=r,root=d,per_side=1)
            self.assertEqual(retry["new_frozen_predictions"],0)
            self.assertEqual(retry["already_existing_predictions"],2)
            b={p.name:p.read_text() for p in (Path(d)/"predictions").glob("*.json")}
            self.assertEqual(a,b)
    def test_close_to_first_pitch_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            r=Stub();r.now=datetime.fromisoformat("2026-10-15T22:30:00+00:00")
            report=capture_current_day(reader=r,root=d,per_side=1)
            self.assertEqual(report["new_frozen_predictions"],0)
            self.assertEqual(report["skipped"][0]["reason"],"under_45_minutes_until_first_pitch")
    def test_duplicate_game_and_invalid_configuration_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=Stub();r.dupe=True
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                capture_current_day(reader=r,root=d)
        for n in (0,5,True):
            with tempfile.TemporaryDirectory() as d,self.assertRaises(ValueError):
                capture_current_day(reader=Stub(),root=d,per_side=n)
    def test_reject_publish_if_too_near_game(self):
        with tempfile.TemporaryDirectory() as d:
            r=Stub()
            report=capture_current_day(reader=r,root=d,per_side=1)
            with self.assertRaisesRegex(ValueError,"Too close"):
                ensure_publishable_before_events(report["records"],
                    now="2026-10-15T22:59:00Z")

if __name__=="__main__":
    unittest.main()
