import copy
import json
import unittest
from unittest.mock import patch

import app_v2_19_3_13 as v
from sports_validation import SportsValidation, HOLDOUTS
from skill_lab import SkillPromotionLab
from test_v2_18_skill_lab import FakeEngine, MemoryStore


class CandidateCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.store, self.engine = MemoryStore(), FakeEngine()
        self.lab = SkillPromotionLab(self.engine, self.store.get_rows, self.store.save_row)
        self.active = self.lab.bootstrap_sports_betting_skill()["skill"]
        self.candidate = {
            "candidate_id": "CND-PENDING", "skill_id": self.active["skill_id"],
            "name": self.active["name"], "purpose": self.active["purpose"],
            "base_version": 1, "candidate_version": 2, "status": "candidate",
            "instructions": self.active["instructions"] + ["Never invent missing probabilities."],
            "success_criteria": self.active["success_criteria"], "allowed_tools": self.active["allowed_tools"],
        }
        self.calls = []
        self.lab._run = lambda profile, request: self.calls.append((profile["version"], request)) or "answer"
        self.lab._judge = lambda profile, case, answer: {"case_id": case["case_id"], "output": answer,
            "score": 100, "passed": True, "weaknesses": []}
        self.validator = SportsValidation(self.lab, self.store.get_rows, self.store.save_row,
            "gemini", "same-model", lambda: "now", candidate_fn=lambda: self.candidate)

    def test_start_pins_candidate_without_a_model_call_or_activation(self):
        before = copy.deepcopy(self.engine.get_skill(self.active["skill_id"]))
        result = self.validator.start()
        self.assertEqual(result["identity"]["candidate_id"], "CND-PENDING")
        self.assertEqual(result["identity"]["target_kind"], "candidate")
        self.assertEqual(result["profile_version"], 2)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.engine.get_skill(self.active["skill_id"]), before)

    def test_one_advance_runs_only_one_case_and_persists_it(self):
        self.validator.start()
        advanced = self.validator.advance()
        self.assertEqual(advanced["completed_cases"], 1)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][0], 2)
        self.assertEqual(self.validator.latest()["results"], advanced["results"])

    def test_provider_failure_does_not_advance_or_activate(self):
        self.validator.start()
        self.lab._run = lambda *a: (_ for _ in ()).throw(RuntimeError("provider quota"))
        with self.assertRaises(RuntimeError):
            self.validator.advance()
        self.assertEqual(self.validator.latest()["completed_cases"], 0)
        self.assertEqual(self.engine.get_skill(self.active["skill_id"])["version"], 1)

    def test_both_baselines_are_candidate_runs_and_holdouts_are_not_training_runs(self):
        self.validator.start()
        for _ in range(25):
            result = self.validator.advance()
        self.assertEqual(result["status"], "passed")
        self.assertFalse(result["profitability_proven"])
        runs = self.lab.evaluations(self.active["skill_id"], "candidate", 100)
        self.assertEqual(len(runs), 2)
        for run in runs:
            self.assertEqual(run["candidate_id"], "CND-PENDING")
            self.assertEqual(run["case_count"], 10)
            self.assertFalse(any(r["case_id"] in {h["case_id"] for h in HOLDOUTS} for r in run["case_results"]))
        self.assertEqual(self.engine.get_skill(self.active["skill_id"])["version"], 1)

    def test_active_and_candidate_checkpoints_remain_separate(self):
        active = SportsValidation(self.lab, self.store.get_rows, self.store.save_row, "gemini", "same-model", lambda: "now")
        saved = active.start()
        active.advance()
        candidate = self.validator.start()
        self.assertNotEqual(saved["validation_id"], candidate["validation_id"])
        self.assertEqual(active.latest()["completed_cases"], 1)
        self.assertNotIn("target_kind", active.latest()["identity"])

    def test_changed_candidate_cannot_silently_continue_old_checkpoint(self):
        old = self.validator.start()
        self.candidate["candidate_id"] = "CND-NEW"
        with self.assertRaises(ValueError):
            self.validator.advance()
        self.assertNotEqual(self.validator.start()["validation_id"], old["validation_id"])

    def test_missing_or_stale_candidate_is_rejected(self):
        for changed in (None, dict(self.candidate, base_version=99), dict(self.candidate, skill_id="other"), dict(self.candidate, candidate_version=1),
                        dict(self.candidate, status="promoted")):
            with self.subTest(candidate=changed):
                self.candidate = changed
                with self.assertRaises(ValueError):
                    self.validator.start()

    def test_identity_change_between_checkpoint_read_and_execution_fails_closed(self):
        self.validator.start()
        original = self.validator.identity
        calls = 0
        def identity():
            nonlocal calls
            calls += 1
            if calls == 2:
                self.candidate["instructions"] = ["changed"]
            return original()
        self.validator.identity = identity
        with self.assertRaises(ValueError):
            self.validator.advance()
        self.assertEqual(self.calls, [])

    def test_private_candidate_commands_still_require_sign_in(self):
        with patch.object(v.previous.previous.previous.previous, "ensure_sports_betting_skill", return_value=None):
            response = v.app.test_client().post("/ui/chat", json={"message": "Start sports candidate validation"})
        self.assertEqual(response.status_code, 401)

    def test_candidate_command_routes_use_only_candidate_validator(self):
        client = v.app.test_client()
        with client.session_transaction() as session:
            session["tyler_ui_authenticated"] = True
        with patch.object(v.previous.previous.previous.previous, "ensure_sports_betting_skill", return_value=None), \
                patch.object(v, "CANDIDATE_VALIDATOR", self.validator):
            response = client.post("/ui/chat", json={"message": "Start sports candidate validation"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("CND-PENDING", response.get_json()["reply"])
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
