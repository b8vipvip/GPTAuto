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


if __name__ == "__main__":
    unittest.main()
