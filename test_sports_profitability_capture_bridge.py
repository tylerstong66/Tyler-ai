"""Synthetic end-to-end provenance bridge: zero network, zero wagers, zero ROI."""
import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import sports_profitability_capture as capture
import sports_profitability_capture_bridge as bridge
import sports_profitability_v1 as profit


class FakeResponse:
    status_code = 200

    def __init__(self, events):
        self.content = json.dumps(events, sort_keys=True).encode()


class ArchivedOriginalInteroperabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.at = datetime(2026, 10, 23, 18, 0, tzinfo=timezone.utc)
        self.official = {
            "game_id": "2026020999", "event_id": "401899999",
            "home": "PHI", "away": "BOS",
            "home_name": "Philadelphia Flyers", "away_name": "Boston Bruins",
            "kickoff": "2026-10-24T19:00:00Z",
        }
        self.events = [{
            "id": "synthetic-provider-id", "sport_key": "icehockey_nhl",
            "commence_time": self.official["kickoff"],
            "home_team": self.official["home_name"],
            "away_team": self.official["away_name"],
            "bookmakers": [{"key": "draftkings", "markets": [{
                "key": "h2h", "last_update": "2026-10-23T17:59:00Z",
                "outcomes": [
                    {"name": "Philadelphia Flyers", "price": -110},
                    {"name": "Boston Bruins", "price": 110},
                ]}]}],
        }]
        self.manifest_path = None

    def archive(self):
        result = capture.observe_source(
            "synthetic-test-key", root=self.repo / capture.ROOT,
            get=lambda url, **kw: FakeResponse(self.events),
            clock=lambda: self.at)
        self.manifest_path = Path(result["manifest_path"]).relative_to(self.repo)
        return result

    def read_manifest(self):
        return json.loads((self.repo / self.manifest_path).read_text())

    def replace_manifest(self, record):
        (self.repo / self.manifest_path).write_text(
            json.dumps(record, sort_keys=True) + "\n")

    def quote(self, official=None):
        return bridge.parse_archived_capture(
            self.repo, self.manifest_path,
            self.official if official is None else official)

    def verified_pregame_sources(self):
        official = {"gameWeek": [{"games": [{
            "id": 2026020999, "gameType": 2,
            "gameState": "FUT", "gameScheduleState": "OK",
            "startTimeUTC": self.official["kickoff"],
            "homeTeam": {"abbrev": "PHI", "id": 22},
            "awayTeam": {"abbrev": "BOS", "id": 6},
            "neutralSite": False,
        }]}]}
        espn = {"events": [{
            "id": "401899999", "date": self.official["kickoff"],
            "status": {"type": {"state": "pre", "completed": False}},
            "competitions": [{"neutralSite": False, "competitors": [
                {"homeAway": "home", "team": {
                    "abbreviation": "PHI", "displayName": "Philadelphia Flyers"}},
                {"homeAway": "away", "team": {
                    "abbreviation": "BOS", "displayName": "Boston Bruins"}},
            ]}],
        }]}
        def saved(filename, record, url, clock):
            path = self.repo / filename
            raw = json.dumps(record, sort_keys=True).encode()
            path.write_bytes(raw)
            return {"path": filename, "source_url": url,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "retrieved_at": clock}
        official_source = saved(
            "nhl_pregame.json", official,
            "https://api-web.nhle.com/v1/schedule/2026-10-24",
            "2026-10-23T17:58:00Z")
        espn_source = saved(
            "espn_pregame.json", espn,
            "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates=20261024",
            "2026-10-23T17:59:00Z")
        return official_source, espn_source

    def complete(self, official=None, espn=None, when="2026-10-23T17:59:30Z"):
        if official is None or espn is None:
            official, espn = self.verified_pregame_sources()
        return bridge.parse_with_independent_pregame_sources(
            self.repo, self.manifest_path, official, espn, "2026020999", when)

    def test_full_original_source_path_is_explicitly_not_profit_eligible(self):
        self.archive()
        quote = self.complete()
        self.assertEqual(quote["prices"]["home"], -110)
        self.assertEqual(quote["event_id"], "401899999")
        self.assertTrue(quote["original_pregame_sources_replayed"])
        self.assertEqual(len(quote["original_official_nhl_source_sha256"]), 64)
        self.assertEqual(len(quote["original_espn_source_sha256"]), 64)
        self.assertEqual(len(quote["independent_pregame_crosswalk_sha256"]), 64)
        self.assertIsNone(quote["provider_updated_at"])
        for flag in ("available_to_paper", "qualified_for_paper_roi",
                     "publication_server_attested", "last_pre_start_offering_verified"):
            self.assertIs(quote[flag], False)
        self.assertEqual(quote["actual_wagers"], 0)
        profit.verify_record(quote)

    def test_crosswalk_saved_after_odds_observation_is_not_accepted(self):
        self.archive()
        with self.assertRaisesRegex(ValueError, "crosswalk must precede"):
            self.complete(when="2026-10-23T18:00:30Z")

    def test_changed_official_original_fails_even_when_odds_archive_is_intact(self):
        self.archive()
        official, espn = self.verified_pregame_sources()
        (self.repo / official["path"]).write_bytes(b'{"fake":"new source"}')
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.complete(official=official, espn=espn)

    def test_bookmaker_team_mismatch_is_rejected_after_independent_crosswalk(self):
        self.events[0]["home_team"] = "New York Rangers"
        self.archive()
        with self.assertRaisesRegex(ValueError, "Exactly one NHL event"):
            self.complete()

    def test_exact_capture_to_parser_bridge_without_false_roi(self):
        result = self.archive()
        quote = self.quote()
        self.assertEqual(quote["prices"], {"home": -110, "away": 110})
        self.assertEqual(quote["provider_event_id"], "synthetic-provider-id")
        self.assertEqual(quote["source_manifest_path"], self.manifest_path.as_posix())
        self.assertEqual(quote["source_snapshot"]["sha256"], result["original_sha256"])
        self.assertEqual(quote["source_snapshot"]["request_parameters"], capture.SAFE_PARAMS)
        self.assertIsNone(quote["provider_updated_at"])
        self.assertFalse(quote["available_to_paper"])
        self.assertFalse(quote["qualified_for_paper_roi"])
        self.assertFalse(quote["last_pre_start_offering_verified"])
        self.assertFalse(quote["publication_server_attested"])
        self.assertTrue(quote["NO_BET"])
        self.assertEqual(quote["actual_wagers"], 0)
        profit.verify_record(quote)
        model = {"game_id": quote["game_id"], "event_id": quote["event_id"],
                 "home": quote["home"], "away": quote["away"],
                 "kickoff": quote["kickoff"],
                 "entry_quote_sha256": quote["sha256"],
                 "generated_at": "2026-10-23T18:02:00Z"}
        with self.assertRaisesRegex(ValueError, "offering not verified"):
            profit.check_quote(quote, model, self.repo, "entry")

    def test_ambiguous_or_nonfinite_manifest_never_replays(self):
        self.archive(); path = self.repo/self.manifest_path; original = path.read_bytes()
        variants = [original.replace(b'"actual_wagers": 0', b'"actual_wagers": 9, "actual_wagers": 0', 1)]
        variants += [b'{"unused": '+token+b','+original[1:]
                     for token in (b'NaN', b'Infinity', b'-Infinity')]
        for raw in variants:
            with self.subTest(raw_kind=raw[:40]):
                path.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, 'manifest is invalid JSON'):
                    self.quote()
                self.assertEqual(path.read_bytes(), raw)

    def test_rehashed_ambiguous_or_nonfinite_original_never_replays(self):
        self.archive(); manifest = self.read_manifest(); original = Path(manifest['original_path']).read_bytes()
        variants = [original.replace(b'"price": -110', b'"price": 5000, "price": -110', 1)]
        variants += [original.replace(b'"id":', b'"unused": '+token+b', "id":', 1)
                     for token in (b'NaN', b'Infinity', b'-Infinity')]
        for raw in variants:
            with self.subTest(raw_kind=raw[:40]):
                digest = hashlib.sha256(raw).hexdigest()
                path = self.repo/capture.ROOT/'originals'/(digest+'.json'); path.write_bytes(raw)
                self.replace_manifest({**manifest, 'raw_entity_body_sha256': digest, 'original_path': str(path)})
                with self.assertRaisesRegex(ValueError, 'Original source is not valid JSON'):
                    self.quote()
                self.assertEqual(path.read_bytes(), raw)
    def test_captured_retrieval_and_archive_time_are_distinct(self):
        self.archive()
        manifest = self.read_manifest()
        self.assertEqual(manifest["retrieved_at"], "2026-10-23T18:00:00+00:00")
        self.assertEqual(manifest["archived_at"], manifest["retrieved_at"])
        self.assertEqual(bridge.REQUEST, capture.SAFE_PARAMS)

    def test_reject_changed_original_bytes(self):
        self.archive()
        manifest = self.read_manifest()
        original = self.repo / manifest["original_path"]
        original.write_bytes(b'{"fabricated":"historical"}')
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.quote()

    def test_reject_manifest_falsely_claiming_book_or_publication_proof(self):
        self.archive()
        base = self.read_manifest()
        for flag in ("qualified_for_paper_roi", "sportsbook_offer_executability_verified",
                     "bookmaker_publication_time_verified", "last_pre_start_offering_verified",
                     "exact_crosswalk_with_official_nhl"):
            with self.subTest(flag=flag):
                altered = copy.deepcopy(base)
                altered[flag] = True
                self.replace_manifest(altered)
                with self.assertRaisesRegex(ValueError, "Cannot promote"):
                    self.quote()
        self.replace_manifest(base)

    def test_reject_wrong_or_secret_bearing_request_contract(self):
        self.archive()
        base = self.read_manifest()
        for value in ({"regions": "us", "markets": "h2h", "bookmakers": "fanduel",
                       "oddsFormat": "american"},
                      {**capture.SAFE_PARAMS, "apiKey": "synthetic-secret"}):
            with self.subTest(value=value):
                altered = copy.deepcopy(base)
                altered["request_parameters"] = value
                self.replace_manifest(altered)
                with self.assertRaisesRegex(ValueError, "pinned to safe request"):
                    self.quote()
        self.replace_manifest(base)

    def test_reject_hindsight_or_stale_capture_manifest(self):
        self.archive()
        base = self.read_manifest()
        for timestamp in ("2026-10-23T18:06:00+00:00",
                          "2026-10-23T17:00:00+00:00"):
            with self.subTest(timestamp=timestamp):
                altered = copy.deepcopy(base)
                altered["archived_at"] = timestamp
                self.replace_manifest(altered)
                with self.assertRaisesRegex(ValueError, "time ordering or freshness"):
                    self.quote()
        self.replace_manifest(base)

    def test_reject_false_denominator_or_nonmatching_original_start(self):
        self.archive()
        base = self.read_manifest()
        altered = copy.deepcopy(base)
        altered["still_future_events_at_retrieval"] = 2
        self.replace_manifest(altered)
        with self.assertRaisesRegex(ValueError, "coverage disagrees"):
            self.quote()
        self.replace_manifest(base)
        wrong = {**self.official, "kickoff": "2026-10-24T20:00:00Z"}
        with self.assertRaisesRegex(ValueError, "Exactly one NHL event"):
            self.quote(official=wrong)

    def test_reject_archive_path_traversal_or_mismatched_digest(self):
        self.archive()
        base = self.read_manifest()
        for path in ("../external.json",
                     "benchmarks/nhl_price_source_observations_v1/originals/other.json"):
            altered = copy.deepcopy(base)
            altered["original_path"] = path
            self.replace_manifest(altered)
            with self.assertRaisesRegex(ValueError, "content-addressed"):
                self.quote()
        self.replace_manifest(base)
        outside = self.repo / "foreign" / self.manifest_path.name
        outside.parent.mkdir(parents=True)
        outside.write_bytes((self.repo / self.manifest_path).read_bytes())
        with self.assertRaisesRegex(ValueError, "pinned NHL capture"):
            bridge.parse_archived_capture(self.repo, outside, self.official)

    def test_reject_symlinks_at_manifest_original_and_directory_ancestors(self):
        for location in ("manifest", "original", "captures", "originals", "root", "benchmarks"):
            with self.subTest(location=location):
                self.archive()
                original = Path(self.read_manifest()["original_path"])
                target = {"manifest": self.repo / self.manifest_path,
                          "original": original,
                          "captures": self.repo / capture.ROOT / "captures",
                          "originals": self.repo / capture.ROOT / "originals",
                          "root": self.repo / capture.ROOT,
                          "benchmarks": self.repo / "benchmarks"}[location]
                moved = self.repo / "redirected"
                target.rename(moved)
                target.symlink_to(moved, target_is_directory=moved.is_dir())
                try:
                    with self.assertRaisesRegex(ValueError, "Symlink"):
                        self.quote()
                finally:
                    target.unlink()
                    moved.rename(target)
                    (self.repo / self.manifest_path).unlink()

    def test_manifest_counts_require_nonnegative_integers_not_booleans_or_floats(self):
        self.archive()
        base = self.read_manifest()
        for field in ("event_rows_returned", "still_future_events_at_retrieval",
                      "already_started_events_at_retrieval"):
            for value in (True, False, 1.0, 0.0, -1, None):
                with self.subTest(field=field, value=value):
                    altered = copy.deepcopy(base)
                    altered[field] = value
                    self.replace_manifest(altered)
                    with self.assertRaises(ValueError):
                        self.quote()
        self.replace_manifest(base)

    def test_all_original_event_rows_must_obey_collector_contract(self):
        self.archive()
        base = self.read_manifest()
        for extra in (None, {}, {**self.events[0], "sport_key": "basketball_nba"},
                      self.events[0]):
            with self.subTest(extra=extra):
                raw = json.dumps(self.events + [extra]).encode()
                digest = hashlib.sha256(raw).hexdigest()
                path = self.repo / capture.ROOT / "originals" / (digest + ".json")
                path.write_bytes(raw)
                altered = {**base, "raw_entity_body_sha256": digest,
                           "original_path": str(path), "event_rows_returned": 2,
                           "still_future_events_at_retrieval": 2}
                self.replace_manifest(altered)
                with self.assertRaises(ValueError):
                    self.quote()
        self.replace_manifest(base)

    def test_oversized_manifest_is_rejected_before_reading_body(self):
        from unittest.mock import patch
        self.archive()
        path = self.repo / self.manifest_path
        path.write_bytes(b" " * 100_001)
        with patch.object(Path, "read_bytes", side_effect=AssertionError("unbounded read")):
            with self.assertRaises(ValueError):
                self.quote()


if __name__ == "__main__":
    unittest.main()
