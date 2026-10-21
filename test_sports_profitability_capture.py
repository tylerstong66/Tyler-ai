"""Synthetic original-body archive tests; ZERO genuine sportsbook observations."""
import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import requests

import sports_profitability_capture as capture


class FakeResponse:
    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code


class NhlPriceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "archive"
        self.now = datetime(2026, 10, 23, 18, tzinfo=timezone.utc)
        self.events = [
            {"id": "future-nhl", "sport_key": "icehockey_nhl",
             "commence_time": "2026-10-24T19:00:00Z",
             "home_team": "Philadelphia Flyers", "away_team": "Boston Bruins",
             "bookmakers": [{"key": "draftkings", "markets": [
                 {"key": "h2h", "last_update": "2026-10-23T17:59:00Z",
                  "outcomes": [{"name": "Philadelphia Flyers", "price": -110},
                               {"name": "Boston Bruins", "price": 100}]}]}]},
            {"id": "started-nhl", "sport_key": "icehockey_nhl",
             "commence_time": "2026-10-23T17:00:00Z",
             "bookmakers": []},
        ]
        self.seen = []

    def fake_get(self, url, **kwargs):
        self.seen.append({"url": url, **kwargs})
        return FakeResponse(json.dumps(self.events).encode())

    def archive(self, key="test-key-only", **kwargs):
        return capture.observe_source(key, root=self.root, get=self.fake_get,
                                      clock=lambda: self.now, **kwargs)

    def test_exact_original_bytes_and_secret_safe_archive_only(self):
        output = self.archive()
        self.assertEqual(output["status"], "unqualified_source_only")
        self.assertEqual(output["future_events"], 1)
        self.assertEqual(output["started_events"], 1)
        self.assertTrue(output["NO_BET"])
        self.assertEqual(output["actual_wagers"], 0)
        self.assertEqual(len(self.seen), 1)
        request = self.seen[0]
        self.assertEqual(request["url"], capture.ENDPOINT)
        self.assertFalse(request["allow_redirects"])
        self.assertEqual(request["timeout"], 20)
        self.assertEqual(request["params"]["apiKey"], "test-key-only")
        self.assertEqual({k: v for k, v in request["params"].items() if k != "apiKey"},
                         capture.SAFE_PARAMS)
        raw = (self.root / "originals" / (output["original_sha256"] + ".json")).read_bytes()
        self.assertEqual(raw, json.dumps(self.events).encode())
        manifest = json.loads(Path(output["manifest_path"]).read_text())
        self.assertEqual(manifest["source_url"], capture.ENDPOINT)
        self.assertEqual(manifest["request_parameters"], capture.SAFE_PARAMS)
        self.assertEqual(manifest["still_future_events_at_retrieval"], 1)
        self.assertFalse(manifest["qualified_for_paper_roi"])
        self.assertFalse(manifest["sportsbook_offer_executability_verified"])
        self.assertFalse(manifest["bookmaker_publication_time_verified"])
        self.assertFalse(manifest["last_pre_start_offering_verified"])
        self.assertNotIn("test-key-only", Path(output["manifest_path"]).read_text())
        self.assertNotIn("test-key-only", json.dumps(output))
        self.assertNotIn("apiKey", Path(output["manifest_path"]).read_text())

    def test_original_bytes_reused_without_mutating_content(self):
        original = self.archive()
        location = self.root / "originals" / (original["original_sha256"] + ".json")
        saved = location.read_bytes()
        self.now = datetime(2026, 10, 23, 19, tzinfo=timezone.utc)
        later = self.archive()
        self.assertEqual(original["original_sha256"], later["original_sha256"])
        self.assertNotEqual(original["manifest_path"], later["manifest_path"])
        self.assertEqual(saved, location.read_bytes())
        self.assertEqual(len(list((self.root / "originals").glob("*.json"))), 1)
        self.assertEqual(len(list((self.root / "captures").glob("*.json"))), 2)

    def test_duplicate_timestamp_manifest_not_replaced(self):
        output = self.archive()
        before = Path(output["manifest_path"]).read_bytes()
        with self.assertRaises(FileExistsError):
            self.archive()
        self.assertEqual(before, Path(output["manifest_path"]).read_bytes())

    def test_no_secret_or_absent_key(self):
        for key in ("", "contains newline\n", None):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.archive(key)
        self.assertFalse(self.root.exists())

    def test_network_exception_is_sanitized_and_archives_nothing(self):
        def fake(url, **kwargs):
            raise requests.RequestException("SECRET-DO-NOT-ECHO")
        with self.assertRaisesRegex(RuntimeError, "request failed") as ctx:
            capture.observe_source("SECRET-DO-NOT-ECHO", root=self.root,
                                   get=fake, clock=lambda: self.now)
        self.assertNotIn("SECRET-DO-NOT-ECHO", str(ctx.exception))
        self.assertFalse(self.root.exists())

    def test_http_error_does_not_persist_error_body(self):
        def fake(url, **kwargs):
            return FakeResponse(b'{"error":"SECRET"}', status_code=429)
        with self.assertRaisesRegex(RuntimeError, "non-200"):
            capture.observe_source("key", root=self.root, get=fake,
                                   clock=lambda: self.now)
        self.assertFalse(self.root.exists())

    def test_secret_in_source_response_refused(self):
        def fake(url, **kwargs):
            return FakeResponse(b'{"apiKey":"test-key-only"}')
        with self.assertRaisesRegex(ValueError, "confidential token"):
            capture.observe_source("test-key-only", root=self.root, get=fake,
                                   clock=lambda: self.now)
        self.assertFalse(self.root.exists())

    def test_bad_shape_or_duplicate_event_never_creates_manifest(self):
        for value in ({"events": self.events}, [self.events[0], self.events[0]],
                      [{**self.events[0], "sport_key": "basketball_nba"}],
                      [{**self.events[0], "bookmakers": None}]):
            with self.subTest(value_type=type(value)):
                self.events = value
                with self.assertRaises(ValueError):
                    self.archive()
                self.assertFalse(self.root.exists())

    def test_no_network_without_explicit_capture_flag(self):
        with patch("sys.argv", ["sports_profitability_capture.py"]), patch(
                "sports_profitability_capture.requests.get") as mock:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                capture.main()
            mock.assert_not_called()
            data = json.loads(output.getvalue())
            self.assertEqual(data["status"], "inactive_no_network")
            self.assertEqual(data["actual_wagers"], 0)

    def test_no_workflow_schedule_or_automatic_odds_requests(self):
        workflow = Path(".github/workflows/nhl_price_source_manual.yml").read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertIn("THE_ODDS_API_KEY", workflow)
        self.assertIn("python sports_profitability_capture.py --capture", workflow)


if __name__ == "__main__":
    unittest.main()
