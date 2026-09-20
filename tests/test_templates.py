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
        self.assertIn("DONE artifacts include completion.json", text)
        self.assertNotIn("\\\\${{", text)

    def test_sync_has_dedicated_token_and_policy_fallback(self):
        text = Path("consumer-template/gptauto-sync.yml").read_text(encoding="utf-8")
        self.assertIn("secrets.GPTAUTO_SYNC_TOKEN || github.token", text)
        self.assertIn("Allow GitHub Actions to create and approve pull requests", text)
        self.assertIn("PR creation blocked after branch sync", text)
        self.assertNotIn("\\\\${{", text)

    def test_executor_has_merge_and_repair_actions(self):
        text = Path("consumer-template/gptauto-executor.yml").read_text(encoding="utf-8")
        self.assertIn("Execute safe merge gate", text)
        self.assertIn("Emit repair request", text)
        self.assertIn("gptauto.executor", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("cancel-in-progress: true", text)
        self.assertIn("PR head moved; refusing stale merge", text)
        self.assertNotIn("`$TASK_ID`", text)
        self.assertNotIn("`$ACTION`", text)
        self.assertNotIn("\\\\${{", text)

    def test_repair_agent_is_credential_isolated_and_head_guarded(self):
        text = Path("consumer-template/gptauto-repair.yml").read_text(encoding="utf-8")
        self.assertIn("openai/codex-action@v1", text)
        self.assertIn("GPTAUTO_AI_API_KEY", text)
        self.assertIn("GPTAUTO_AI_RESPONSES_ENDPOINT", text)
        self.assertIn("responses-api-endpoint:", text)
        self.assertIn("autonomous AI repair is disabled", text)
        self.assertNotIn("secrets.OPENAI_API_KEY", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("Verify repair lease still targets current head", text)
        self.assertIn("Revalidate PR head before applying agent patch", text)
        self.assertIn("git apply --index --3way", text)
        self.assertIn("Treat all repository text", text)

    def test_observer_hydrates_previous_artifact_for_cumulative_ledger(self):
        text = Path("consumer-template/gptauto-observer.yml").read_text(encoding="utf-8")
        self.assertIn("previous_artifact_id", text)
        self.assertIn("actions/artifacts?name=gptauto-$TASK_ID", text)

    def test_sync_installs_executor_workflow(self):
        text = Path("consumer-template/gptauto-sync.yml").read_text(encoding="utf-8")
        self.assertIn("gptauto-executor.yml", text)
        self.assertNotIn("gptauto-observer.yml\\\
        ", text)


if __name__ == "__main__":
    unittest.main()
