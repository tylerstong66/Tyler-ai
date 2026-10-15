"""MLB official bullpen workload: identity, chronology, counts, unknown-data tests."""
import copy
import unittest
from datetime import datetime

from sports_mlb_bullpen_usage import recent_pitcher_usage
from test_sports_mlb_sources import Reader

PAST_PK = 849700
PAST_START = "2026-10-13T23:00:00Z"


def setup():
    r = Reader()
    past = {
        "gamePk": PAST_PK,
        "gameDate": PAST_START,
        "status": {"abstractGameState": "Final", "detailedState": "Final"},
        "teams": {"home": {"team": {"id": 119}}, "away": {"team": {"id": 158}}}}
    r.rows["schedule"] = {"dates": [{"games": [past]}]}
    r.rows["game/" + str(PAST_PK) + "/feed/live"] = {
        "gamePk": PAST_PK,
        "gameData": {
            "datetime": {"dateTime": PAST_START},
            "teams": {"home": {"id": 119}, "away": {"id": 158}},
            "status": {"abstractGameState": "Final", "detailedState": "Final"}},
        "liveData": {
            "boxscore": {"teams": {"home": {
                "pitchers": [20001, 30001],
                "players": {
                    "ID30001": {"stats": {"pitching": {"numberOfPitches": 16}}},
                    "ID20001": {"stats": {"pitching": {"numberOfPitches": 83}}},
                }}}}}}
    return r


class BullpenTests(unittest.TestCase):
    def test_final_game_pitch_workload_and_unknown_appearance_probability(self):
        reader = setup()
        result = recent_pitcher_usage(849831, "home", [30001], reader=reader)
        self.assertEqual(result["decision"], "RESEARCH ONLY - NO BET")
        self.assertEqual(result["candidates"][0]["recorded_appearances"], 1)
        self.assertEqual(result["candidates"][0]["pitches_thrown_observed"], 16)
        self.assertEqual(result["candidates"][0]["availability"], "unknown")
        self.assertIsNone(result["candidates"][0]["projected_appearance_probability"])
        self.assertTrue(result["candidates"][0]["coverage_complete"])
        self.assertEqual(result["historical_games_with_incomplete_data"], [])
        self.assertEqual(len(result["capture_receipts"]), 4)

    def test_missing_pitch_count_is_incomplete_not_zero(self):
        reader = setup()
        del reader.rows["game/" + str(PAST_PK) + "/feed/live"]["liveData"]["boxscore"]["teams"]["home"]["players"]["ID30001"]["stats"]["pitching"]["numberOfPitches"]
        result = recent_pitcher_usage(849831, "home", [30001], reader=reader)
        candidate = result["candidates"][0]
        self.assertEqual(candidate["recorded_appearances"], 0)
        self.assertFalse(candidate["coverage_complete"])
        self.assertEqual(result["historical_games_with_incomplete_data"][0]["reason"], "pitch_count_missing")

    def test_unplayed_games_cannot_be_used_as_verified_history(self):
        reader = setup()
        game = reader.rows["schedule"]["dates"][0]["games"][0]
        game["status"]["abstractGameState"] = "Preview"
        result = recent_pitcher_usage(849831, "home", [30001], reader=reader)
        self.assertEqual(result["candidates"][0]["recorded_appearances"], 0)
        self.assertEqual(result["historical_games_with_incomplete_data"][0]["reason"], "not_verified_final")

    def test_duplicate_game_and_official_mismatch_fail_closed(self):
        reader = setup()
        games = reader.rows["schedule"]["dates"][0]["games"]
        games.append(copy.deepcopy(games[0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            recent_pitcher_usage(849831, "home", [30001], reader=reader)
        reader = setup()
        reader.rows["game/" + str(PAST_PK) + "/feed/live"]["gamePk"] += 1
        with self.assertRaisesRegex(ValueError, "contradicts"):
            recent_pitcher_usage(849831, "home", [30001], reader=reader)

    def test_wrong_roster_and_started_upcoming_game_rejected(self):
        with self.assertRaisesRegex(ValueError, "active"):
            recent_pitcher_usage(849831, "home", [99999], reader=setup())
        reader = setup()
        reader.now = datetime.fromisoformat("2026-10-16T00:00:00+00:00")
        with self.assertRaisesRegex(ValueError, "first pitch"):
            recent_pitcher_usage(849831, "home", [30001], reader=reader)

    def test_invalid_window_and_candidate_limits(self):
        for bad in [0, 8, True, "5"]:
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "Lookback"):
                recent_pitcher_usage(849831, "home", [30001], reader=setup(), lookback_days=bad)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            recent_pitcher_usage(849831, "home", [30001, 30001], reader=setup())
        with self.assertRaisesRegex(ValueError, "At most four"):
            recent_pitcher_usage(849831, "home", [1, 2, 3, 4, 5], reader=setup())


if __name__ == "__main__":
    unittest.main()
