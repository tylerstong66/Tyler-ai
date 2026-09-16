import os
import subprocess
import sys
import unittest


class StableWsgiLauncherTests(unittest.TestCase):
    def run_launcher(self, module_marker="__unset__"):
        env = os.environ.copy()
        if module_marker == "__unset__":
            env.pop("TYLER_APP_MODULE", None)
        else:
            env["TYLER_APP_MODULE"] = module_marker
        return subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import wsgi; "
                    "print(wsgi.ACTIVE_MODULE); "
                    "print(wsgi.VERSION_SHORT); "
                    "assert wsgi.app is not None"
                ),
            ],
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
