"""Regression gates for GPTAuto consumer deploy decisions."""
import unittest

from gptauto.smart_update import plan_update

A = "a" * 40
B = "b" * 40


class SmartUpdateTests(unittest.TestCase):
    def check(self, repo, files):
        return plan_update(repo, A, B, files)

    def test_chat2api_python_runtime_hotfix(self):
        p = self.check("chat2api", [("M", "app/request_recovery_patch.py")])
        self.assertEqual(p.mode, "runtime-hotfix")
        self.assertEqual(p.required_checks, ("CI",))
        self.assertTrue(p.manual_deploy_only)

    def test_dependency_requires_image(self):
        p = self.check("chat2api", [("M", "requirements.txt"),
                                   ("M", "app/request_recovery_patch.py")])
        self.assertEqual(p.mode, "verified-image")

    def test_worker_bundle_requires_image(self):
        p = self.check("chat2api", [("M", "chrome_extension/content.js")])
        self.assertTrue(p.full_build_required)

    def test_updater_is_not_self_hotpatched(self):
        p = self.check("chat2api", [("M", "app/server_update_patch.py")])
        self.assertEqual(p.mode, "verified-image")

    def test_qnbot_runtime_static(self):
        p = self.check("qnbot", [("M", "services/api-control-plane/static/version-update.js")])
        self.assertEqual(p.mode, "runtime-hotfix")

    def test_qnbot_client_build(self):
        p = self.check("qnbot", [("M", "src/Bot/Update/BotAutoUpdater.ps1")])
        self.assertEqual(p.mode, "client-build")

    def test_qnbot_mixed_changes(self):
        p = self.check("qnbot", [
            ("M", "src/Bot/Update/BotAutoUpdater.ps1"),
            ("M", "services/api-control-plane/static/version-update.js")])
        self.assertEqual(p.mode, "verified-image")
        self.assertIn("Windows x64 release build", p.required_checks)

    def test_mv3c_official_image_proof_preserved(self):
        p = self.check("mv3c", [("M", "api/server/index.js")])
        self.assertEqual(p.mode, "verified-image")
        self.assertIn("mv3c source Docker build", p.required_checks)

    def test_docs_do_not_deploy(self):
        p = self.check("mv3c", [("M", "docs/README.md")])
        self.assertEqual(p.mode, "checks-only")

    def test_gptauto_managed_workflows_are_checks_only_for_all_consumers(self):
        paths = [
            ("M", ".github/workflows/gptauto-sync.yml"),
            ("M", ".github/workflows/gptauto-observer.yml"),
            ("M", ".github/gptauto/smart_update.py"),
            ("A", ".github/GPTAUTO_SMART_UPDATE.md"),
        ]
        for repo in ("chat2api", "qnbot", "mv3c"):
            with self.subTest(repo=repo):
                plan = self.check(repo, paths)
                self.assertEqual(plan.mode, "checks-only")
                self.assertFalse(plan.full_build_required)
                self.assertTrue(plan.required_checks)

    def test_real_product_workflows_and_dependencies_still_require_image(self):
        examples = {
            "chat2api": "requirements.txt",
            "qnbot": ".github/workflows/api-control-plane-ci.yml",
            "mv3c": ".github/workflows/mv3c-build.yml",
        }
        for repo, path in examples.items():
            with self.subTest(repo=repo):
                plan = self.check(repo, [("M", path)])
                self.assertEqual(plan.mode, "verified-image")

    def test_refuse_deleted_runtime_and_unclassified(self):
        p = self.check("chat2api", [("D", "app/models.py")])
        self.assertEqual(p.mode, "verified-image")
        self.assertEqual(self.check("chat2api", [("M", "mystery.bin")]).mode,
                         "verified-image")

    def test_invalid_sha_and_unsafe_path(self):
        with self.assertRaises(ValueError):
            plan_update("qnbot", "main", B, [])
        with self.assertRaises(ValueError):
            self.check("qnbot", [("M", "../escape.py")])

    def test_no_op(self):
        self.assertEqual(plan_update("chat2api", A, A, []).mode, "no-op")
        with self.assertRaises(ValueError):
            plan_update("chat2api", A, A, [("M", "app/models.py")])


if __name__ == "__main__":
    unittest.main()
