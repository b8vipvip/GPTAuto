import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from gptauto.validation import run_targeted_validation, validation_plan


class ValidationTests(unittest.TestCase):
    def test_plan_targets_only_changed_language_families(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "native-core").mkdir()
            (repo / "native-core" / "Cargo.toml").write_text('[package]\nname="x"\nversion="0.1.0"\n', encoding="utf-8")
            (repo / "native-core" / "src").mkdir()
            files = ["native-core/src/lib.rs", "extension/a.js", "packaging/windows/x.ps1", "docs/readme.md"]
            plan = validation_plan(repo, files)
            self.assertEqual(plan["cargo_roots"], ["native-core"])
            self.assertEqual(plan["node"], ["extension/a.js"])
            self.assertEqual(plan["powershell"], ["packaging/windows/x.ps1"])
            self.assertNotIn("docs/readme.md", plan["node"])

    def test_fast_builtin_validation_catches_invalid_json(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)
            path = repo / "config.json"
            path.write_text(json.dumps({"ok": True}), encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            path.write_text("{broken", encoding="utf-8")
            result = run_targeted_validation(repo)
            self.assertFalse(result["passed"])
            self.assertIn("json:config.json", result["failed_checks"])


if __name__ == "__main__":
    unittest.main()
