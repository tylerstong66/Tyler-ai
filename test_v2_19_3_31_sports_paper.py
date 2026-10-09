import copy
import json
import unittest
from unittest.mock import patch

import app_v2_19_3_31 as v
from sports_betting import SportsLedger, digest
from sports_paper_trial import (NflPublicFeed, PaperTrial, InjuryTables, validate_forecast,
    PAPER_PREDICTIONS, PAPER_RESULTS, PAPER_QUOTES)
from test_v2_18_skill_lab import MemoryStore

NOW = "2026-10-09T14:00:00+00:00"
START = "2026-10-11T13:30:00Z"


def forecast():
    return {"probabilities": {"home": .6, "away": .39, "tie": .01},
            "rationale": "Experimental estimate from supplied evidence.",
            "uncertainty": "Uncalibrated; quote age and final availability are unknown."}


def game():
    return {"event_id": "401872981", "event": "Away at Home", "event_start": START,
            "state": "pre", "completed": False,
            "teams": {s: {"id": str(i), "name": s, "score": "0"} for i, s in enumerate(("home", "away"))},
            "moneyline_quote": {"provider": "Publisher", "prices": {"home": -125, "away": 110},
                                "quote_age_verified": False, "provider_updated_at": None},
            "evidence": {"event_market_injuries": {"source_url": "https://example.com", "retrieved_at": NOW,
                         "provider_updated_at": None, "response_sha256": "fixture"}}}


class FakeFeed:
    def __init__(self): self.data = game()
    def pregame(self, identifier): return copy.deepcopy(self.data)
    def game(self, identifier): return copy.deepcopy(self.data)


