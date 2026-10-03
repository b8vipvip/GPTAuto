import unittest
from pathlib import Path

from gptauto.observer import release_expected


class ReleaseIntentTests(unittest.TestCase):
    def test_technical_release_workflow_mentions_do_not_require_release(self):
        body = """Root cause: qnbot has a Windows x64 release build workflow.
The Reconcile path should validate the canonical CI and preserve the existing Release workflow behavior.
"""
        self.assertFalse(release_expected("fix: add canonical product CI for GPTAuto Reconcile", body))

    def test_explicit_body_release_directives_still_require_release(self):
        self.assertTrue(release_expected("fix: repair packaging", "Please publish after merge."))
        self.assertTrue(release_expected("fix: repair packaging", "Release required after CI is green."))
        self.assertTrue(release_expected("fix: repair packaging", "完成后正式发布"))

    def test_title_release_and_version_intent_remain_authoritative(self):
        self.assertTrue(release_expected("fix: publish stable release"))
        self.assertTrue(release_expected("v0.15.7: repair Reconcile permissions"))
        self.assertFalse(release_expected("chore: sync GPTAuto v0.15.7", "Release required after CI is green."))

    def test_reconcile_can_write_recovery_and_terminal_pr_receipts(self):
        text = Path("consumer-template/gptauto-reconcile.yml").read_text(encoding="utf-8")
        self.assertIn("pull-requests: write", text)
        self.assertIn("Publish post-merge recovery handoff", text)
        self.assertIn("Publish terminal foreground receipt", text)


if __name__ == "__main__":
    unittest.main()
