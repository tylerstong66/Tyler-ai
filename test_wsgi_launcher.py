import os
import subprocess
import sys
import unittest


class StableWsgiLauncherTests(unittest.TestCase):
    def run_launcher(self, module_marker="__unset__", check_root=False):
        env = os.environ.copy()
        if module_marker == "__unset__":
            env.pop("TYLER_APP_MODULE", None)
        else:
            env["TYLER_APP_MODULE"] = module_marker

        code = [
            "import wsgi",
            "print(wsgi.ACTIVE_MODULE)",
            "print(wsgi.VERSION_SHORT)",
            "assert wsgi.app is not None",
        ]
        if check_root:
            code.extend([
                "client = wsgi.app.test_client()",
                "response = client.get('/')",
                "print(response.status_code)",
                "assert response.status_code == 200",
                "assert b'Private assistant access' in response.data",
            ])

        return subprocess.run(
            [sys.executable, "-c", "; ".join(code)],
            env=env,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_default_is_current_stable_version(self):
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("app_v2_15", result.stdout)
        self.assertIn("v2.15.0", result.stdout)

    def test_explicit_current_version_loads(self):
        result = self.run_launcher("app_v2_15")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("app_v2_15", result.stdout)
        self.assertIn("v2.15.0", result.stdout)

    def test_unauthenticated_root_renders_login_page(self):
        result = self.run_launcher("app_v2_15", check_root=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("200", result.stdout)

    def test_arbitrary_python_module_is_rejected(self):
        result = self.run_launcher("os")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid TYLER_APP_MODULE", result.stderr)

    def test_path_traversal_is_rejected(self):
        result = self.run_launcher("../app_v2_15")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid TYLER_APP_MODULE", result.stderr)

    def test_missing_version_fails_closed(self):
        result = self.run_launcher("app_v99_99")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not exist", result.stderr)


if __name__ == "__main__":
    unittest.main()