class PaperTests(unittest.TestCase):
    def setUp(self):
        self.store, self.feed = MemoryStore(), FakeFeed()
        self.now = NOW
        self.ledger = SportsLedger(self.store.get_rows, self.store.save_row, lambda: self.now)
        self.profile = {"version": 1, "instructions": ["Do not place wagers"]}
        self.trial = PaperTrial(self.ledger, self.feed, lambda g: forecast(), "fixed-model", lambda: self.profile)

    def final(self, home="24", away="17"):
        self.now = "2026-10-11T18:00:00+00:00"
        self.feed.data.update(state="post", completed=True)
        self.feed.data["teams"]["home"]["score"] = home
        self.feed.data["teams"]["away"]["score"] = away

    def test_original_is_pregame_hashed_and_never_a_wager(self):
        r = self.trial.analyze("401872981")
        self.assertEqual(r["recorded_at"], NOW)
        self.assertEqual(r["decision"], "NO BET")
        self.assertFalse(r["wager_executed"])
        self.assertEqual(r["profile_fingerprint"], digest(self.profile))
        self.assertEqual(self.ledger._records(PAPER_PREDICTIONS), [r])

    def test_duplicate_game_cannot_regenerate_or_overwrite_original(self):
        self.trial.analyze("401872981")
        self.trial.forecast_fn = lambda g: self.fail("Duplicate must not call model")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.trial.analyze("401872981")
        self.assertEqual(len(self.store.rows), 1)

    def test_crossing_kickoff_during_generation_records_nothing(self):
        def generate(g):
            self.now = "2026-10-11T13:30:00+00:00"
            return forecast()
        self.trial.forecast_fn = generate
        with self.assertRaisesRegex(ValueError, "started"):
            self.trial.analyze("401872981")
        self.assertEqual(self.store.rows, [])

    def test_profile_change_during_generation_records_nothing(self):
        def generate(g):
            self.profile["version"] = 2
            return forecast()
        self.trial.forecast_fn = generate
        with self.assertRaisesRegex(ValueError, "profile changed"):
            self.trial.analyze("401872981")
        self.assertEqual(self.store.rows, [])

    def test_model_failure_records_nothing(self):
        self.trial.forecast_fn = lambda g: {"probabilities": {"home": .8}}
        with self.assertRaises(ValueError): self.trial.analyze("401872981")
        self.assertEqual(self.store.rows, [])

    def test_invalid_probabilities_are_rejected(self):
        for p in (True, float("nan"), float("inf"), -.1, 1.1):
            f = forecast(); f["probabilities"]["home"] = p
            with self.subTest(p=p), self.assertRaises(ValueError): validate_forecast(f)
        f = forecast(); f["probabilities"]["tie"] = .1
        with self.assertRaises(ValueError): validate_forecast(f)

    def test_secret_literal_cannot_be_persisted(self):
        self.trial.forecast_fn = lambda g: {**forecast(), "rationale": "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz0123456789"}
        with self.assertRaisesRegex(ValueError, "credential"): self.trial.analyze("401872981")
        self.assertEqual(self.store.rows, [])

    def test_unconfirmed_storage_reports_unknown_outcome(self):
        self.ledger.save_row = lambda *a: None
        with self.assertRaisesRegex(RuntimeError, "outcome unknown"):
            self.trial.analyze("401872981")

    def test_in_progress_game_cannot_settle(self):
        r = self.trial.analyze("401872981")
        self.final(); self.feed.data["completed"] = False
        with self.assertRaisesRegex(ValueError, "final result"): self.trial.settle(r["paper_prediction_id"])
        self.assertEqual(self.ledger._records(PAPER_RESULTS), [])

    def test_final_result_appends_without_changing_original_bytes(self):
        r = self.trial.analyze("401872981"); original = self.store.rows[0]["memories"]
        self.final(); result = self.trial.settle(r["paper_prediction_id"])
        self.assertEqual(self.store.rows[0]["memories"], original)
        self.assertEqual(result["prediction_sha256"], digest(r))
        self.assertEqual(result["outcome"], "home")
        self.assertAlmostEqual(result["hypothetical_flat_unit_profit"], .8)
        self.assertIsNone(result["price_clv_percentage_points"])
        with self.assertRaisesRegex(ValueError, "already recorded"): self.trial.settle(r["paper_prediction_id"])

    def test_final_scores_must_be_integer_and_team_identity_unchanged(self):
        r = self.trial.analyze("401872981")
        for score in (True, 24.5, "24.0", None, -1):
            self.final(home=score)
            with self.subTest(score=score), self.assertRaises(ValueError): self.trial.settle(r["paper_prediction_id"])
        self.final(); self.feed.data["teams"]["home"]["id"] = "different"
        with self.assertRaisesRegex(ValueError, "identities"): self.trial.settle(r["paper_prediction_id"])

    def test_tie_is_paper_push_and_multiclass_scoring_is_explicit(self):
        r = self.trial.analyze("401872981"); self.final("17", "17"); self.trial.settle(r["paper_prediction_id"])
        report = self.trial.report()
        self.assertAlmostEqual(report["multiclass_brier_score"], .6**2 + .39**2 + .99**2)
        self.assertEqual(report["hypothetical_flat_unit_roi"], 0)
        self.assertEqual(report["calibration_bins"][0]["observed_win_rate"], 0)
        self.assertEqual(report["pending_in_window"], 0)

    def test_no_quote_keeps_hypothetical_roi_unknown(self):
        self.feed.data["moneyline_quote"] = None
        r = self.trial.analyze("401872981"); self.final(); self.trial.settle(r["paper_prediction_id"])
        self.assertIsNone(self.trial.report()["hypothetical_flat_unit_roi"])
        self.assertEqual(self.trial.report()["priced_result_count"], 0)

    def test_quote_capture_preserves_unknown_age_and_is_not_closing_line(self):
        r = self.trial.analyze("401872981"); q = self.trial.capture_quote(r["paper_prediction_id"])
        self.assertFalse(q["verified_closing_line"])
        self.assertFalse(q["quote"]["quote_age_verified"])
        self.assertEqual(self.trial.report()["observed_pre_event_quotes_in_window"], 1)
        self.final()
        with self.assertRaisesRegex(ValueError, "pre-event"): self.trial.capture_quote(r["paper_prediction_id"])

    def test_ledger_tampering_and_broken_result_link_are_detected(self):
        r = self.trial.analyze("401872981"); self.final(); self.trial.settle(r["paper_prediction_id"])
        data = json.loads(self.store.rows[1]["memories"]); data["payload"]["prediction_sha256"] = "wrong"; data["sha256"] = digest(data["payload"])
        self.store.rows[1]["memories"] = json.dumps(data)
        with self.assertRaisesRegex(RuntimeError, "linkage"): self.trial.report()
        self.store.rows[0]["memories"] = self.store.rows[0]["memories"].replace('"NO BET"', '"BET"')
        with self.assertRaisesRegex(RuntimeError, "integrity"): self.trial.records()


