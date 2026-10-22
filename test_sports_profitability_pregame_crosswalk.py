"""Synthetic-only frozen pregame schedule source crosswalk integrity tests."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import sports_profitability_pregame_crosswalk as crosswalk
import sports_profitability_v1 as profit


class OriginalNhlEspnCrosswalkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game_id = "2026020999"
        self.kickoff = "2026-10-24T19:00:00Z"
        self.official_game = {
            "id": 2026020999, "gameType": 2, "gameState": "FUT",
            "gameScheduleState": "OK", "startTimeUTC": self.kickoff,
            "neutralSite": False,
            "homeTeam": {"id": 22, "abbrev": "PHI"},
            "awayTeam": {"id": 6, "abbrev": "BOS"},
        }
        self.espn_event = {
            "id": "401899999", "date": self.kickoff,
            "status": {"type": {"state": "pre", "completed": False}},
            "competitions": [{
                "neutralSite": False,
                "competitors": [
                    {"homeAway": "home", "team": {
                        "abbreviation": "PHI",
                        "displayName": "Philadelphia Flyers"}},
                    {"homeAway": "away", "team": {
                        "abbreviation": "BOS",
                        "displayName": "Boston Bruins"}},
                ]}],
        }
        self.nhl = {"gameWeek": [{"date": "2026-10-24",
                                  "games": [self.official_game]}]}
        self.espn = {"events": [self.espn_event]}
        self.official_source, self.espn_source = self.save_sources()
        self.at = "2026-10-23T18:02:00Z"

    def save_one(self, path, document, url, retrieved):
        raw = json.dumps(document, sort_keys=True).encode()
        (self.root / path).write_bytes(raw)
        return {
            "path": path,
            "source_url": url,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "retrieved_at": retrieved,
        }

    def save_sources(self):
        official = self.save_one(
            "official.json", self.nhl,
            crosswalk.NHL_SCHEDULE + "2026-10-24", "2026-10-23T18:00:00Z")
        espn = self.save_one(
            "espn.json", self.espn,
            crosswalk.ESPN_SCOREBOARD + "20261024", "2026-10-23T18:01:00Z")
        return official, espn

    def read(self, sources=None):
        return crosswalk.read_pregame_crosswalk(
            self.root, *(sources or self.save_sources()), self.game_id, self.at)

    def test_byte_verified_independent_identity_is_unqualified(self):
        result = self.read()
        self.assertEqual(result["game_id"], self.game_id)
        self.assertEqual(result["event_id"], "401899999")
        self.assertEqual(result["home"], "PHI")
        self.assertEqual(result["away"], "BOS")
        self.assertEqual(result["home_id"], "22")
        self.assertEqual(result["away_name"], "Boston Bruins")
        self.assertEqual(result["kickoff"], "2026-10-24T19:00:00+00:00")
        profit.verify_record(result)
        self.assertIs(result["qualified_for_paper_roi"], False)
        self.assertIs(result["publication_server_attested"], False)
        self.assertEqual(result["actual_wagers"], 0)

    def test_missing_original_response_or_bytes_tamper_refused(self):
        sources = self.save_sources()
        (self.root / sources[0]["path"]).write_text('{"changed":"after archive"}')
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.read(sources)
        (self.root / sources[1]["path"]).unlink()
        with self.assertRaises(ValueError):
            self.read(sources)

    def test_espn_teams_or_original_start_disagreement_is_not_crosswalked(self):
        for mode in ("team", "start", "not_completed", "duplicate"):
            with self.subTest(mode=mode):
                self.espn = {"events": [copy.deepcopy(self.espn_event)]}
                e = self.espn["events"][0]
                if mode == "team":
                    e["competitions"][0]["competitors"][0]["team"]["abbreviation"] = "TOR"
                if mode == "start":
                    e["date"] = "2026-10-24T19:01:00Z"
                if mode == "not_completed":
                    e["status"]["type"] = {"state": "post", "completed": True}
                if mode == "duplicate":
                    self.espn["events"].append(copy.deepcopy(e))
                with self.assertRaisesRegex(ValueError, "Unique exact pre-event"):
                    self.read()

    def test_official_status_and_team_ids_must_be_normal(self):
        for mode in ("started", "preseason", "cancelled", "same_id"):
            with self.subTest(mode=mode):
                self.nhl = {"gameWeek": [{"games": [copy.deepcopy(self.official_game)]}]}
                g = self.nhl["gameWeek"][0]["games"][0]
                if mode == "started":
                    g["gameState"] = "LIVE"
                elif mode == "preseason":
                    g["gameType"] = 1
                elif mode == "cancelled":
                    g["gameScheduleState"] = "CNCL"
                else:
                    g["awayTeam"]["id"] = g["homeTeam"]["id"]
                with self.assertRaises(ValueError):
                    self.read()

    def test_conflicting_venue_neutrality_quarantined(self):
        self.espn = {"events": [copy.deepcopy(self.espn_event)]}
        self.espn["events"][0]["competitions"][0]["neutralSite"] = True
        with self.assertRaisesRegex(ValueError, "venue neutrality"):
            self.read()

    def test_both_raw_sources_must_precede_original_start_and_follow_activation(self):
        sources = list(self.save_sources())
        for timestamp in ("2026-10-22T20:00:00Z", "2026-10-25T01:00:00Z"):
            with self.subTest(timestamp=timestamp):
                wrong = copy.deepcopy(sources)
                wrong[1]["retrieved_at"] = timestamp
                with self.assertRaisesRegex(ValueError, "pre-kickoff"):
                    self.read(wrong)

    def test_wrong_source_date_path_rejected(self):
        sources = list(self.save_sources())
        for index in (0, 1):
            with self.subTest(index=index):
                wrong = copy.deepcopy(sources)
                wrong[index]["source_url"] += "1"
                with self.assertRaisesRegex(ValueError, "source URL"):
                    self.read(wrong)

    def test_original_source_duplicate_game_id_rejected(self):
        self.nhl["gameWeek"][0]["games"].append(copy.deepcopy(self.official_game))
        with self.assertRaisesRegex(ValueError, "Exactly one official"):
            self.read()

    def test_different_espn_event_same_time_does_not_override_matchup(self):
        unrelated = copy.deepcopy(self.espn_event)
        unrelated["id"] = "unrelated"
        unrelated["competitions"][0]["competitors"][0]["team"]["abbreviation"] = "NYR"
        self.espn["events"].append(unrelated)
        result = self.read()
        self.assertEqual(result["event_id"], "401899999")


if __name__ == "__main__":
    unittest.main()
