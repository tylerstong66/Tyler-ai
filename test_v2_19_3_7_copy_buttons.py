import unittest

import app_v2_19_3_7 as v21937


class AssistantCopyButtonTests(unittest.TestCase):
    def test_copy_button_ui_is_installed(self):
        template = v21937.base.CHAT_HTML
        self.assertIn("function attachCopyButton", template)
        self.assertIn('if(who === "assistant")', template)
        self.assertIn("navigator.clipboard.writeText", template)
        self.assertIn('document.execCommand("copy")', template)
        self.assertIn('aria-label","Copy Tyler AI response', template)

    def test_copy_button_is_assistant_only_and_safe(self):
        template = v21937.base.CHAT_HTML
        self.assertEqual(template.count('if(who === "assistant")'), 2)
        self.assertNotIn("copyButton.innerHTML", template)
        self.assertIn("button.textContent", template)
        self.assertIn("helper.remove()", template)

    def test_status_exposes_new_version_and_capability(self):
        response = v21937.app.test_client().get("/status")
        data = response.get_json()
        self.assertEqual(data["version_short"], "v2.19.3.7")
        self.assertIn("assistant_message_copy_buttons", data["capabilities"])

    def test_current_source_is_available_to_maintenance(self):
        self.assertIn("app_v2_19_3_7.py", v21937.EXECUTOR.safe_source_files_fn())


if __name__ == "__main__":
    unittest.main()
