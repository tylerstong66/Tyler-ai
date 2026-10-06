import json
import unittest
from unittest.mock import patch

import app_v2_19_3_10 as v
from test_sports_betting import snapshot, NOW
from test_v2_18_skill_lab import MemoryStore, FakeEngine
from skill_lab import SkillPromotionLab


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.profile = self.lab.bootstrap_sports_betting_skill()["skill"]

    def test_full_profile_preserves_final_two_safety_instructions(self):
        context = v._sports_context(self.lab, self.profile)
        for instruction in self.profile["instructions"]:
            self.assertIn(instruction, context)
        self.assertIn("Do not place wagers", context)
        self.assertIn("Do not imply guaranteed profit", context)

    def test_answer_budget_is_per_case_and_provider_context_restored(self):
        seen = {}
        def complete(messages, **kwargs):
            seen.update(kwargs)
            seen["provider"] = v.provider._TRAINING_PROVIDER_CONTEXT.get()
            return "answer"
        self.engine.complete = complete
        self.lab._context = lambda profile: "all instructions"
        self.lab._benchmark_run_tokens = 25
        self.assertEqual(v._sports_run(self.lab, self.profile, "test"), "answer")
        self.assertEqual(seen["tokens"], 400)
        self.assertEqual(seen["provider"], "gemini")
        self.assertIsNone(v.provider._TRAINING_PROVIDER_CONTEXT.get())

    def test_unparseable_judge_fails_closed(self):
        self.engine.complete = lambda *a, **k: "Looks great, passed!"
        case = self.lab.benchmark_cases("Sports Betting Analyst")[0]
        judged = v._sports_judge(self.lab, self.profile, case, "candidate output")
        self.assertFalse(judged["passed"])
        self.assertEqual(judged["score"], 0)

    def test_general_memory_edit_and_delete_cannot_rewrite_sports_records(self):
        with patch.object(v.base, "get_memory", return_value={"id": 1, "category": "sports_prediction"}), \
                patch.object(v, "_OLD_PATCH") as edit, patch.object(v, "_OLD_DELETE") as delete:
            with self.assertRaises(ValueError):
                v._protected_patch(1, "replace losing prediction")
            with self.assertRaises(ValueError):
                v._protected_delete(1)
            edit.assert_not_called()
            delete.assert_not_called()

    def test_private_chat_still_requires_authentication(self):
        with patch.object(v.previous, "ensure_sports_betting_skill", return_value=None):
            response = v.app.test_client().post("/ui/chat", json={"message": "show sports ledger"})
        self.assertEqual(response.status_code, 401)

    def test_structured_evaluate_route_calls_no_model_or_storage(self):
        with patch.object(v, "evaluate_snapshot", return_value={"decision": "NO BET"}), patch.object(v.ENGINE, "complete") as complete:
            payload, code = v.handle_message("sports evaluate :: " + json.dumps(snapshot()))
        self.assertEqual(code, 200)
        self.assertEqual(payload["sports"]["decision"], "NO BET")
        complete.assert_not_called()

    def test_old_harness_training_cannot_silently_resume(self):
        with patch.object(v.TRAINER, "latest_session", return_value={"harness_version": "old"}), patch.object(v, "_OLD_ADVANCE") as advance:
            with self.assertRaises(ValueError):
                v._training_advance(v.TRAINER, "sports-betting-analyst")
            advance.assert_not_called()

    def test_authenticated_chat_runs_real_math_without_model(self):
        client = v.app.test_client()
        with client.session_transaction() as session:
            session["tyler_ui_authenticated"] = True
        # Freeze only the wall clock: exercise the actual route and calculator.
        with patch.object(v.previous, "ensure_sports_betting_skill", return_value=None), \
                patch.object(v, "evaluate_snapshot", side_effect=lambda data: __import__("sports_betting").evaluate_snapshot(data, NOW)), \
                patch.object(v.ENGINE, "complete") as complete:
            response = client.post("/ui/chat", json={"message": "sports evaluate :: " + json.dumps(snapshot())})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["sports"]
        self.assertEqual(data["decision"], "VALUE CANDIDATE")
        self.assertAlmostEqual(data["edge_percentage_points"], 7)
        self.assertFalse(data["wager_executed"])
        complete.assert_not_called()

    def test_runtime_sports_answer_routes_to_same_lab_path(self):
        with patch.object(v.ENGINE, "get_skill", return_value=self.profile), \
                patch.object(v.SKILL_LAB, "_run", return_value="NO BET") as run:
            self.assertEqual(v.ENGINE.run_skill("Sports Betting Analyst", "current odds unavailable"), "NO BET")
            run.assert_called_once_with(self.profile, "current odds unavailable")


if __name__ == "__main__":
    unittest.main()
