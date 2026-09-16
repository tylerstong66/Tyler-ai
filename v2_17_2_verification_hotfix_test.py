import copy
import unittest
from unittest import mock

import app_v2_17_2 as v2172


class ProductionVerificationHotfixTests(unittest.TestCase):
    def test_failed_record_can_recover_to_deployed_without_self_http(self):
        record = {
            "deployment_id": "DPL-516CA7D59A",
            "status": "verification_failed",
            "target_commit_sha": "4b151816666ac784c8b0a1cc6fea5d11777a85c5",
            "rollback_commit_sha": "08e2abb5efe18c24b40ab2afa91ef5eaba051879",
            "production_deployment_performed": False,
            "post_deploy_health_verified": False,
            "rollback_performed": False,
        }
        run = {
            "id": 35134009853,
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/tylerstong66/Tyler-ai/actions/runs/35134009853",
        }
        persisted = []

        with mock.patch.object(v2172.v2171, "_record", return_value=copy.deepcopy(record)), \
             mock.patch.object(v2172.v2171, "_find_run", return_value=run), \
             mock.patch.object(v2172.v2171, "_runtime_commit", return_value=record["target_commit_sha"]), \
             mock.patch.object(v2172.v2171, "_post", side_effect=lambda item: persisted.append(copy.deepcopy(item)) or True), \
             mock.patch.object(v2172.v2171.requests, "get") as self_http:
            result = v2172.verify_production("DPL-516CA7D59A")

        self.assertTrue(result["success"])
        self.assertTrue(result["terminal"])
        self.assertEqual(result["deployment"]["status"], "deployed")
        self.assertTrue(result["deployment"]["production_deployment_performed"])
        self.assertTrue(result["deployment"]["post_deploy_health_verified"])
        self.assertEqual(
            result["deployment"]["verification_source"],
            "external_workflow_plus_render_git_commit",
        )
        self.assertEqual(len(persisted), 1)
        self_http.assert_not_called()

    def test_runtime_mismatch_still_fails_closed(self):
        record = {
            "deployment_id": "DPL-AAAAAAAAAA",
            "status": "deployment_dispatched",
            "target_commit_sha": "1" * 40,
            "rollback_commit_sha": "2" * 40,
        }
        run = {"status": "completed", "conclusion": "success", "html_url": "https://example.invalid/run"}

        with mock.patch.object(v2172.v2171, "_record", return_value=copy.deepcopy(record)), \
             mock.patch.object(v2172.v2171, "_find_run", return_value=run), \
             mock.patch.object(v2172.v2171, "_runtime_commit", return_value="3" * 40), \
             mock.patch.object(v2172.v2171, "_post", return_value=True):
            result = v2172.verify_production("DPL-AAAAAAAAAA")

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "production_verification_failed")
        self.assertEqual(result["deployment"]["status"], "verification_failed")


if __name__ == "__main__":
    unittest.main()
