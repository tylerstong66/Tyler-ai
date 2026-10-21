"""Synthetic archived odds only; cannot establish a real executable sportsbook price."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import sports_profitability_price_source as parser
import sports_profitability_v1 as p


class ArchivedNhlOddsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.official = {
            "game_id": "2026020999", "event_id": "401899999",
            "home": "PHI", "away": "BOS",
            "home_name": "Philadelphia Flyers", "away_name": "Boston Bruins",
            "kickoff": "2026-10-24T19:00:00Z",
        }
        self.events = [{
            "sport_key": "icehockey_nhl",
            "id": "api-external-id", "commence_time": self.official["kickoff"],
            "home_team": self.official["home_name"],
            "away_team": self.official["away_name"],
            "bookmakers": [
                {"key": "draftkings", "last_update": "2026-10-20T00:00:00Z",
                 "markets": [{"key": "h2h", "last_update": "2026-10-23T17:59:00Z",
                              "outcomes": [
                                  {"name": "Philadelphia Flyers", "price": -110},
                                  {"name": "Boston Bruins", "price": 110}]}]}
            ],
        }]
        self.capture_time = "2026-10-23T18:00:00Z"
        self.archive_time = "2026-10-23T18:01:00Z"
        self.source = self.save(self.events)

    def save(self, events):
        data = json.dumps(events, sort_keys=True, indent=2).encode()
        file = self.root / "evidence" / "odds.json"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        return {
            "path": "evidence/odds.json",
            "source_url": parser.ODDS_ENDPOINT,
            "request_parameters": dict(parser.REQUEST),
            "sha256": hashlib.sha256(data).hexdigest(),
            "retrieved_at": self.capture_time,
        }

    def observe(self, source=None, official=None, archive_time=None):
        return parser.observe(
            self.root, self.source if source is None else source,
            self.official if official is None else official,
            self.archive_time if archive_time is None else archive_time)

    def test_market_quote_preserves_exact_book_event_start_and_no_bet(self):
        quote = self.observe()
        self.assertEqual(quote["provider_event_id"], "api-external-id")
        self.assertEqual(quote["event_id"], "401899999")
        self.assertEqual(quote["prices"], {"home": -110, "away": 110})
        self.assertEqual(quote["market"], p.MARKET)
        self.assertEqual(quote["line"], None)
        self.assertEqual(quote["aggregator_market_last_seen_at"], "2026-10-23T17:59:00Z")
        self.assertIsNone(quote["provider_updated_at"])
        self.assertEqual(quote["recorded_at"], self.archive_time)
        self.assertFalse(quote["available_to_paper"])
        self.assertFalse(quote["last_pre_start_offering_verified"])
        self.assertEqual(quote["actual_wagers"], 0)
        self.assertTrue(quote["NO_BET"])
        p.verify_record(quote)
        paper = {"game_id": quote["game_id"], "event_id": quote["event_id"],
                 "home": quote["home"], "away": quote["away"],
                 "kickoff": quote["kickoff"],
                 "entry_quote_sha256": quote["sha256"],
                 "generated_at": "2026-10-23T18:02:00Z"}
        with self.assertRaisesRegex(ValueError, "offering not verified"):
            p.check_quote(quote, paper, self.root, "entry")

    def test_even_relabelled_aggregator_quote_cannot_become_proven_bookmaker_quote(self):
        quote = self.observe()
        quote["available_to_paper"] = True
        quote.pop("sha256")
        quote["sha256"] = p.hash_record(quote)
        pred = {"game_id": quote["game_id"], "event_id": quote["event_id"],
                "home": quote["home"], "away": quote["away"],
                "kickoff": quote["kickoff"],
                "entry_quote_sha256": quote["sha256"],
                "generated_at": "2026-10-23T18:02:00Z"}
        with self.assertRaisesRegex(ValueError, "UTC timestamp string required"):
            p.check_quote(quote, pred, self.root, "entry")

    def test_missing_market_last_update_rejected_even_when_book_has_timestamp(self):
        events = copy.deepcopy(self.events)
        del events[0]["bookmakers"][0]["markets"][0]["last_update"]
        self.save(events)
        with self.assertRaisesRegex(ValueError, "Market-specific update timestamp"):
            self.observe(source=self.save(events))

    def test_outdated_market_update_not_backfilled_from_bookmaker(self):
        events = copy.deepcopy(self.events)
        events[0]["bookmakers"][0]["markets"][0]["last_update"] = "2026-10-23T17:40:00Z"
        with self.assertRaisesRegex(ValueError, "older than"):
            self.observe(source=self.save(events))

    def test_future_provider_quote_update_rejected(self):
        events = copy.deepcopy(self.events)
        events[0]["bookmakers"][0]["markets"][0]["last_update"] = "2026-10-23T18:01:00Z"
        with self.assertRaisesRegex(ValueError, "future-dated"):
            self.observe(source=self.save(events))

    def test_event_or_start_not_exact_cannot_enter_market_sample(self):
        for field, value in (
                ("home_team", "New York Rangers"),
                ("commence_time", "2026-10-24T19:01:00Z"),
                ("sport_key", "americanfootball_nfl")):
            with self.subTest(field=field):
                events = copy.deepcopy(self.events)
                events[0][field] = value
                with self.assertRaisesRegex(ValueError, "Exactly one NHL event"):
                    self.observe(source=self.save(events))

    def test_book_or_market_ambiguity_never_arbitrarily_selects_a_quote(self):
        for mode in ("duplicate_book", "duplicate_market", "wrong_book", "wrong_market"):
            with self.subTest(mode=mode):
                events = copy.deepcopy(self.events)
                books = events[0]["bookmakers"]
                if mode == "duplicate_book":
                    books.append(copy.deepcopy(books[0]))
                elif mode == "duplicate_market":
                    books[0]["markets"].append(copy.deepcopy(books[0]["markets"][0]))
                elif mode == "wrong_book":
                    books[0]["key"] = "fanduel"
                else:
                    books[0]["markets"][0]["key"] = "h2h_p1"
                with self.assertRaisesRegex(ValueError, "Exactly one"):
                    self.observe(source=self.save(events))

    def test_no_third_side_or_handicap_or_wrong_team(self):
        for mode in ("third", "point", "name", "duplicate"):
            with self.subTest(mode=mode):
                events = copy.deepcopy(self.events)
                outcomes = events[0]["bookmakers"][0]["markets"][0]["outcomes"]
                if mode == "third":
                    outcomes.append({"name": "Draw", "price": 250})
                elif mode == "point":
                    outcomes[0]["point"] = -1.5
                elif mode == "name":
                    outcomes[0]["name"] = "Unrelated Team"
                else:
                    outcomes[1]["name"] = outcomes[0]["name"]
                with self.assertRaises(ValueError):
                    self.observe(source=self.save(events))

    def test_original_bytes_and_sanitized_request_params_are_mandatory(self):
        source = copy.deepcopy(self.source)
        source["request_parameters"]["apiKey"] = "not-an-actual-key"
        with self.assertRaisesRegex(ValueError, "sanitized"):
            self.observe(source=source)
        source = copy.deepcopy(self.source)
        source["source_url"] += "?apiKey=should_not_be_recorded"
        with self.assertRaisesRegex(ValueError, "sanitized"):
            self.observe(source=source)
        (self.root / self.source["path"]).write_bytes(b"tamper")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.observe()

    def test_started_or_delayed_publication_is_never_eligible(self):
        with self.assertRaisesRegex(ValueError, "before kickoff"):
            self.observe(archive_time="2026-10-24T19:05:00Z")
        with self.assertRaisesRegex(ValueError, "before kickoff"):
            self.observe(archive_time="2026-10-23T18:10:00Z")

    def test_duplicate_event_and_unknown_format_rejected(self):
        events = copy.deepcopy(self.events) * 2
        with self.assertRaisesRegex(ValueError, "Exactly one NHL event"):
            self.observe(source=self.save(events))
        src = self.save({"data": self.events})
        with self.assertRaisesRegex(ValueError, "event array"):
            self.observe(source=src)


if __name__ == "__main__":
    unittest.main()
