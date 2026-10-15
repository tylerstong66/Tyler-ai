"""Authenticated named MLB research through actual Flask routing, offline mocks."""
import copy
import json
import unittest
from unittest.mock import patch

import app as core
import app_v2_19_3_36 as app36
from test_v2_19_3_35_mlb_full_chat import complete as base_research

KEY = "synthetic-do-not-use-in-production"
MESSAGE = ('sports mlb full research by name :: '
           '{"date":"2026-10-15","hitter_name":"Synthetic Hitter",'
           '"team_name":"Away Club","starter_name":"Synthetic Starter",'
           '"reliever_names":["Synthetic Reliever"]}')


def resolved():
    return {
        "game_id": 849831, "hitter_id": 10001, "hitter_side": "away",
        "reliever_ids": [30001], "probable_starter_id": 20001,
        "team_name": "Away Club", "opponent_name": "Home Club",
        "limitations": ["Names are exact roster matches; no betting predictions."],
    }


def research():
    output = base_research()
    output["matchup_research"] = {"reliever_matchups": [{"pitcher": {"id": 30001}}]}
    return output


class NamedRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app36.app.test_client()

    def test_authenticated_request_resolves_names_then_independently_rechecks(self):
        with patch.object(core, "TYLER_API_KEY", KEY), patch.object(
                app36, "resolve_named_pregame", return_value=resolved()) as resolver, patch.object(
                app36, "complete_matchup_research", return_value=research()) as work:
            reply = self.client.post("/chat", json={"message": MESSAGE},
                                     headers={"X-Tyler-Key": KEY})
        self.assertEqual(reply.status_code, 200, reply.get_data(as_text=True)[:350])
        data = reply.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["sports_mlb_name_research"]["research"]["decision"], "RESEARCH ONLY - NO BET")
        self.assertTrue(data["sports_mlb_name_research"]["no_wager"])
        resolver.assert_called_once()
        work.assert_called_once_with(849831, 10001, "away", [30001])

    def test_unauthenticated_request_never_resolves_any_name(self):
        with patch.object(core, "TYLER_API_KEY", KEY), patch.object(
                app36, "resolve_named_pregame",
                side_effect=AssertionError("Unauthorized source fetch")) as resolver:
            reply = self.client.post("/chat", json={"message": MESSAGE})
        self.assertEqual(reply.status_code, 401)
        resolver.assert_not_called()

    def test_identity_mismatch_stops_result(self):
        changed = research()
        changed["probable_starter"]["id"] = 222222
        with patch.object(core, "TYLER_API_KEY", KEY), patch.object(
                app36, "resolve_named_pregame", return_value=resolved()), patch.object(
                app36, "complete_matchup_research", return_value=changed):
            reply = self.client.post("/chat", json={"message": MESSAGE},
                                     headers={"X-Tyler-Key": KEY})
        self.assertEqual(reply.status_code, 409)
        self.assertFalse(reply.get_json()["success"])
        self.assertNotIn("sports_mlb_name_research", reply.get_json())

    def test_duplicate_and_unknown_json_fields_rejected(self):
        wrong = [
            'sports mlb full research by name :: {"date":"2026-10-15","date":"2026-10-16","hitter_name":"X"}',
            'sports mlb full research by name :: {"date":"2026-10-15","hitter_name":"X","bet":true}',
            'sports mlb full research by name :: {"date":"2026-10-15"}',
            'sports mlb full research by name :: ["X"]',
            'sports mlb full research by name :: garbage',
        ]
        for m in wrong:
            with self.subTest(m=m), self.assertRaises(ValueError):
                app36.parse_named_request(m)

    def test_old_strict_id_command_still_passes_through(self):
        old = 'sports mlb full research :: {"game_id":849831,"hitter_id":10001,"hitter_side":"away"}'
        with patch.object(app36, "_OLD_HANDLE", return_value=({"legacy": True}, 200)) as previous:
            self.assertEqual(app36.handle_message(old), ({"legacy": True}, 200))
        previous.assert_called_once_with(old)

    def test_status_says_name_resolution_unfitted_and_no_wagers(self):
        r = self.client.get("/status")
        self.assertEqual(r.status_code, 200)
        status = r.get_json()
        self.assertTrue(status["sports_mlb_named_research_command_supported"])
        self.assertFalse(status["sports_mlb_named_research_predictive_edge_proven"])
        self.assertFalse(status["sports_mlb_named_research_wager_execution_enabled"])


if __name__ == "__main__":
    unittest.main()
