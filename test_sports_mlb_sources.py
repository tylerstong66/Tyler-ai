"""Offline, mock-only tests for official MLB pregame research collection."""
import copy
import json
import unittest
from datetime import datetime, timezone

from sports_mlb_sources import OfficialMlbReader, official_counts, pregame_research

START = "2026-10-15T23:00:00Z"
NOW = datetime.fromisoformat("2026-10-15T17:00:00+00:00")


def fixture():
    return {
        "game/849831/feed/live": {
            "gamePk": 849831,
            "gameData": {
                "game": {"type": "L"},
                "datetime": {"dateTime": START},
                "status": {"abstractGameState": "Preview", "detailedState": "Scheduled"},
                "teams": {"home": {"id": 119}, "away": {"id": 158}},
                "probablePitchers": {"home": {"id": 20001, "fullName": "Starter"}}}},
        "teams/158/roster": {"roster": [{"person": {"id": 10001, "fullName": "Synthetic Hitter"},
                                      "position": {"abbreviation": "RF"}}]},
        "teams/119/roster": {"roster": [
            {"person": {"id": 20001, "fullName": "Synthetic Starter"}, "position": {"abbreviation": "P"}},
            {"person": {"id": 30001, "fullName": "Synthetic Reliever"}, "position": {"abbreviation": "P"}}]},
    }


def stats(pa=12, ab=11, hits=4, hr=1, year=2025):
    item = {"plateAppearances": pa, "atBats": ab, "hits": hits, "homeRuns": hr}
    return {"stats": [
        {"type": {"displayName": "vsPlayerTotal"}, "group": {"displayName": "hitting"},
         "splits": [{"stat": {"plateAppearances": 999, "atBats": 999,
                               "hits": 999, "homeRuns": 999}}]},
        {"type": {"displayName": "vsPlayer"}, "group": {"displayName": "hitting"},
         "splits": [
             {"season": str(year), "gameType": "R", "team": {"id": 158},
              "opponent": {"id": 119}, "stat": item},
             {"season": "2018", "gameType": "W", "team": {"id": 111},
              "opponent": {"id": 147}, "stat": {"plateAppearances": 100,
                  "atBats": 100, "hits": 100, "homeRuns": 100}}]}]}



class Reader:
    def __init__(self):
        self.calls = []
        self.audit = []
        self.rows = fixture()
        self.now = NOW

    def clock(self):
        return self.now

    def load(self, path, params=None, api_version="v1"):
        self.calls.append((path, params))
        if "/stats" in path:
            if params["opposingPlayerId"] == 30001:
                data = {"stats": []}  # Do NOT fabricate missing BvP samples
            else:
                data = stats(year=2025) if params["season"] == 2025 else stats(6, 5, 2, 0, year=2026)
        else:
            data = self.rows[path]
        url = "https://statsapi.mlb.com/api/" + api_version + "/" + path
        e = {"source_url": url, "retrieved_at": self.now.isoformat(),
             "data_through": self.now.isoformat(), "response_sha256": "testhash"}
        self.audit.append(e)
        return copy.deepcopy(data), e


