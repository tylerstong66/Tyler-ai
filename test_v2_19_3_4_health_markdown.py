import unittest

import app_v2_19_3_4 as v21934


class HealthMarkdownReleaseTests(unittest.TestCase):
    def test_release_version_and_source_grounding(self):
        self.assertEqual(v21934.VERSION_SHORT, "v2.19.3.4")
        self.assertIn("app_v2_19_3_4.py", v21934.EXECUTOR.safe_source_files_fn())

    def test_ui_uses_safe_dom_markdown_renderer(self):
        template = v21934.base.CHAT_HTML
        self.assertIn("function renderMarkdown(parent,text)", template)
        self.assertIn("appendInlineMarkdown", template)
        self.assertIn("renderMarkdown(body,text)", template)
        self.assertNotIn("body.innerHTML", template)
        self.assertNotIn("marked.min.js", template)

    def test_ui_supports_expected_markdown_blocks(self):
        template = v21934.base.CHAT_HTML
        self.assertIn("isTableDivider", template)
        self.assertIn('document.createElement("pre")', template)
        self.assertIn('document.createElement(ordered ? "ol" : "ul")', template)
        self.assertIn('document.createElement("h" + heading[1].length)', template)

    def test_status_exposes_release_capabilities(self):
        response = v21934.app.test_client().get("/status")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["version_short"], "v2.19.3.4")
        self.assertIn("operation_checkpoint_health_history", data["capabilities"])
        self.assertIn("safe_markdown_chat_ui", data["capabilities"])


if __name__ == "__main__":
    unittest.main()
