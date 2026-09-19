import unittest
from pathlib import Path


class ConsumerTemplateTests(unittest.TestCase):
    def test_observer_tracks_post_merge_and_release_events(self):
        text = Path("consumer-template/gptauto-observer.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_run:", text)
        self.assertIn("workflows: [CI, Release]", text)
        self.assertIn("release:", text)
        self.assertIn('commits/$HEAD_SHA/pulls', text)
        self.assertIn("A merged PR is VERIFY, not DONE", text)
        self.assertIn('select(.name == "Release" and .conclusion == "success")', text)
        self.assertIn('--release-conclusion "$RELEASE_CONCLUSION"', text)
        self.assertNotIn("\\${{", text)

    def test_sync_has_dedicated_token_and_policy_fallback(self):
        text = Path("consumer-template/gptauto-sync.yml").read_text(encoding="utf-8")
        self.assertIn("secrets.GPTAUTO_SYNC_TOKEN || github.token", text)
        self.assertIn("Allow GitHub Actions to create and approve pull requests", text)
        self.assertIn("PR creation blocked after branch sync", text)
        self.assertNotIn("\\${{", text)

    def test_executor_has_merge_and_repair_actions(self):
        text = Path("consumer-template/gptauto-executor.yml").read_text(encoding="utf-8")
        self.assertIn("Execute safe merge gate", text)
        self.assertIn("Emit repair request", text)
        self.assertIn("gptauto.executor", text)
        self.assertIn("PR head moved; refusing stale merge", text)
        self.assertNotIn("\\\\${{", text)

    def test_observer_hydrates_previous_artifact_for_cumulative_ledger(self):
        text = Path("consumer-template/gptauto-observer.yml").read_text(encoding="utf-8")
        self.assertIn("previous_artifact_id", text)
        self.assertIn("actions/artifacts?name=gptauto-$TASK_ID", text)

    def test_sync_installs_executor_workflow(self):
        text = Path("consumer-template/gptauto-sync.yml").read_text(encoding="utf-8")
        self.assertIn("gptauto-executor.yml", text)

if __name__ == "__main__":
    unittest.main()
