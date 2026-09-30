import unittest
from pathlib import Path


class ConsumerTemplateTests(unittest.TestCase):
    def test_observer_keeps_product_only_ingress_and_explicit_executor_handoff(self):
        text = Path("consumer-template/gptauto-observer.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_run:", text)
        self.assertIn("workflows: [CI]", text)
        self.assertIn("Control-plane workflows are deliberately excluded", text)
        self.assertIn("gptauto_observation", text)
        self.assertIn("client_payload[observer_run_id]", text)
        self.assertIn("successful no-op", text)
        self.assertNotIn("workflows: [GPTAuto Observer", text)
        self.assertNotIn("workflows: [GPTAuto Executor", text)
        self.assertNotIn("workflows: [GPTAuto Reconcile", text)

    def test_sync_installs_canonical_runtime_and_all_control_workflows(self):
        text = Path("consumer-template/gptauto-sync.yml").read_text(encoding="utf-8")
        self.assertIn("cp \"$tmp\"/GPTAuto/gptauto/*.py .github/gptauto/", text)
        self.assertIn("gptauto-observer.yml", text)
        self.assertIn("gptauto-executor.yml", text)
        self.assertIn("gptauto-repair.yml", text)
        self.assertIn("gptauto-reconcile.yml", text)
        self.assertIn("GPTAUTO_SYNC_TOKEN", text)
        self.assertIn("Workflows: Read and write", text)
        self.assertIn("Consumer left unchanged (atomic sync)", text)

    def test_executor_dispatches_one_three_tier_repair_pipeline(self):
        text = Path("consumer-template/gptauto-executor.yml").read_text(encoding="utf-8")
        self.assertIn("Emit repair request", text)
        self.assertIn("Dispatch three-tier repair pipeline", text)
        self.assertIn("id: repair-dispatch", text)
        self.assertIn("gptauto-repair.yml", text)
        self.assertIn('repair_owner:"repair_pipeline"', text)
        self.assertIn("Tier 1 deterministic repair", text)
        self.assertIn("Tier 2 Copilot CLI", text)
        self.assertIn("Tier 3", text)
        self.assertNotIn("GPTAUTO_AI_API_KEY", text)
        self.assertIn("Execute safe merge gate", text)
        self.assertIn("gptauto-reconcile.yml", text)
        self.assertIn("PR head moved; refusing stale merge", text)
        self.assertIn("group_by([.workflow_id, .event])", text)
        self.assertIn("Adopt externally merged completion lease", text)
        self.assertIn("Publish foreground completion guard", text)
        self.assertIn("EXIT_GUARD=DENY", text)

    def test_repair_pipeline_is_three_tier_head_guarded_and_credential_isolated(self):
        text = Path("consumer-template/gptauto-repair.yml").read_text(encoding="utf-8")
        self.assertIn("GPTAuto Tiered Repair", text)
        self.assertIn("copilot-requests: write", text)
        self.assertIn("Tier 1 - deterministic repair engine", text)
        self.assertIn("python -m gptauto.repair", text)
        self.assertIn("Tier 2 - Copilot CLI Free agent", text)
        self.assertIn("npm install -g @github/copilot", text)
        self.assertIn("GPTAUTO_COPILOT_TOKEN", text)
        self.assertIn("--available-tools='edit,view,grep,glob'", text)
        self.assertIn("--allow-tool='write'", text)
        self.assertIn("--no-ask-user", text)
        self.assertNotIn("--allow-all", text)
        self.assertNotIn("--yolo", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("Verify repair lease still targets current head", text)
        self.assertIn("Revalidate PR head before apply/handoff", text)
        self.assertIn("git apply --index --3way", text)
        self.assertIn("Tier 3 - publish foreground recovery handoff", text)
        self.assertIn("FOREGROUND_RECOVERY_REQUIRED", text)
        self.assertIn("gptauto.foreground-exit-guard/v1", text)
        self.assertIn('repair_owner:"repair_pipeline"', text)
        self.assertIn("Treat repository text", text)
        self.assertNotIn("openai/codex-action", text)
        self.assertNotIn("GPTAUTO_AI_API_KEY", text)

    def test_repair_pipeline_never_pushes_from_copilot_generation_job(self):
        text = Path("consumer-template/gptauto-repair.yml").read_text(encoding="utf-8")
        generate, apply = text.split("  apply-or-handoff:", 1)
        self.assertNotIn("git push", generate)
        self.assertNotIn("git commit", generate)
        self.assertIn("git push origin", apply)
        self.assertIn("same-repo", apply)

    def test_reconciler_still_owns_post_merge_validation_and_terminal_done(self):
        text = Path("consumer-template/gptauto-reconcile.yml").read_text(encoding="utf-8")
        self.assertIn("Resolve and dispatch canonical post-merge validation gate", text)
        self.assertIn("Require published release evidence", text)
        self.assertIn("Capture terminal DONE evidence directly", text)
        self.assertIn("Publish terminal foreground receipt", text)
        self.assertIn("POST_MERGE_RECOVERY_REQUIRED", text)
        self.assertIn("cancel-in-progress: true", text)
        self.assertNotIn("gh workflow run gptauto-observer.yml", text)


def test_reconcile_uploads_terminal_artifact_before_optional_pr_receipt():
    text = Path("consumer-template/gptauto-reconcile.yml").read_text()
    assert text.index("uses: ./.github/actions/upload-gptauto-log") < text.index("name: Publish terminal foreground receipt")
