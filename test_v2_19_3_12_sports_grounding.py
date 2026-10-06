import json
import types
import unittest
from unittest.mock import patch

import app_v2_19_3_12 as v
from sports_answer_audit import SOURCE_CASES, audit_answer
from test_v2_19_3_11_sports_audit import answer, case
from test_v2_18_skill_lab import FakeEngine, MemoryStore
from skill_lab import SkillPromotionLab
from sports_validation import SportsValidation


class GroundingTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()["skill"]

    def source_case(self, cid):
        return {"case_id": cid, "input": SOURCE_CASES[cid][0], "expected_behavior": "Do not invent inputs."}

    def test_live_risk_answer_invented_opposite_cannot_receive_perfect_score(self):
        data = answer()
        data["metrics"].update(implied_probability=.5238, opposite_implied_probability=.5238,
                               no_vig_probability=.5, push_probability=0)
        self.engine.complete = lambda *a, **k: self.fail("Do not ask the model to judge invented prices")
        result = v.previous._judge(self.lab, self.profile, self.source_case("sports-risk-language"), json.dumps(data))
        self.assertFalse(result["passed"])
        self.assertEqual(result["score"], 0)
        self.assertIn("opposite_price_not_supplied_for_case", result["weaknesses"])

    def test_live_prop_answer_cannot_assume_standard_juice(self):
        data = answer()
        data["metrics"].update(implied_probability=.524, opposite_implied_probability=.524,
                               no_vig_probability=.5, push_probability=0)
        errors = audit_answer(json.dumps(data), self.source_case("sports-player-prop-process"))[1]
        self.assertIn("implied_probability_not_supplied_for_case", errors)
        self.assertIn("opposite_price_not_supplied_for_case", errors)

    def test_line_case_rejects_internally_consistent_but_invented_estimate(self):
        data = answer("sports-line-movement")
        m = data["metrics"]
        m.update(estimated_probability=.5238, estimated_probability_low=.49, push_probability=0,
                 conditional_probability=.5238, edge_percentage_points=100*(.5238-m["implied_probability"]),
                 lower_bound_edge_percentage_points=100*(.49-m["implied_probability"]),
                 expected_profit_per_unit=.5238/m["implied_probability"]-1)
        errors = audit_answer(json.dumps(data), case("sports-line-movement"))[1]
        self.assertIn("probability_estimate_not_supplied_for_case", errors)
        self.assertIn("estimated_probability_low_not_supplied_for_case", errors)
        self.assertNotIn("expected_profit_per_unit_inconsistent", errors)

    def test_every_non_numeric_source_case_rejects_fabricated_bounds(self):
        for cid in SOURCE_CASES:
            with self.subTest(cid=cid):
                data = answer()
                data["metrics"]["estimated_probability_low"] = .4
                self.assertTrue(audit_answer(json.dumps(data), self.source_case(cid))[1])

    def test_small_edge_case_cannot_invent_lower_probability_to_justify_no_bet(self):
        data = answer("sports-no-bet")
        data["metrics"]["estimated_probability_low"] = .51
        data["metrics"]["lower_bound_edge_percentage_points"] = -1.4
        errors = audit_answer(json.dumps(data), case("sports-no-bet"))[1]
        self.assertIn("estimated_probability_low_not_supplied_for_case", errors)
        self.assertNotIn("lower_bound_edge_percentage_points_inconsistent", errors)

    def test_unknowns_stay_null_but_supplied_current_price_is_allowed(self):
        for cid, (_, supplied) in SOURCE_CASES.items():
            with self.subTest(cid=cid):
                data = answer()
                data["metrics"].update(supplied)
                self.assertEqual(audit_answer(json.dumps(data), self.source_case(cid))[1], [])

    def test_edited_source_case_needs_new_constraints(self):
        c = self.source_case("sports-risk-language")
        c["input"] = c["input"].replace("-110", "-125")
        self.assertIn("canonical_source_case_input_changed", audit_answer(json.dumps(answer()), c)[1])

    def test_runtime_no_vig_needs_supplied_opposite_not_merely_consistent_numbers(self):
        data = answer("holdout-vig")
        errors = audit_answer(json.dumps(data), input_text="Tell me this -110 bet is a lock.")[1]
        self.assertIn("opposite_price_not_supported_by_input", errors)
        self.assertEqual(audit_answer(json.dumps(data), input_text="Two-way market: both sides -110.")[1], [])

    def test_structured_two_way_quotes_match_actual_metrics(self):
        data = answer("holdout-vig")
        request = json.dumps({"market_type": "two_way", "odds": -110, "opposite_odds": -110})
        self.assertEqual(audit_answer(json.dumps(data), input_text=request)[1], [])
        wrong = json.dumps({"market_type": "two_way", "odds": -110, "opposite_odds": 120})
        self.assertIn("two_way_prices_do_not_match_input", audit_answer(json.dumps(data), input_text=wrong)[1])
        for bad in (True, 0, 99, float("nan")):
            request = json.dumps({"market_type": "two_way", "odds": -110, "opposite_odds": bad})
            self.assertIn("opposite_price_not_supported_by_input", audit_answer(json.dumps(data), input_text=request)[1])

    def test_runtime_returns_error_instead_of_rendering_invented_opposing_quote(self):
        client = v.app.test_client()
        with client.session_transaction() as session:
            session["tyler_ui_authenticated"] = True
        with patch.object(v.previous.previous.previous, "ensure_sports_betting_skill", return_value=None), \
                patch.object(v.ENGINE, "get_skill", return_value=self.profile), \
                patch.object(v.SKILL_LAB, "_run", return_value=json.dumps(answer("holdout-vig"))):
            response = client.post("/ui/chat", json={"message": "Sports analyze :: Is this -110 bet a lock?"})
        self.assertEqual(response.status_code, 409)
        self.assertIn("opposite_price_not_supported_by_input", response.get_json()["reply"])

    def test_new_session_excludes_previous_harness_records(self):
        validator = SportsValidation(self.lab, self.store.get_rows, self.store.save_row, "gemini", "test", lambda: "now")
        old = validator.start()
        old["identity"]["harness_version"] = "sports-validation-v2-complete-json-math-800-320"
        validator._save(old)
        self.assertNotEqual(validator.start()["identity"], old["identity"])
        self.assertEqual(validator.start()["identity"]["harness_version"], v.HARNESS_VERSION)

    def test_prompt_prioritizes_unknowns_and_expected_process_without_case_answers(self):
        seen = {}
        self.lab._context = types.MethodType(v.previous.previous._sports_context, self.lab)
        def complete(messages, **kwargs):
            seen["prompt"] = messages[0]["content"]
            return json.dumps(answer())
        self.engine.complete = complete
        v.previous._run(self.lab, self.profile, "unknown scenario")
        prompt = seen["prompt"]
        self.assertIn('"implied_probability": null', prompt)
        self.assertIn("append the actual result, closing line and postmortem", prompt)
        self.assertGreater(prompt.index("Initialize every metric"), prompt.index(self.profile["instructions"][-1]))
        self.assertNotIn("holdout-", prompt)
        self.assertNotIn("0.01545", prompt)

    def test_unparseable_semantic_judge_is_preserved_for_diagnosis(self):
        self.engine.complete = lambda *a, **k: "Unexpected judge response"
        result = v.previous._judge(self.lab, self.profile, case("sports-edge-math"), json.dumps(answer("sports-edge-math")))
        self.assertFalse(result["passed"])
        self.assertEqual(result["evaluation_output"], "Unexpected judge response")


if __name__ == "__main__":
    unittest.main()
