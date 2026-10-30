import unittest
from pathlib import Path
from gptauto.consumer_sync_ci_gate import verdict

SHA = "a" * 40
BAD = "b" * 40


def run(name, sha=SHA, status="completed", conclusion="success",
        event="pull_request"):
    return {"name": name, "head_sha": sha, "status": status,
            "conclusion": conclusion, "event": event}


class ConsumerMergeGateTests(unittest.TestCase):
    def test_require_exact_sha_and_pr_ci(self):
        self.assertEqual(verdict("chat2api", SHA, [run("CI", BAD)])["status"], "pending")
        self.assertEqual(verdict("chat2api", SHA, [run("CI", event="push")])["status"], "pending")
        self.assertEqual(verdict("chat2api", SHA, [run("CI", status="in_progress", conclusion=None)])["status"], "pending")
        self.assertEqual(verdict("chat2api", SHA, [run("CI")])["status"], "passed")

    def test_all_mv3c_proofs_required(self):
        success = [run("CI"), run("mv3c validation"),
                   run("mv3c source Docker build")]
        self.assertEqual(verdict("mv3c", SHA, success)["status"], "passed")
        self.assertEqual(verdict("mv3c", SHA, success[:2])["status"], "pending")

    def test_failed_checks_block_even_without_branch_protection(self):
        self.assertEqual(verdict("qnbot", SHA, [run("CI", conclusion="failure")])["status"], "failed")
        self.assertEqual(verdict("qnbot", SHA, [run("CI", conclusion="cancelled")])["status"], "failed")

    def test_durable_success_for_same_sha_overrides_older_failure(self):
        self.assertEqual(verdict("chat2api", SHA, [
            run("CI", conclusion="failure"), run("CI")])["status"], "passed")

    def test_gptwork_requires_policy_and_boundary(self):
        self.assertEqual(verdict("GPTWork", SHA, [run("CI")])["status"], "pending")
        self.assertEqual(verdict("GPTWork", SHA, [
            run("CI"), run("Private Core Boundary"), run("Actions Policy Check")
        ])["status"], "passed")

    def test_sync_template_never_unconditionally_auto_merges(self):
        workflow = Path("consumer-template/gptauto-sync.yml").read_text(encoding="utf-8")
        self.assertIn("--match-head-commit", workflow)
        self.assertIn("gptauto.consumer_sync_ci_gate", workflow)
        self.assertIn("gate_passed=true", workflow)
        self.assertIn("if [[ \"$gate_passed\" != true ]]", workflow)
        self.assertLess(workflow.index("gate_passed=true"),
                        workflow.index('gh pr merge "$pr" --squash'))
        self.assertNotIn('gh pr merge "$pr" --auto --squash', workflow)

    def test_unknown_repo_or_invalid_commit_blocked(self):
        self.assertEqual(verdict("unsupported", SHA, [run("CI")])["status"], "blocked")
        self.assertEqual(verdict("qnbot", "master", [run("CI")])["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
