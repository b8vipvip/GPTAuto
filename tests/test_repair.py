import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from gptauto.repair import apply_deterministic_repairs


class DeterministicRepairTests(unittest.TestCase):
    def test_version_sync_updates_declared_targets_only(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".git").mkdir()
            (repo / ".gptauto").mkdir()
            (repo / "manifest.json").write_text('{"version":"1.2.3"}\n', encoding="utf-8")
            (repo / "Cargo.toml").write_text('[package]\nname="demo"\nversion="1.2.2"\n', encoding="utf-8")
            rules = {
                "version_sync": [
                    {
                        "name": "product-version",
                        "source": {"file": "manifest.json", "regex": r'"version"\s*:\s*"([^"]+)"'},
                        "targets": [
                            {"file": "Cargo.toml", "regex": r'(?m)^version\s*=\s*"([^"]+)"'}
                        ],
                    }
                ]
            }
            (repo / ".gptauto" / "repair-rules.json").write_text(json.dumps(rules), encoding="utf-8")

            payload = apply_deterministic_repairs(repo, "version mismatch")
            self.assertIn('version="1.2.3"', (repo / "Cargo.toml").read_text())
            self.assertEqual(payload["fixers"][0]["status"], "changed")

    def test_version_sync_respects_log_trigger(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".git").mkdir()
            (repo / ".gptauto").mkdir()
            (repo / "a.txt").write_text("v=2.0.0\n")
            (repo / "b.txt").write_text("v=1.0.0\n")
            rules = {
                "version_sync": [
                    {
                        "name": "guarded",
                        "when_log_matches": ["VERSION_DRIFT"],
                        "source": {"file": "a.txt", "regex": r"v=([^\n]+)"},
                        "targets": [{"file": "b.txt", "regex": r"v=([^\n]+)"}],
                    }
                ]
            }
            (repo / ".gptauto" / "repair-rules.json").write_text(json.dumps(rules))
            payload = apply_deterministic_repairs(repo, "ordinary test failure")
            self.assertEqual((repo / "b.txt").read_text(), "v=1.0.0\n")
            self.assertEqual(payload["fixers"][0]["status"], "skipped")

    def test_formatter_is_only_invoked_from_matching_failure_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".git").mkdir()
            (repo / "Cargo.toml").write_text("[package]\nname='demo'\n")
            calls = []

            def runner(command, cwd):
                calls.append((command, cwd))
                return subprocess.CompletedProcess(command, 0, "formatted")

            payload = apply_deterministic_repairs(
                repo,
                "error: cargo fmt --all -- --check failed",
                runner=runner,
                tool_available=lambda _: True,
            )
            self.assertEqual(calls[0][0], ["cargo", "fmt", "--all"])
            self.assertTrue(any(item["name"] == "rustfmt" for item in payload["fixers"]))

    def test_malformed_rule_falls_through_without_raising(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".git").mkdir()
            (repo / ".gptauto").mkdir()
            (repo / ".gptauto" / "repair-rules.json").write_text('{"version_sync": {}}')
            payload = apply_deterministic_repairs(repo, "failure")
            self.assertTrue(payload["errors"])


if __name__ == "__main__":
    unittest.main()
