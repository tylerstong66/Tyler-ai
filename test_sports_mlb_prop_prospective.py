"""Immutable game-ID / player-ID prospective forecast and official final settlement tests."""
import copy
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from sports_mlb_prop_prospective import (
    freeze_pregame_hit_props, settle_frozen_hit_props, write_exclusive_json, _verify, _seal
)

START="2026-10-15T23:00:00Z"
BEFORE=datetime.fromisoformat("2026-10-15T19:15:00+00:00")
AFTER=datetime.fromisoformat("2026-10-16T03:00:00+00:00")


class OfficialReader:
    def __init__(self):
        self.now=BEFORE
        self.audit=[]
        self.final=False
        self.at_bats=4
        self.exists=True
        self.bad_identity=False
        self.omit_at_bats=False
        self.omit_batting_fields=()
        self.null_batting=False
        self.days=40

    def clock(self):
        return self.now

    def load(self,path,params=None,api_version="v1"):
        if path=="game/849810/feed/live":
            if api_version!="v1.1":
                raise AssertionError("Should request official v1.1 MLB game feed.")
            data={"gamePk":849810,"gameData":{
                "datetime":{"dateTime":START},
                "status":{"abstractGameState":"Final" if self.final else "Preview",
                          "detailedState":"Final" if self.final else "Scheduled"},
                "teams":{"home":{"id":119},"away":{"id":158}}}}
            if self.final:
                player={"person":{"id":683734 if not self.bad_identity else 987},
                        "stats":{"batting":{"atBats":self.at_bats,
                                            "hits":1 if self.at_bats else 0,"homeRuns":0}}}
                if self.omit_at_bats:
                    player["stats"]["batting"].pop("atBats")
                for missing in self.omit_batting_fields:
                    player["stats"]["batting"].pop(missing)
                if self.null_batting:
                    player["stats"]["batting"]=None
                data["liveData"]={"boxscore":{"teams":{"away":{"players":{
                    "ID683734":player} if self.exists else {}}}}}
        elif path=="teams/158/roster":
            data={"roster":[{"person":{"id":683734,"fullName":"Synthetic Hitter"},
                              "position":{"abbreviation":"1B"}}]}
        elif path=="people/683734/stats":
            season=params["season"]
            beginning=date(season,6,1)
            splits=[]
            for i in range(self.days):
                day=(beginning+timedelta(days=i)).isoformat()
                splits.append({"date":day,"season":str(season),"gameType":"R",
                               "game":{"gamePk":season*100000+i},
                               "player":{"id":683734},
                               "team":{"id":158},
                               "stat":{"atBats":4,"plateAppearances":4,
                                       "hits":1 if (i%2 or i%13==1) else 0,"homeRuns":1 if i%13==1 else 0}})
            data={"stats":[{"type":{"displayName":"gameLog"},
                            "group":{"displayName":"hitting"},"splits":splits}]}
        else:
            raise AssertionError("Unexpected network request "+path)
        audit={"source_url":"https://statsapi.mlb.com/api/v1/"+path,
               "retrieved_at":self.now.isoformat(),
               "data_through":self.now.isoformat(),
               "response_sha256":"synthetic"}
        self.audit.append(audit)
        return copy.deepcopy(data),audit


