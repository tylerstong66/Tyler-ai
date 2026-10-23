import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sports_chat_nhl_evidence_manifest import compare_nhl_manifest


class NhlEvidenceManifestTests(unittest.TestCase):
    def test_missing_paths_fail_closed(self):
        result = compare_nhl_manifest({}, ".")
        self.assertEqual(result["status"], "unavailable")
        self.assertTrue(result["NO_BET"])

    def test_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            result = compare_nhl_manifest(
                {"prediction": "../outside.json", "entry_quote": "quote.json"}, root)
            self.assertEqual(result["status"], "unavailable")

    def test_tampered_json_is_rejected_by_original_gate(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, "prediction.json").write_text(json.dumps({"sha256": "tampered"}))
            Path(root, "quote.json").write_text(json.dumps({"sha256": "tampered"}))
            result = compare_nhl_manifest(
                {"prediction": "prediction.json", "entry_quote": "quote.json"}, root)
            self.assertEqual(result["status"], "unavailable")
            self.assertTrue(result["NO_BET"])

    def test_valid_json_is_forwarded_to_existing_verification(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, "prediction.json").write_text(json.dumps({"game_id": "synthetic"}))
            Path(root, "quote.json").write_text(json.dumps({"game_id": "synthetic"}))
            with patch("sports_chat_nhl_evidence_manifest.nhl_verified_chat_comparison",
                       return_value={"status": "unavailable", "NO_BET": True}) as gate:
                compare_nhl_manifest(
                    {"prediction": "prediction.json", "entry_quote": "quote.json"}, root,
                    now="2026-10-23T18:00:00Z")
            gate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
