"""Authenticated Flask transport contract for newly deployed MLB research module.

All credentials are synthetic, external requests are mocked, and no production
wagers, model calls, or writes occur.
"""
import unittest
from unittest.mock import patch

import app as core
import app_v2_19_3_35 as app35
from test_v2_19_3_35_mlb_full_chat import complete, request

TEST_KEY = "nonprod-mock-auth-key-for-unit-tests"


class AuthenticatedMlbChatTests(unittest.TestCase):
    def setUp(self):
        self.client = app35.app.test_client()

    def test_unauthenticated_api_cannot_run_research(self):
        with patch.object(core, "TYLER_API_KEY", TEST_KEY), patch.object(
                app35, "complete_matchup_research",
                side_effect=AssertionError("Should not fetch without authorization")) as work:
            reply = self.client.post("/chat", json={"message": request()})
        self.assertEqual(reply.status_code, 401)
        self.assertFalse(work.called)

    def test_authenticated_api_routes_to_new_full_research_command(self):
        with patch.object(core, "TYLER_API_KEY", TEST_KEY), patch.object(
                app35, "complete_matchup_research", return_value=complete()) as work:
            reply = self.client.post("/chat", json={"message": request()},
                         headers={"X-Tyler-Key": TEST_KEY})
        self.assertEqual(reply.status_code, 200, reply.get_data(as_text=True)[:500])
        result = reply.get_json()
        self.assertTrue(result["success"])
        self.assertEqual(result["sports_mlb_full_research"]["decision"], "RESEARCH ONLY - NO BET")
        self.assertIsNone(result["sports_mlb_full_research"]["estimated_home_run_probability"])
        self.assertFalse(result["sports_mlb_full_research"]["wager_executed"])
        work.assert_called_once_with(849831, 10001, "away", [30001])

    def test_wrong_key_never_reaches_matchup_research(self):
        with patch.object(core, "TYLER_API_KEY", TEST_KEY), patch.object(
                app35, "complete_matchup_research",
                side_effect=AssertionError("No unauthorized external calls")) as work:
            result = self.client.post("/chat", json={"message": request()},
                                      headers={"X-Tyler-Key": "wrong-key"})
        self.assertEqual(result.status_code, 401)
        work.assert_not_called()

    def test_authorized_source_failure_is_explicit_and_no_wager(self):
        with patch.object(core, "TYLER_API_KEY", TEST_KEY), patch.object(
                app35, "complete_matchup_research", side_effect=RuntimeError("Public source missing")):
            result = self.client.post("/chat", json={"message": request()},
                                      headers={"X-Tyler-Key": TEST_KEY})
        self.assertEqual(result.status_code, 409)
        self.assertFalse(result.get_json()["success"])
        self.assertNotIn("sports_mlb_full_research", result.get_json())

    def test_existing_public_routes_stay_consistent(self):
        status = self.client.get("/status")
        self.assertEqual(status.status_code, 200)
        data = status.get_json()
        self.assertTrue(data["sports_mlb_full_research_command_supported"])
        self.assertFalse(data["sports_wager_execution_enabled"])
        self.assertEqual(self.client.get("/ui/paper-results").status_code, 401)


if __name__ == "__main__":
    unittest.main()