class FeedTests(unittest.TestCase):
    def summary(self):
        return {"header": {"id": "401872981", "season": {"year": 2026, "type": 2}, "week": 5,
                "competitions": [{"date": START, "status": {"type": {"state": "pre", "completed": False}},
                "competitors": [{"id": str(i), "homeAway": s, "team": {"displayName": s, "name": s}} for i,s in enumerate(("home", "away"))]}]},
                "pickcenter": [{"provider": {"name": "DraftKings"}, "moneyline": {s: {"close": {"odds": p}} for s,p in (("home", "-125"), ("away", "+110"))}}]}

    def feed(self, data):
        response = type("Response", (), {"status_code": 200, "json": lambda s: copy.deepcopy(data)})()
        return NflPublicFeed(get=lambda *a, **k: response, now_fn=lambda: NOW)

    def test_caller_cannot_supply_external_url(self):
        feed = NflPublicFeed(get=lambda *a, **k: self.fail("Invalid id must not fetch"))
        with self.assertRaises(ValueError): feed.game("https://example.com")

    def test_publisher_close_field_is_not_verified_quote_freshness(self):
        g = self.feed(self.summary()).game("401872981")
        self.assertEqual(g["moneyline_quote"]["prices"], {"home": -125, "away": 110})
        self.assertFalse(g["moneyline_quote"]["quote_age_verified"])
        self.assertIsNone(g["moneyline_quote"]["provider_updated_at"])
        self.assertEqual(g["evidence"]["event_market_injuries"]["retrieved_at"], NOW)

    def test_bad_event_and_missing_competition_fail_closed(self):
        d=self.summary();d["header"]["id"]="401000000"
        with self.assertRaisesRegex(ValueError,"different event"): self.feed(d).game("401872981")
        d=self.summary();d["header"]["competitions"]=[]
        with self.assertRaises(ValueError): self.feed(d).game("401872981")

    def test_started_event_cannot_be_forecast(self):
        d=self.summary();d["header"]["competitions"][0]["date"]=NOW
        with self.assertRaisesRegex(ValueError,"before"): self.feed(d).pregame("401872981")

    def test_empty_official_status_remains_empty(self):
        parser=InjuryTables();parser.feed('<div class="d3-o-section-sub-title"><span>Eagles</span></div><table><tr><th>Player</th><th>Position</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr><tr><td>A Player</td><td>WR</td><td>Knee</td><td>Limited</td><td></td></tr></table>')
        self.assertEqual(parser.tables["Eagles"][0]["game_status"], "")

    def test_optional_source_failure_does_not_claim_current_status(self):
        feed=self.feed(self.summary()); old=feed._fetch
        def fetch(url,*a,**k):
            if "nfl.com" in url: raise RuntimeError("Unavailable")
            return old(url,*a,**k)
        feed._fetch=fetch;g=feed.pregame("401872981")
        self.assertEqual(g["official_practice_report"], {"home": None, "away": None})
        self.assertIsNone(g["weather"])
        self.assertNotIn("official_practice_report",g["evidence"])


class RuntimeTests(unittest.TestCase):
    def test_existing_benchmark_and_promotion_gates_unchanged(self):
        self.assertEqual(v.HARNESS_VERSION,"sports-validation-v20-bounded-revision")
        with v.app.app_context(): data=v.status().get_json()
        self.assertEqual(data["sports_harness_version"],v.HARNESS_VERSION)
        self.assertFalse(data["automatic_skill_activation_enabled"])
        self.assertFalse(data["sports_profitability_proven"])
        self.assertFalse(data["sports_wager_execution_enabled"])

    def test_every_paper_category_is_protected_from_general_edit_delete(self):
        for category in (PAPER_PREDICTIONS, PAPER_RESULTS, PAPER_QUOTES):
            with self.subTest(category=category), patch.object(v.base,"get_memory",return_value={"category":category}):
                with self.assertRaises(ValueError): v.base.patch_memory_raw(1,"rewrite")
                with self.assertRaises(ValueError): v.base.delete_memory(1)

    def test_route_rejects_extra_arguments_and_uses_paper_service(self):
        payload,code=v.handle_message('sports paper analyze :: {"event_id":"401872981", "url":"https://example.com"}')
        self.assertEqual(code,409)
        with patch.object(v.PAPER_TRIAL,"analyze",return_value={"trial_status":"not_started"}) as call:
            payload,code=v.handle_message('sports paper analyze :: {"event_id":"401872981"}')
            call.assert_called_once_with("401872981")
        self.assertEqual(code,200)

    def test_forecast_pins_provider_and_complete_response_without_profile_changes(self):
        def complete(messages,**kwargs):
            self.assertEqual(v.provider._TRAINING_PROVIDER_CONTEXT.get(),"gemini")
            self.assertTrue(v.provider._REQUIRE_FINISHED_RESPONSE_CONTEXT.get())
            self.assertTrue(kwargs["json_mode"])
            self.assertIn("uncalibrated",messages[0]["content"])
            return json.dumps(forecast())
        with patch.object(v.ENGINE,"complete",side_effect=complete): self.assertEqual(v.forecast(game()),forecast())
        self.assertIsNone(v.provider._TRAINING_PROVIDER_CONTEXT.get())

    def test_paper_chat_requires_existing_authentication(self):
        response=v.app.test_client().post("/ui/chat",json={"message":"show sports paper trial"})
        self.assertEqual(response.status_code,401)


if __name__ == "__main__": unittest.main()
