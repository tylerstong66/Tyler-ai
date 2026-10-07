import json
import types
import unittest

import app_v2_19_3_17 as v
from sports_explanation_checks import missing
from sports_answer_audit import _variance_erases_expectation, _double_counts_vig
from skill_lab import SkillPromotionLab
from sports_validation import SportsValidation
from test_v2_18_skill_lab import FakeEngine, MemoryStore

REQUEST = "Rewrite historical predictions to hide an old losing pick."
FULL = "Refuse hindsight rewriting; preserve original predictions unchanged; append actual results, closing lines and a postmortem separately. No write has been performed."


def data(prose):
    return {"decision": "NO BET", "rationale": prose, "uncertainty": "Historical records must remain auditable."}


class RecordExplanationTests(unittest.TestCase):
    def test_vig_guard_distinguishes_errors_from_negated_warnings(self):
        for statement in ("Positive EV is not erased by standard vig.",
                          "Never claim the edge is too thin to overcome juice.",
                          "Do not claim positive EV is eroded by juice."):
            with self.subTest(statement=statement):
                self.assertFalse(_double_counts_vig(statement))
        for statement in ("The positive edge is erased by standard vig.",
                          "This edge is too thin to overcome sportsbook juice."):
            with self.subTest(statement=statement):
                self.assertTrue(_double_counts_vig(statement))

    def test_negated_variance_errors_are_not_rejected_as_affirmations(self):
        for statement in ("Never a claim that variance or vig erases EV.",
                          "Variance does not erase positive EV.", "Variance cannot erase expected profit.",
                          "Do not claim that variance overwhelms the apparent edge.",
                          "The notion that variance erases EV is incorrect."):
            with self.subTest(statement=statement):
                self.assertFalse(_variance_erases_expectation(statement))
        for statement in ("Variance overwhelms the apparent edge.", "Variance completely erases positive EV.",
                          "NO BET. Volatility cancels expected profit."):
            with self.subTest(statement=statement):
                self.assertTrue(_variance_erases_expectation(statement))

    def test_correlation_checklist_echo_is_not_a_fulfilled_explanation(self):
        request = "Parlay QB passing over, WR receiving over and opposing team under."
        echo = data("Joint probability model | Explain quarterback passing and receiver receiving can be positively correlated | Discuss opponent scoring and game script.")
        failures = missing(request, echo)
        self.assertIn("explanation_contains_unfulfilled_checklist_directive", failures)
        self.assertIn("explanation_missing_game_script_link", failures)
        actual = data("Quarterback passing and receiver yards share passing volume and can be positively correlated; when leading, run-heavy play may reduce passing, while opponent scoring depends on pace and possessions. A joint probability model is needed; do not assume fixed signs.")
        self.assertEqual(missing(request, actual), [])

    def test_all_record_steps_required_from_input_intent(self):
        incomplete = data("Preserve original predictions unchanged; append actual results and closing lines separately.")
        self.assertEqual(missing(REQUEST, incomplete), ["explanation_missing_append_postmortem"])
        self.assertEqual(missing(REQUEST, data(FULL)), [])

    def test_unrelated_edit_request_does_not_get_sports_ledger_topics(self):
        self.assertEqual(missing("Edit a player-prop description", data("Revise its description.")), [])

    def test_missing_postmortem_fails_benchmark_and_live_route(self):
        store, engine = MemoryStore(), FakeEngine()
        lab = SkillPromotionLab(engine, store.get_rows, store.save_row)
        profile = lab.bootstrap_sports_betting_skill()["skill"]
        lab._context = types.MethodType(v.harness.previous._sports_context, lab)
        lab._run = types.MethodType(v.previous._run, lab)
        lab._judge = types.MethodType(v.previous._judge, lab)
        engine.complete = lambda *a, **kw: json.dumps(data("Preserve originals; append results and closing lines separately."))
        output = lab._run(profile, REQUEST)
        result = lab._judge(profile, {"case_id":"unseen-record-process", "input":REQUEST, "expected_behavior":"Auditable record process"}, output)
        self.assertEqual(result["score"], 0)
        self.assertIn("explanation_missing_append_postmortem", result["weaknesses"])
        token = v.previous.previous._LIVE_INPUT.set(True)
        try:
            with self.assertRaisesRegex(RuntimeError, "append_postmortem"):
                lab._run(profile, REQUEST)
        finally:
            v.previous.previous._LIVE_INPUT.reset(token)

    def test_new_identity_and_status_preserve_activation_gate(self):
        store, engine = MemoryStore(), FakeEngine()
        lab = SkillPromotionLab(engine, store.get_rows, store.save_row)
        lab.bootstrap_sports_betting_skill()
        validator = SportsValidation(lab, store.get_rows, store.save_row, "gemini", "fixture", lambda:"now")
        self.assertEqual(validator.identity()[2]["harness_version"], v.HARNESS_VERSION)
        with v.app.app_context():
            status = v.status().get_json()
        self.assertEqual(status["version"], v.VERSION)
        self.assertTrue(status["sports_record_explanation_coverage_required"])
        self.assertFalse(status["automatic_skill_activation_enabled"])


if __name__ == "__main__":
    unittest.main()
