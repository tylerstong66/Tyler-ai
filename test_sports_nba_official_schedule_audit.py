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
            "gameId":f"0022600{i:03d}",
            "gameDateTimeUTC":time,"gameStatus":1,
            "homeTeam":{"teamTricode":"NYK","score":None},
            "awayTeam":{"teamTricode":"BOS","score":None},
        })
    # Whole-season shape is required. Dummy other games must be unique IDs.
    for i in range(125):
        result.append({
            "gameId":f"002270{i:04d}",
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
    def test_direct_provider_replay_rejects_unbound_archive_filename(self):
        for kind in ('absolute', 'traversal', 'other_day'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                root = Path(td); self.espn_root(root)
                folder = next((root/observer.ROOT/'captures').iterdir())
                manifest = json.loads((folder/'manifest.json').read_bytes())
                snap = next(s for s in manifest['snapshots'] if s['league'] == 'NBA' and s['day'] == '2026-10-20')
                original = folder/snap['compressed_file']
                if kind == 'other_day':
                    target = folder/'NBA_2026-10-21.json.gz'; declared = target.name
                else:
                    target = folder.parent/'outside.json.gz'
                    declared = str(target) if kind == 'absolute' else '../outside.json.gz'
                target.write_bytes(original.read_bytes()); snap['compressed_file'] = declared
                with self.assertRaisesRegex(ValueError, 'filename'): nba.espn_games(manifest, folder)

    def test_direct_provider_replay_rejects_noncanonical_calendar_day(self):
        for day in ('2026-1-01', '2026-02-30', '../2026-10-20', None):
            with self.subTest(day=day), tempfile.TemporaryDirectory() as td:
                root = Path(td); self.espn_root(root)
                folder = next((root/observer.ROOT/'captures').iterdir())
                manifest = json.loads((folder/'manifest.json').read_bytes())
                snap = next(s for s in manifest['snapshots'] if s['league'] == 'NBA')
                snap['day'] = day
                with self.assertRaises(ValueError): nba.espn_games(manifest, folder)

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

    def test_nba_owned_final_scores_reject_unicode_and_noninteger_values(self):
        for bad in ("١٠٦", "１０６", "10٦", "²", 106.0, True, -1):
            with self.subTest(score=bad):
                obj = json.loads(official_games())
                game = obj["leagueSchedule"]["gameDates"][0]["games"][0]
                game["gameStatus"] = 3
                game["homeTeam"]["score"] = bad
                game["awayTeam"]["score"] = 104
                with self.assertRaisesRegex(ValueError, "Malformed NBA official final score"):
                    nba.official_games(json.dumps(obj, ensure_ascii=False).encode())
        obj = json.loads(official_games())
        game = obj["leagueSchedule"]["gameDates"][0]["games"][0]
        game["gameStatus"] = 3
        game["homeTeam"]["score"] = "106"
        game["awayTeam"]["score"] = 104
        self.assertEqual(nba.official_games(json.dumps(obj).encode())[0]["nba_home_score"], 106)

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

    def test_official_schedule_rejects_ambiguous_raw_json_before_archival(self):
        valid=official_games()
        for name,raw in (
                ("duplicate", b'{"leagueSchedule":{"gameDates":[]},'+valid[1:]),
                ("nonfinite", b'{"unknown":NaN,'+valid[1:])):
            with self.subTest(name=name), self.assertRaises(ValueError):
                nba.official_games(raw)
            with self.subTest(name=name),tempfile.TemporaryDirectory() as td:
                root=Path(td); self.espn_root(root)
                with self.assertRaises(ValueError):
                    nba.run(lambda _:raw,base=root,
                            now=datetime(2026,10,17,13,tzinfo=timezone.utc))
                self.assertFalse((root/nba.ROOT).exists())

    def test_duplicate_espn_raw_json_fails_even_with_matching_new_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self.espn_root(root)
            capture=next((root/observer.ROOT/'captures').iterdir())
            manifest=json.loads((capture/'manifest.json').read_text())
            snap=next(s for s in manifest['snapshots'] if s['league']=='NBA'
                      and s['day']=='2026-10-20')
            blob=capture/snap['compressed_file']
            original=gzip.decompress(blob.read_bytes())
            altered=b'{"count":0,'+original[1:]
            blob.write_bytes(gzip.compress(altered,mtime=0))
            snap['original_response_sha256']=hashlib.sha256(altered).hexdigest()
            with self.assertRaisesRegex(ValueError,'Duplicate'):
                nba.espn_games(manifest,capture)

    def test_nba_crosswalk_requires_replay_of_linked_espn_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self.espn_root(root)
            capture=next((root/observer.ROOT/'captures').iterdir())
            manifest=capture/'manifest.json'
            original=manifest.read_bytes()
            manifest.write_bytes(b'{"NO_BET":false,'+original[1:])
            with self.assertRaisesRegex(ValueError,'Duplicate'):
                nba.run(lambda _:official_games(),base=root,
                        now=datetime(2026,10,17,13,tzinfo=timezone.utc))
            self.assertFalse((root/nba.ROOT).exists())

    def test_oversized_espn_archive_fails_closed_before_nba_crosswalk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.espn_root(root)
            capture=next((root/observer.ROOT/'captures').glob('*'))
            target=capture/'NBA_2026-10-20.json.gz'
            target.write_bytes(gzip.compress(b'x' * 8_000_001,mtime=0))
            with self.assertRaisesRegex(ValueError,'exceeds maximum'):
                nba.run(lambda _:official_games(),base=root)
            self.assertFalse((root/nba.ROOT).exists())

    def test_truncated_espn_archive_fails_closed_before_nba_crosswalk(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.espn_root(root)
            capture=next((root/observer.ROOT/'captures').glob('*'))
            target=capture/'NBA_2026-10-20.json.gz'
            target.write_bytes(target.read_bytes()[:-6])
            with self.assertRaisesRegex(ValueError,'Corrupt or incomplete'):
                nba.run(lambda _:official_games(),base=root)
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
            with self.assertRaisesRegex(ValueError,"archived response SHA256|hash disagrees"):
                nba.run(lambda _:official_games(),base=root)

if __name__=="__main__":
    unittest.main()
