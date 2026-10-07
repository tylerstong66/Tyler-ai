import json
import types
import unittest
from fractions import Fraction
from unittest.mock import patch

import app_v2_19_3_15 as v
from sports_answer_audit import audit_answer
from sports_input_metrics import calculate
from sports_validation import SportsValidation
from skill_lab import SkillPromotionLab
from test_v2_18_skill_lab import FakeEngine, MemoryStore


EXPLANATION = {"decision": "NO BET", "rationale": "The supplied estimate alone cannot justify a live bet.",
               "uncertainty": "Current inputs and calibration evidence are missing."}


class InputMathTests(unittest.TestCase):
    def test_independent_fraction_arithmetic_across_prices_and_pushes(self):
        for odds in (-310, -165, -101, 100, 145, 260, 725):
            for win, push in ((Fraction(3, 10), Fraction(0)), (Fraction(2, 5), Fraction(1, 20)), (Fraction(3, 5), Fraction(1, 10))):
                with self.subTest(odds=odds, win=win, push=push):
                    m = calculate(json.dumps({"odds": odds, "p_win": float(win), "p_push": float(push)}))["metrics"]
                    decimal = 1 + (Fraction(odds, 100) if odds > 0 else Fraction(100, -odds))
                    self.assertAlmostEqual(m["implied_probability"], float(1 / decimal))
                    self.assertAlmostEqual(m["conditional_probability"], float(win / (1 - push)))
                    self.assertAlmostEqual(m["expected_profit_per_unit"], float(win * decimal + push - 1))
                    self.assertAlmostEqual(m["edge_percentage_points"], float(100 * (win / (1 - push) - 1 / decimal)))
                    self.assertIsNone(m["opposite_implied_probability"])
                    self.assertIsNone(m["no_vig_probability"])

    def test_opposing_prices_must_be_explicit_same_market(self):
        m = calculate('{"market_type":"two_way","odds":-140,"opposite_odds":125}')["metrics"]
        self.assertAlmostEqual(m["no_vig_probability"], float(Fraction(7, 12) / (Fraction(7, 12) + Fraction(4, 9))))
        with self.assertRaises(ValueError):
            calculate('{"odds":-140,"opposite_odds":125}')
        self.assertIsNone(calculate("Selected bet -140")["metrics"]["no_vig_probability"])

    def test_live_missing_push_withholds_ev_and_does_not_assume_zero(self):
        facts = calculate("A quote +145. Tyler estimates it hits 44%.")
        m = facts["metrics"]
        self.assertEqual(m["estimated_probability"], .44)
        for key in ("push_probability", "conditional_probability", "expected_profit_per_unit", "edge_percentage_points"):
            self.assertIsNone(m[key])
        self.assertTrue(facts["issues"])
        self.assertFalse(facts["assumptions"])

    def test_synthetic_assumption_is_explicit_and_separate(self):
        facts = calculate("A quote +145. Tyler estimates it hits 44%.", synthetic=True)
        self.assertEqual(facts["metrics"]["push_probability"], 0)
        self.assertIn("assumes no pushes", facts["assumptions"][0])
        self.assertAlmostEqual(facts["metrics"]["expected_profit_per_unit"], .078)

    def test_explicit_push_and_range_are_respected(self):
        m = calculate("-160 odds; estimated win probability 0.60 with range 0.55 to 0.65; push 0.04.")["metrics"]
        self.assertEqual(m["push_probability"], .04)
        self.assertEqual(m["estimated_probability_low"], .55)
        self.assertAlmostEqual(m["lower_bound_edge_percentage_points"], 100 * (.55 / .96 - 160 / 260))

    def test_changed_price_roles_and_ambiguous_prices(self):
        m = calculate("Over 31.5 at -115 earlier. It is now Over 34.5 at -130.")["metrics"]
        self.assertAlmostEqual(m["previous_implied_probability"], 115 / 215)
        self.assertAlmostEqual(m["implied_probability"], 130 / 230)
        self.assertIsNone(m["estimated_probability"])
        facts = calculate("Prices -140 and +125 from unrelated games.")
        self.assertTrue(facts["issues"])
        self.assertTrue(all(value is None for value in facts["metrics"].values()))

    def test_sample_record_and_leg_probability_do_not_create_win_estimate(self):
        for text in ("A record of 9-3 proves value.", "Three legs each have 70% probability, payout +650.", "Went over in five straight games."):
            self.assertIsNone(calculate(text, synthetic=True)["metrics"]["estimated_probability"])

    def test_invalid_and_conflicting_inputs_fail_closed(self):
        for data in ({"odds": -140.5}, {"odds": True}, {"odds": -99}, {"p_win": 58},
                     {"p_win": .8, "p_push": .3}, {"p_win": .5, "p_low": .6, "p_high": .8},
                     {"p_win": .5, "p_push": .1, "p_loss": .5}, {"implied_probability": 0},
                     {"odds": -140, "implied_probability": .4}, {"p_push": 1}, {"p_win": float("nan")}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                calculate(json.dumps(data))
        for text in ('{"odds":-140,"odds":125}', '{"odds":', '[125]', "win 0.5; win 0.6", "win 0.6 push 0.1 with no pushes"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                calculate(text)

    def test_supplied_implied_probability_supports_calculation(self):
        m = calculate("The sportsbook implies 60% and Tyler estimates 65%; no pushes.")["metrics"]
        self.assertAlmostEqual(m["expected_profit_per_unit"], .65 / .6 - 1)
        self.assertIsNone(m["no_vig_probability"])

    def test_fractional_and_percentage_quotes_are_not_american_odds(self):
        for text in ("Not odds: -140.5", "An unrelated change is +150%"):
            self.assertIsNone(calculate(text)["metrics"]["implied_probability"])


class ApplicationMathTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()["skill"]
        self.lab._context = types.MethodType(v.harness.previous._sports_context, self.lab)
        self.lab._run = types.MethodType(v._run, self.lab)
        self.lab._judge = types.MethodType(v.harness._judge, self.lab)
        self.engine.complete = lambda *args, **kw: json.dumps(EXPLANATION)

    def test_model_explains_but_application_supplies_metrics_and_provenance(self):
        seen = {}
        def complete(messages, **kwargs):
            seen.update(kwargs)
            seen["prompt"] = messages[0]["content"]
            seen["thinking"] = v.provider._SPORTS_THINKING_CONTEXT.get()
            return json.dumps(EXPLANATION)
        self.engine.complete = complete
        result = json.loads(self.lab._run(self.profile, "A quote +145. Tyler estimates it hits 44%."))
        self.assertAlmostEqual(result["metrics"]["expected_profit_per_unit"], .078)
        self.assertEqual(result["calculation_assumptions"], ["Synthetic lab calculation assumes no pushes; not verified for a live market."])
        self.assertIn("Application calculations", result["uncertainty"])
        self.assertIn("No other keys", seen["prompt"])
        self.assertEqual(seen["tokens"], 2400)
        self.assertEqual(seen["thinking"], "LOW")
        self.assertEqual(audit_answer(json.dumps(result))[1], [])

    def test_live_context_does_not_inherit_synthetic_push_assumption(self):
        token = v._LIVE_INPUT.set(True)
        try:
            result = json.loads(self.lab._run(self.profile, "A quote +145. Tyler estimates it hits 44%."))
        finally:
            v._LIVE_INPUT.reset(token)
        self.assertIsNone(result["metrics"]["expected_profit_per_unit"])
        self.assertEqual(audit_answer(json.dumps(result), input_text="A quote +145. Tyler estimates it hits 44%.")[1], [])
        result["metrics"]["expected_profit_per_unit"] = .078
        self.assertIn("push_unknown_requires_unknown_calculations", audit_answer(json.dumps(result), input_text="exercise")[1])

    def test_model_generated_metrics_are_rejected_not_repaired(self):
        self.engine.complete = lambda *a, **kw: json.dumps(dict(EXPLANATION, metrics={"expected_profit_per_unit": 9}))
        with self.assertRaisesRegex(RuntimeError, "three-key"):
            self.lab._run(self.profile, "A quote -140")

    def test_numeric_prose_and_decision_gate_violation_rejected(self):
        for item in (dict(EXPLANATION, rationale="The edge is 10 percent."), dict(EXPLANATION, decision="VALUE CANDIDATE")):
            self.engine.complete = lambda *a, **kw: json.dumps(item)
            with self.assertRaises(RuntimeError):
                self.lab._run(self.profile, "A quote -140")

    def test_model_failure_does_not_advance_checkpoint_or_activate_profile(self):
        validator = SportsValidation(self.lab, self.store.get_rows, self.store.save_row, "gemini", "fixture-model", lambda: "now")
        validator.start()
        before = self.engine.get_skill(self.profile["skill_id"])
        self.engine.complete = lambda *a, **kw: json.dumps(dict(EXPLANATION, metrics={}))
        with self.assertRaises(RuntimeError):
            validator.advance()
        self.assertEqual(validator.latest()["completed_cases"], 0)
        self.assertEqual(self.engine.get_skill(self.profile["skill_id"]), before)

    def test_invalid_input_causes_no_model_call(self):
        self.engine.complete = lambda *a, **kw: self.fail("Invalid input must fail before calling a model")
        with self.assertRaises(ValueError):
            self.lab._run(self.profile, '{"odds":true}')

    def test_live_context_is_reset_on_failure(self):
        with patch.object(v.ENGINE, "get_skill", return_value=self.profile), patch.object(v.SKILL_LAB, "_run", side_effect=RuntimeError("failure")):
            with self.assertRaises(RuntimeError):
                v._engine_run(v.ENGINE, "Sports Betting Analyst", "exercise")
        self.assertFalse(v._LIVE_INPUT.get())

    def test_positive_ev_erased_by_juice_claim_fails_objective_audit(self):
        result = json.loads(self.lab._run(self.profile, '{"odds":145,"p_win":0.44,"p_push":0}'))
        result["rationale"] = "The positive edge is erased by standard juice."
        self.assertIn("positive_ev_rationale_double_counts_vig", audit_answer(json.dumps(result))[1])

    def test_status_and_identity_disclose_new_application_harness(self):
        validator = SportsValidation(self.lab, self.store.get_rows, self.store.save_row, "gemini", "fixture-model", lambda: "now")
        identity = validator.identity()[2]
        self.assertEqual(identity["harness_version"], v.HARNESS_VERSION)
        with v.app.app_context():
            status = v.status().get_json()
        self.assertTrue(status["sports_application_owned_math"])
        self.assertFalse(status["sports_live_push_assumption_enabled"])
        self.assertFalse(status["automatic_skill_activation_enabled"])


if __name__ == "__main__":
    unittest.main()