class OfficialStatsTests(unittest.TestCase):
    def test_season_and_game_type_are_filtered_even_when_server_ignores_params(self):
        d = stats()
        self.assertEqual(official_counts(d, 2025)["hits"], 4)
        self.assertIsNone(official_counts(d, 2026))
        self.assertIsNone(official_counts(d, 2025, "W"))
        self.assertEqual(official_counts(d, 2018, "W")["hits"], 100)

    def test_no_stat_duplicate_and_invalid_totals_fail_closed(self):
        self.assertIsNone(official_counts({"stats": []}, 2025))
        d = stats()
        d["stats"][1]["splits"].append(copy.deepcopy(d["stats"][1]["splits"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            official_counts(d, 2025)
        d = stats(); del d["stats"][1]["splits"][0]["stat"]["plateAppearances"]
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            official_counts(d, 2025)
        with self.assertRaisesRegex(ValueError, "Inconsistent"):
            official_counts(stats(pa=2, ab=2, hits=3, hr=1), 2025)



class PregameTests(unittest.TestCase):
    def test_sourced_live_pregame_identity_and_two_seasons(self):
        reader = Reader()
        out = pregame_research(849831, 10001, "away", [30001], reader=reader)
        self.assertEqual(out["decision"], "RESEARCH ONLY - NO BET")
        self.assertEqual(out["starter_matchup"]["plate_appearances"], 18)
        self.assertEqual(out["starter_matchup"]["hits"], 6)
        self.assertEqual(out["coverage"], {"expected_pitchers": 2, "pitchers_with_sourced_stats": 1})
        self.assertIsNone(out["reliever_matchups"][0]["historical_batting_average"])
        self.assertEqual(out["reliever_matchups"][0]["pitcher"]["availability"], "unknown")
        self.assertEqual(len(reader.audit), 7)  # game, two rosters, four stat calls
        self.assertEqual(out["official_data"]["historical_seasons"], [2025, 2026])
        self.assertIsNone(out["estimated_home_run_probability"])
        self.assertTrue(out["official_data"]["rosters_are_active_not_confirmed_lineups"])

    def test_utc_midnight_uses_eastern_roster_date(self):
        reader = Reader()
        reader.rows["game/849831/feed/live"]["gameData"]["datetime"]["dateTime"] = "2026-10-16T00:30:00Z"
        pregame_research(849831, 10001, "away", reader=reader)
        roster_calls = [params for path, params in reader.calls if "/roster" in path]
        self.assertEqual([p["date"] for p in roster_calls], ["2026-10-15", "2026-10-15"])

    def test_missing_official_probable_pitcher_fails_closed(self):
        r = Reader()
        del r.rows["game/849831/feed/live"]["gameData"]["probablePitchers"]["home"]
        with self.assertRaisesRegex(ValueError, "probable"):
            pregame_research(849831, 10001, "away", reader=r)

    def test_status_and_started_game_refused(self):
        for status in ("Live", "Final"):
            with self.subTest(status=status):
                r = Reader()
                r.rows["game/849831/feed/live"]["gameData"]["status"]["abstractGameState"] = status
                with self.assertRaisesRegex(ValueError, "pregame"):
                    pregame_research(849831, 10001, "away", reader=r)
        r = Reader()
        r.now = datetime.fromisoformat("2026-10-16T00:00:00+00:00")
        with self.assertRaisesRegex(ValueError, "started"):
            pregame_research(849831, 10001, "away", reader=r)

    def test_wrong_rosters_and_roles_refused(self):
        r = Reader()
        with self.assertRaisesRegex(ValueError, "Hitter"):
            pregame_research(849831, 99999, "away", reader=r)
        r = Reader()
        r.rows["teams/119/roster"]["roster"][1]["position"]["abbreviation"] = "1B"
        with self.assertRaisesRegex(ValueError, "Reliever"):
            pregame_research(849831, 10001, "away", [30001], reader=r)

    def test_crossgame_ambiguous_roles_refused(self):
        r = Reader()
        r.rows["game/849831/feed/live"]["gamePk"] = 849832
        with self.assertRaisesRegex(ValueError, "identity"):
            pregame_research(849831, 10001, "away", reader=r)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            pregame_research(849831, 10001, "away", [30001, 30001], reader=Reader())
        with self.assertRaisesRegex(ValueError, "collision"):
            pregame_research(849831, 10001, "away", [20001], reader=Reader())


class FixedOriginTransportTests(unittest.TestCase):
    def test_no_external_host_or_unbounded_path(self):
        class Response:
            status_code = 200
            url = "https://statsapi.mlb.com/api/v1/people/10001"
            content = b'{"people":[]}'
            def json(self):
                return json.loads(self.content)
        captured = []
        def getter(url, **kwargs):
            captured.append((url, kwargs))
            return Response()
        client = OfficialMlbReader(get=getter, clock=lambda: NOW)
        value, receipt = client.load("people/10001")
        self.assertEqual(value, {"people": []})
        self.assertTrue(receipt["source_url"].startswith("https://statsapi.mlb.com/"))
        self.assertEqual(captured[0][1]["timeout"], 12)
        self.assertFalse(captured[0][1]["allow_redirects"])
        with self.assertRaisesRegex(ValueError, "Invalid"):
            client.load("https://evil.example/path")
        with self.assertRaisesRegex(ValueError, "Invalid"):
            client.load("../people/10001")


if __name__ == "__main__":
    unittest.main()
