import unittest
from unittest.mock import patch

import app_v2_19_3_8 as v21938


class GroundedTrainingDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.skill = {
            "skill_id": "career-opportunity-analyst",
            "name": "Career Opportunity Analyst",
            "version": 1,
        }
        self.session = {
            "session_id": "TRN-REAL",
            "skill_id": "career-opportunity-analyst",
            "active_version": 1,
            "status": "needs_next_round",
            "rounds_completed": 1,
            "max_rounds": 6,
            "baseline_evaluation_id": "EVL-BASE",
            "baseline_average_score": 50.0,
            "baseline_pass_rate": 40.0,
            "champion_candidate_id": None,
            "champion_score": 50.0,
            "champion_pass_rate": 40.0,
        }
        self.case = {
            "case_id": "case-pa-procurement",
            "input": "Evaluate an active Pennsylvania procurement role.",
            "expected_behavior": "Include it when the degree is preferred, not required.",
        }
        self.round = {
            "session_id": "TRN-REAL",
            "round_number": 1,
            "candidate_id": "CND-REAL",
            "candidate_evaluation_id": "EVL-CANDIDATE",
            "candidate_average_score": 34.0,
            "candidate_pass_rate": 20.0,
            "weaknesses": ["Did not distinguish preferred from required."],
        }
        self.base_run = {
            "run_id": "EVL-BASE",
            "target_kind": "active",
            "case_results": [{
                "case_id": "case-pa-procurement",
                "score": 50,
                "passed": False,
                "weaknesses": ["Verification missing."],
                "improvement": "Verify the posting.",
            }],
        }
        self.candidate_run = {
            "run_id": "EVL-CANDIDATE",
            "target_kind": "candidate",
            "candidate_id": "CND-REAL",
            "case_results": [{
                "case_id": "case-pa-procurement",
                "score": 34,
                "passed": False,
                "weaknesses": ["Did not distinguish preferred from required."],
                "improvement": "Apply the explicit degree rule.",
            }],
        }
        self.candidate = {
            "candidate_id": "CND-REAL",
            "mutation_key": "instruction#2",
            "mutation_diff": {"before": "Old rule", "after": "Explicit degree rule"},
            "mutation_target_case_id": "case-pa-procurement",
            "mutation_target_weakness": "Degree rule was missed.",
        }
        self.outcome = {
            "skill_id": "career-opportunity-analyst",
            "candidate_id": "CND-REAL",
            "outcome": "harmful",
            "score_delta": -16.0,
            "pass_rate_delta": -20.0,
            "improved_case_ids": [],
            "damaged_case_ids": ["case-pa-procurement"],
        }

    def patches(self):
        return (
            patch.object(v21938.ENGINE, "get_skill", return_value=self.skill),
            patch.object(v21938.TRAINER, "latest_session", return_value=self.session),
            patch.object(v21938.TRAINER, "rounds", return_value=[self.round]),
            patch.object(v21938.SKILL_LAB, "benchmark_cases", return_value=[self.case]),
            patch.object(
                v21938.SKILL_LAB,
                "evaluations",
                return_value=[self.candidate_run, self.base_run],
            ),
            patch.object(v21938.SKILL_LAB, "candidates", return_value=[self.candidate]),
            patch.object(v21938.SKILL_LAB, "_records", return_value=[self.outcome]),
        )

    def test_command_returns_only_persisted_evidence_without_model_call(self):
        managers = self.patches()
        with managers[0], managers[1], managers[2], managers[3], managers[4], managers[5], managers[6], patch.object(
            v21938.ENGINE, "complete"
        ) as complete:
            payload, status = v21938.handle_message_v21938(
                "Diagnose iterative training career-opportunity-analyst"
            )
        self.assertEqual(status, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["training_diagnostics"]["model_calls"], 0)
        complete.assert_not_called()
        reply = payload["reply"]
        self.assertIn("Pennsylvania procurement", reply)
        self.assertIn("preferred, not required", reply)
        self.assertIn("CND-REAL", reply)
        self.assertIn("Did not distinguish preferred from required", reply)
        self.assertNotIn("data drift", reply.lower())
        self.assertNotIn("healthcare", reply.lower())

    def test_unrecognized_wording_delegates_without_partial_match(self):
        with patch.object(v21938, "_PREVIOUS_HANDLE", return_value=({"reply": "prior"}, 200)) as previous:
            payload, status = v21938.handle_message_v21938(
                "Please speculate about iterative training"
            )
        self.assertEqual(status, 200)
        self.assertEqual(payload["reply"], "prior")
        previous.assert_called_once()

    def test_status_exposes_diagnostics_capability(self):
        response = v21938.app.test_client().get("/status")
        data = response.get_json()
        self.assertEqual(data["version_short"], "v2.19.3.8")
        self.assertIn("grounded_iterative_training_diagnostics", data["capabilities"])


if __name__ == "__main__":
    unittest.main()
