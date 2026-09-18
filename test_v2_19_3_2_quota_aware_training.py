import unittest

import app_v2_19_3_2 as v21932


class FakeExampleEngine:
    def examples_for_skill(self, skill_id, limit):
        self.request = (skill_id, limit)
        return [{
            "input": "x" * 1000,
            "ideal_output": "y" * 2000,
        }]


class FakeLab:
    def __init__(self):
        self.engine = FakeExampleEngine()


class QuotaAwareTrainingTests(unittest.TestCase):
    def setUp(self):
        v21932._QUOTA_BLOCKED_UNTIL = 0.0
        v21932._QUOTA_WAIT_SECONDS = 0

    def test_compact_context_is_bounded_and_keeps_profile_controls(self):
        lab = FakeLab()
        profile = {
            "skill_id": "test-skill",
            "name": "Test Skill",
            "purpose": "Safe developer work " * 100,
            "version": 1,
            "allowed_tools": ["reason", "github"],
            "instructions": ["Inspect current code " * 60 for _ in range(20)],
            "success_criteria": ["Only verified claims " * 60 for _ in range(20)],
        }
        context = v21932._compact_benchmark_context(lab, profile)
        self.assertLessEqual(len(context), 4200)
        self.assertIn("ALLOWED TOOLS: reason, github", context)
        self.assertIn("INSTRUCTIONS:", context)
        self.assertIn("SUCCESS CRITERIA:", context)
        self.assertEqual(lab.engine.request, ("test-skill", 1))

    def test_output_budget_is_reduced_without_weakening_safety_gates(self):
        self.assertLessEqual(
            v21932.ITERATIVE_BENCHMARK_OUTPUT_BUDGET
            + v21932.ITERATIVE_CANDIDATE_OUTPUT_TOKENS,
            770,
        )
        self.assertEqual(v21932.MAX_MUTATED_FIELDS, 1)
        status = v21932.TRAINER.status()
        self.assertFalse(status["automatic_activation"])
        self.assertTrue(status["human_promotion_required"])

    def test_daily_quota_error_is_sanitized_and_starts_local_cooldown(self):
        original = v21932._ORIGINAL_SKILL_COMPLETE

        def limited(*args, **kwargs):
            raise RuntimeError(
                "Rate limit reached for model in organization org_secret on "
                "tokens per day (TPD). Please try again in 1m33.7s."
            )

        try:
            v21932._ORIGINAL_SKILL_COMPLETE = limited
            with self.assertRaises(RuntimeError) as caught:
                v21932._quota_aware_complete([], tokens=120)
            first = str(caught.exception)
            self.assertIn("No training round was consumed", first)
            self.assertNotIn("org_secret", first)
            self.assertGreater(v21932._QUOTA_BLOCKED_UNTIL, 0)

            with self.assertRaises(RuntimeError) as second_caught:
                v21932._quota_aware_complete([], tokens=120)
            self.assertIn("current session is preserved", str(second_caught.exception))
        finally:
            v21932._ORIGINAL_SKILL_COMPLETE = original

    def test_non_quota_errors_are_unchanged(self):
        original = v21932._ORIGINAL_SKILL_COMPLETE

        def broken(*args, **kwargs):
            raise RuntimeError("unrelated provider failure")

        try:
            v21932._ORIGINAL_SKILL_COMPLETE = broken
            with self.assertRaisesRegex(RuntimeError, "unrelated provider failure"):
                v21932._quota_aware_complete([], tokens=120)
        finally:
            v21932._ORIGINAL_SKILL_COMPLETE = original

    def test_source_inventory_contains_new_layer(self):
        self.assertEqual(v21932.VERSION_SHORT, "v2.19.3.2")
        self.assertIn("app_v2_19_3_2.py", v21932.EXECUTOR.safe_source_files_fn())


if __name__ == "__main__":
    unittest.main()
