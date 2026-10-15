"""Deterministic official-name MLB resolver checks, no live calls or wagering."""
import copy
import unittest

from sports_mlb_name_lookup import resolve_named_pregame
from test_sports_mlb_sources import Reader


def reader():
    r = Reader()
    g = r.rows["game/849831/feed/live"]
    g["gameData"]["probablePitchers"]["home"]["fullName"] = "Synthetic Starter"
    r.rows["schedule"] = {"dates": [{"games": [{
        "gamePk": 849831, "gameDate": "2026-10-15T23:00:00Z",
        "status": {"abstractGameState": "Preview", "detailedState": "Scheduled"},
        "teams": {
            "home": {"team": {"id": 119, "name": "Home Club"}},
            "away": {"team": {"id": 158, "name": "Away Club"}},
        },
    }]}]}
    return r


def resolve(r=None, **overrides):
    params = {"date": "2026-10-15", "hitter_name": "Synthetic Hitter",
              "team_name": "Away Club", "starter_name": "Synthetic Starter",
              "reliever_names": ["Synthetic Reliever"], "reader": r or reader()}
    params.update(overrides)
    return resolve_named_pregame(**params)


class NamedPregameTests(unittest.TestCase):
    def test_valid_exact_names_resolve_real_identity_fields(self):
        r = reader()
        out = resolve(r)
        self.assertEqual(out["game_id"], 849831)
        self.assertEqual(out["hitter_id"], 10001)
        self.assertEqual(out["hitter_side"], "away")
        self.assertEqual(out["probable_starter_id"], 20001)
        self.assertEqual(out["reliever_ids"], [30001])
        self.assertEqual(out["status"], "IDENTITIES VERIFIED - RESEARCH ONLY")
        self.assertEqual(len(out["sources"]), 3)
        self.assertEqual(out["team_name"], "Away Club")
        self.assertTrue(any("not prove" in x for x in out["limitations"]))

    def test_wrong_names_and_teams_fail_closed(self):
        for change in [
            {"hitter_name": "Unknown Player"}, {"team_name": "Different Club"},
            {"starter_name": "Unknown Starter"}, {"reliever_names": ["Unknown Pitcher"]},
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                resolve(**change)

    def test_future_time_and_invalid_dates_are_rejected(self):
        for date in ["2026-10-14", "2026-10-22", "2026-02-30",
                     "2026/10/15", "2026-10-15T00:00:00Z"]:
            with self.subTest(date=date), self.assertRaises(ValueError):
                resolve(date=date)

    def test_doubleheader_requires_specific_game_id(self):
        r = reader()
        g = copy.deepcopy(r.rows["schedule"]["dates"][0]["games"][0])
        g["gamePk"] = 849832
        g["gameDate"] = "2026-10-16T00:30:00Z"  # same local Eastern date
        r.rows["schedule"]["dates"][0]["games"].append(g)
        feed = copy.deepcopy(r.rows["game/849831/feed/live"])
        feed["gamePk"] = 849832
        feed["gameData"]["datetime"]["dateTime"] = "2026-10-16T00:30:00Z"
        r.rows["game/849832/feed/live"] = feed
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            resolve(r)
        self.assertEqual(resolve(r, game_id=849832)["game_id"], 849832)

    def test_bad_game_feed_identity_rejected(self):
        r = reader()
        r.rows["game/849831/feed/live"]["gameData"]["teams"]["home"]["id"] = 888
        with self.assertRaisesRegex(ValueError, "identity"):
            resolve(r)

    def test_strict_hitter_identity_and_pregame_only(self):
        r = reader()
        r.rows["teams/158/roster"]["roster"][0]["position"]["abbreviation"] = "P"
        with self.assertRaisesRegex(ValueError, "No unique"):
            resolve(r)
        r = reader()
        r.rows["schedule"]["dates"][0]["games"][0]["status"]["abstractGameState"] = "Final"
        with self.assertRaisesRegex(ValueError, "No unique"):
            resolve(r)

    def test_refuses_unverified_relief_role_and_repeated_names(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            resolve(reliever_names=["Synthetic Reliever", "synthetic reliever"])
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            resolve(reliever_names=["Synthetic Starter"])


if __name__ == "__main__":
    unittest.main()
