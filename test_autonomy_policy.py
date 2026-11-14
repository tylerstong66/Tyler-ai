"""Tests for the opt-in, fail-closed Tyler AI self-improvement policy."""
import unittest

from autonomy_policy import assess_autonomous_change


class AutonomyPolicyTests(unittest.TestCase):
    def decision(self, action="open_pr", paths=None, **kw):
        return assess_autonomous_change(
            action=action,
            paths=["app_v2_19_3_39.py"] if paths is None else paths,
            **kw,
        )

    def test_default_disabled_even_for_low_risk(self):
        result = self.decision(action="create_branch")
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "autonomy_not_enabled")

    def test_can_propose_code_change_when_explicitly_enabled(self):
        self.assertTrue(self.decision(enabled=True)["allowed"])
        self.assertTrue(self.decision(action="run_tests", enabled=True)["allowed"])

    def test_high_impact_actions_always_require_approval(self):
        for action in ["deploy", "spend", "place_bet", "change_credentials",
                       "change_permissions", "change_safety_policy", "send_message"]:
            with self.subTest(action=action):
                self.assertFalse(self.decision(action=action, enabled=True)["allowed"])

    def test_no_automatic_production_merge(self):
        result = self.decision(
            action="merge", enabled=True, ci_passed=True,
            exact_head_verified=True, rollback_available=True,
            auto_deploy_disabled=True,
        )
        self.assertFalse(result["allowed"])

    def test_isolated_merge_requires_every_evidence_bit(self):
        path = ["docs/autonomy/overview.md"]
        for missing in ("ci_passed", "exact_head_verified", "rollback_available", "auto_deploy_disabled"):
            evidence = dict(ci_passed=True, exact_head_verified=True,
                            rollback_available=True, auto_deploy_disabled=True)
            evidence[missing] = False
            with self.subTest(missing=missing):
                self.assertFalse(self.decision(action="merge", paths=path, enabled=True, **evidence)["allowed"])
        self.assertTrue(self.decision(
            action="merge", paths=path, enabled=True,
            ci_passed=True, exact_head_verified=True,
            rollback_available=True, auto_deploy_disabled=True,
        )["allowed"])

    def test_no_self_revision_of_policy_or_workflows(self):
        for path in ("autonomy_policy.py", "test_autonomy_policy.py",
                     ".github/workflows/tests.yml", ".env", "config/.env.production",
                     "requirements.txt", "SPORTS_BETTING_V1_STATUS.md"):
            with self.subTest(path=path):
                self.assertFalse(self.decision(paths=[path], enabled=True)["allowed"])

    def test_path_aliases_and_traversal_are_rejected(self):
        for path in ("/tmp/file.py", "a/../autonomy_policy.py", "a//file.py",
                     "./file.py", "a\\b.py", "C:secret", "docs/autonomy/"):
            with self.subTest(path=path):
                self.assertFalse(self.decision(paths=[path], enabled=True)["allowed"])

    def test_no_external_side_effects_even_on_branch(self):
        self.assertFalse(self.decision(action="edit_branch", enabled=True,
                                       external_side_effects=True)["allowed"])

    def test_change_scope_is_bounded(self):
        self.assertFalse(self.decision(paths=[], enabled=True)["allowed"])
        self.assertFalse(self.decision(paths=["x.py"] * 2, enabled=True)["allowed"])
        self.assertFalse(self.decision(paths=[f"x{i}.py" for i in range(21)],
                                       enabled=True)["allowed"])

    def test_unknown_action_denied(self):
        self.assertFalse(self.decision(action="make_my_own_rules", enabled=True)["allowed"])


if __name__ == "__main__":
    unittest.main()