class FrozenTrialTests(unittest.TestCase):
    def test_resealed_noninteger_zero_wager_rejected_before_final_fetch(self):
        for value in (False, 0.0, -0.0):
            with self.subTest(value=value):
                reader = OfficialReader()
                record = freeze_pregame_hit_props(849810, 683734, 'away', reader=reader)
                core = _verify(record); core['actual_wager'] = value
                forged = _seal(core); before = copy.deepcopy(forged)
                reader.now = AFTER; reader.final = True; reader.audit.clear()
                with self.assertRaisesRegex(ValueError, 'no-bet'):
                    settle_frozen_hit_props(forged, reader=reader)
                self.assertEqual(reader.audit, [])
                self.assertEqual(forged, before)

    def test_frozen_pregame_content_and_final_are_separate_records(self):
        r=OfficialReader()
        original=freeze_pregame_hit_props(849810,683734,"away",reader=r)
        _verify(original)
        self.assertLess(original["frozen_at_utc"],original["event_start_utc"])
        self.assertEqual(original["model_calibrated"],False)
        self.assertEqual(original["sportsbook_wager_eligible"],False)
        self.assertEqual(original["actual_wager"],0)
        self.assertEqual(original["condition"],"at_least_one_official_at_bat")
        self.assertEqual(len(original["source_receipts"]["hitter_game_logs"]),2)
        self.assertTrue(0<original["conditional_at_bat_probabilities"]["hit"]<1)

        before=copy.deepcopy(original)
        r.final=True;r.now=AFTER
        settled=settle_frozen_hit_props(original,reader=r)
        self.assertEqual(original,before)
        self.assertEqual(settled["prediction_digest_sha256"],original["record_digest_sha256"])
        self.assertEqual(settled["status"],"SETTLED_CONDITIONAL")
        self.assertEqual(settled["conditional_binary_scoring"]["hit"]["observed_binary_event"],1)
        self.assertIsNone(settled["sportsbook_settlement"])
        self.assertEqual(settled["actual_wager"],0)
        _verify(settled)

    def test_freeze_requires_strict_pregame_verified_roster_and_history(self):
        r=OfficialReader();r.now=AFTER
        with self.assertRaisesRegex(ValueError,"first pitch"):
            freeze_pregame_hit_props(849810,683734,"away",reader=r)
        r=OfficialReader();r.days=12
        with self.assertRaisesRegex(ValueError,"Insufficient"):
            freeze_pregame_hit_props(849810,683734,"away",reader=r)
        r=OfficialReader()
        with self.assertRaisesRegex(ValueError,"active non-pitcher"):
            freeze_pregame_hit_props(849810,99999,"away",reader=r)

    def test_prediction_tampering_detected_even_if_probability_changed(self):
        r=OfficialReader()
        record=freeze_pregame_hit_props(849810,683734,"away",reader=r)
        record["conditional_at_bat_probabilities"]["hit"]=0.999
        with self.assertRaisesRegex(ValueError,"digest mismatch"):
            settle_frozen_hit_props(record,reader=r)

    def test_final_or_failed_identity_rejected(self):
        r=OfficialReader();record=freeze_pregame_hit_props(849810,683734,"away",reader=r)
        with self.assertRaisesRegex(ValueError,"before the scheduled first pitch"):
            settle_frozen_hit_props(record,reader=r)
        r.now=AFTER
        with self.assertRaisesRegex(ValueError,"final"):
            settle_frozen_hit_props(record,reader=r)
        r.final=True;r.bad_identity=True
        with self.assertRaisesRegex(ValueError,"identity"):
            settle_frozen_hit_props(record,reader=r)

    def test_zero_at_bats_or_missing_boxscore_does_not_count_as_loss(self):
        r=OfficialReader();record=freeze_pregame_hit_props(849810,683734,"away",reader=r)
        r.now=AFTER;r.final=True;r.at_bats=0
        outcome=settle_frozen_hit_props(record,reader=r)
        self.assertEqual(outcome["status"],"INELIGIBLE_ZERO_AB")
        self.assertIsNone(outcome["conditional_binary_scoring"])
        r.exists=False
        absent=settle_frozen_hit_props(record,reader=r)
        self.assertEqual(absent["status"],"INELIGIBLE_NOT_IN_FINAL_BOXSCORE")
        self.assertIsNone(absent["conditional_binary_scoring"])

    def test_immutable_exclusive_file_create_and_verified_digest(self):
        record=freeze_pregame_hit_props(849810,683734,"away",reader=OfficialReader())
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"predictions"/"849810_683734.json"
            write_exclusive_json(path,record)
            self.assertEqual(json.loads(path.read_text())["record_digest_sha256"],
                             record["record_digest_sha256"])
            with self.assertRaises(FileExistsError):
                write_exclusive_json(path,record)
            self.assertEqual(json.loads(path.read_text()),record)


if __name__=="__main__":
    unittest.main()
