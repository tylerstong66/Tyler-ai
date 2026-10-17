"""Cross-provider NBA schedule checks, including missing, drifted and ambiguous IDs."""
import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import datetime,timezone
from pathlib import Path

import sports_expansion_observer as observer
import sports_nba_official_schedule_audit as nba

START="2026-10-20T19:00:00+00:00"

def official_games(times=("2026-10-20T19:00:00Z",)):
    result=[]
    for i,time in enumerate(times):
        result.append({
            "gameId":f"00226000{i:03d}",
            "gameDateTimeUTC":time,"gameStatus":1,
            "homeTeam":{"teamTricode":"NYK","score":None},
            "awayTeam":{"teamTricode":"BOS","score":None},
        })
    # Whole-season shape is required. Dummy other games must be unique IDs.
    for i in range(125):
        result.append({
            "gameId":f"0022700{i:04d}",
            "gameDateTimeUTC":"2026-11-02T19:00:00Z",
            "gameStatus":1,
            "homeTeam":{"teamTricode":"LAL","score":None},
            "awayTeam":{"teamTricode":"GSW","score":None},
        })
    return json.dumps({"leagueSchedule":{"gameDates":[
        {"gameDate":f"2026-10-{(i%30)+1:02d}","games":
         result if i==0 else []} for i in range(60)]}}).encode()


def espn_event():
    return {
        "id":"401234567","date":"2026-10-20T19:00:00Z",
        "season":{"type":2},
        "status":{"type":{"state":"pre","completed":False}},
        "competitions":[{"neutralSite":False,"competitors":[
            {"homeAway":"home","team":{"id":"18","displayName":"New York Knicks","abbreviation":"NY"}},
            {"homeAway":"away","team":{"id":"2","displayName":"Boston Celtics","abbreviation":"BOS"}}]}],
    }


class NbaOfficialCorroborationTests(unittest.TestCase):
    def espn_root(self,path):
        def fetch(url):
            data={"events":[],"count":0}
            if "basketball/nba" in url and "dates=20261020" in url:
                data={"events":[espn_event()],"count":1}
            return json.dumps(data).encode()
        observer.capture(fetch,base=path,
                         now=datetime(2026,10,17,12,tzinfo=timezone.utc),
                         days_ahead=3)

    def test_team_alias_and_exact_game_scheduled_identity(self):
        data=nba.official_games(official_games())
        self.assertGreater(len(data),100)
        self.assertEqual(data[0]["home_tricode"],"NYK")
        self.assertEqual(data[0]["nba_game_id"],"0022600000")
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.espn_root(root)
            saved=nba.run(lambda _:official_games(),base=root,
                          now=datetime(2026,10,17,13,tzinfo=timezone.utc))
            comp=saved["report"]
            self.assertEqual(comp["espn_observed_games"],1)
            self.assertEqual(comp["strict_schedule_correlated"],1)
            self.assertEqual(comp["matched"][0]["nba_official_game_id"],"0022600000")
            self.assertEqual(comp["matched"][0]["start_offset_minutes"],0)
            self.assertFalse(comp["official_final_scoring_enabled"])
            self.assertFalse(comp["forecasting_enabled"])
            self.assertTrue(comp["NO_BET"])
            self.assertEqual(saved["actual_wagers"],0)
            stored=(root/nba.ROOT/"captures"/"20261017T130000000000Z")
            self.assertEqual(hashlib.sha256(gzip.decompress(
                (stored/"nba_schedule.json.gz").read_bytes())).hexdigest(),
                saved["nba_raw_sha256"])
            self.assertEqual(json.loads((stored/"manifest.json").read_text()),saved)
            with self.assertRaisesRegex(ValueError,"collision"):
                nba.run(lambda _:official_games(),base=root,
                        now=datetime(2026,10,17,13,tzinfo=timezone.utc))

    def test_conflicting_start_and_missing_or_multiple_official_games_fail_closed(self):
        saved={"espn_game_id":"401234567","home_tricode":"NYK",
               "away_tricode":"BOS","scheduled_start_utc":START,
               "provider_completed":False}
        def compare(times):
            return nba.compare(nba.official_games(official_games(times)),
                               {"401234567":saved})
        delayed=compare(("2026-10-20T20:00:00Z",))
        self.assertEqual(delayed["strict_schedule_correlated"],0)
        self.assertEqual(delayed["unverified"][0]["reason"],
                         "SOURCE_KICKOFF_DISAGREEMENT")
        absent=compare(("2026-10-25T20:00:00Z",))
        self.assertEqual(absent["unverified"][0]["reason"],
                         "NO_INDEPENDENT_NBA_GAME_FOUND")
        duplicates=compare(("2026-10-20T19:00:00Z",
                            "2026-10-20T19:10:00Z"))
        self.assertEqual(duplicates["unverified"][0]["reason"],
                         "AMBIGUOUS_NBA_IDENTITY")

    def test_unknown_games_and_invalid_finals_are_excluded_or_rejected(self):
        raw=official_games()
        obj=json.loads(raw)
        obj["leagueSchedule"]["gameDates"][0]["games"][0]["gameId"]="0012600000"
        valid=nba.official_games(json.dumps(obj).encode())
        self.assertTrue(all(x["nba_game_id"]!="0012600000" for x in valid))
        obj=json.loads(raw)
        obj["leagueSchedule"]["gameDates"][0]["games"][0]["gameStatus"]=3
        obj["leagueSchedule"]["gameDates"][0]["games"][0]["homeTeam"]["score"]=106
        obj["leagueSchedule"]["gameDates"][0]["games"][0]["awayTeam"]["score"]=104
        games=nba.official_games(json.dumps(obj).encode())
        self.assertEqual(games[0]["nba_home_score"],106)
        obj["leagueSchedule"]["gameDates"][0]["games"][0]["awayTeam"]["score"]=106
        with self.assertRaisesRegex(ValueError,"tied"):
            nba.official_games(json.dumps(obj).encode())
        obj["leagueSchedule"]["gameDates"][0]["games"][0]["awayTeam"]["score"]="DNP"
        with self.assertRaisesRegex(ValueError,"Malformed"):
            nba.official_games(json.dumps(obj).encode())

    def test_capture_and_fetch_failures_leave_original_archive_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.espn_root(root)
            before=list((root/observer.ROOT/"captures").glob("*"))
            with self.assertRaisesRegex(ValueError,"oversized"):
                nba.run(lambda _:b"x"*(nba.MAX_BYTES+1),base=root)
            self.assertEqual(before,list((root/observer.ROOT/"captures").glob("*")))
            with self.assertRaises(json.JSONDecodeError):
                nba.run(lambda _:b"not json",base=root)
            self.assertFalse((root/nba.ROOT).exists())

    def test_espn_raw_source_identity_must_be_unambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.espn_root(root)
            capture=next((root/observer.ROOT/"captures").glob("*"))
            target=capture/"NBA_2026-10-20.json.gz"
            raw=json.loads(gzip.decompress(target.read_bytes()))
            raw["events"][0]["competitions"][0]["competitors"][0]["team"]["abbreviation"]="BOS"
            raw["events"][0]["competitions"][0]["competitors"][1]["team"]["abbreviation"]="NYK"
            target.write_bytes(gzip.compress(json.dumps(raw).encode()))
            with self.assertRaisesRegex(ValueError,"hash disagrees"):
                nba.run(lambda _:official_games(),base=root)

if __name__=="__main__":
    unittest.main()
