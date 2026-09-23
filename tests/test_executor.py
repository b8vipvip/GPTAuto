import unittest

from gptauto.executor import next_action
from gptauto.model import Criterion, CriterionStatus, Gate, GateStatus, GateStep, State, Task


class ExecutorTests(unittest.TestCase):
    def task(self, *, state=State.EXECUTE, pr_ci=GateStatus.PASSED, merge=GateStatus.WAITING, conclusion="success"):
        return Task(
            "GA-test", "v1.2.3: ship", "o/r", [Criterion("done", CriterionStatus.PASSED, "verified")], state=state,
            plan=[GateStep(Gate.PR_CI, status=pr_ci), GateStep(Gate.MERGE, status=merge)],
            metadata={
                "pr_number": "7", "head_sha": "abc", "event_head_sha": "abc", "current_pr_head_sha": "abc",
                "run_id": "42", "workflow_name": "CI", "workflow_conclusion": conclusion,
                "completion_gate": "release", "release_required": True,
            },
        )

    def test_ci_passed_merge_waiting_becomes_merge_action(self):
        action = next_action(self.task())
        self.assertEqual(action["action"], "merge")
        self.assertEqual(action["pr_number"], "7")
        self.assertTrue(action["completion_lease"]["active"])
        self.assertFalse(action["completion_lease"]["may_finish_foreground"])
        self.assertEqual(action["completion_lease"]["foreground_completion_status"], "continue_required")
        self.assertIn("Do not report", action["completion_lease"]["foreground_instruction"])

    def test_failure_becomes_one_head_scoped_repair_cycle(self):
        action = next_action(self.task(pr_ci=GateStatus.FAILED, conclusion="failure"))
        self.assertEqual(action["action"], "repair_request")
        self.assertEqual(action["repair_key"], "GA-test:abc")

    def test_superseded_failure_does_not_create_repair(self):
        task = self.task(pr_ci=GateStatus.WAITING, conclusion="failure")
        task.metadata["event_head_sha"] = "old"
        task.metadata["current_pr_head_sha"] = "abc"
        action = next_action(task)
        self.assertEqual(action["action"], "superseded")

    def test_cancelled_current_head_keeps_lease_without_repair(self):
        action = next_action(self.task(pr_ci=GateStatus.WAITING, conclusion="cancelled"))
        self.assertEqual(action["action"], "lease_wait")
        self.assertTrue(action["completion_lease"]["active"])

    def test_merged_verify_adopts_reconciler_even_when_executor_did_not_merge(self):
        task = self.task(state=State.VERIFY, merge=GateStatus.PASSED)
        task.metadata["merge_sha"] = "merged123"
        action = next_action(task)
        self.assertEqual(action["action"], "reconcile_adopt")
        self.assertEqual(action["merge_sha"], "merged123")
        self.assertEqual(action["pr_number"], "7")
        self.assertTrue(action["release_required"])
        self.assertTrue(action["completion_lease"]["active"])
        self.assertFalse(action["completion_lease"]["may_finish_foreground"])

    def test_verify_without_merge_identity_keeps_waiting(self):
        action = next_action(self.task(state=State.VERIFY, merge=GateStatus.PASSED))
        self.assertEqual(action["action"], "verify")

    def test_timeout_guard_becomes_recovery_when_no_gate_action_is_ready(self):
        task = self.task(pr_ci=GateStatus.WAITING)
        task.metadata["time_budget_level"] = "UI_TIMEOUT_GUARD"
        task.metadata["time_budget_action"] = "detach"
        task.metadata["chat_session_elapsed_minutes"] = 48.2
        action = next_action(task)
        self.assertEqual(action["action"], "timeout_recovery")
        self.assertTrue(action["detach"])

    def test_unfinished_task_never_returns_plain_wait(self):
        action = next_action(self.task(pr_ci=GateStatus.WAITING))
        self.assertEqual(action["action"], "lease_wait")
        self.assertTrue(action["completion_lease"]["active"])

    def test_done_releases_completion_lease(self):
        task = self.task(state=State.DONE, merge=GateStatus.PASSED)
        task.plan.extend([GateStep(Gate.MAIN_CI, status=GateStatus.PASSED, evidence="main-ci"), GateStep(Gate.RELEASE, status=GateStatus.PASSED, evidence="v1.2.3")])
        task.metadata["release_run_id"] = "99"
        action = next_action(task)
        self.assertEqual(action["action"], "done")
        self.assertFalse(action["completion_lease"]["active"])
        self.assertTrue(action["completion_lease"]["may_finish_foreground"])
        self.assertEqual(action["completion_lease"]["foreground_completion_status"], "terminal")
        self.assertIn("terminal DONE evidence", action["completion_lease"]["foreground_instruction"])
        self.assertEqual(action["completion_lease"]["host_control"]["foreground_disposition"], "EXIT_ALLOWED")
        self.assertTrue(action["completion_lease"]["host_control"]["terminal_done"])
        self.assertEqual(action["completion_receipt"]["completion_gate"], "release")
        self.assertTrue(action["completion_receipt"]["release_required"])


    def test_active_lease_requires_foreground_poll_and_denies_exit(self):
        task = self.task(state=State.EXECUTE)
        action = next_action(task)
        lease = action["completion_lease"]
        self.assertEqual(lease["foreground_disposition"], "CONTINUE_REQUIRED")
        self.assertFalse(lease["allow_foreground_exit"])
        self.assertTrue(lease["requires_foreground_poll"])
        self.assertEqual(lease["host_control"]["schema"], "gptauto.host-control/v1")
        self.assertFalse(lease["host_control"]["allow_foreground_exit"])
        self.assertEqual(lease["host_control"]["next_host_action"], "CONTINUE_CURRENT_TASK")


if __name__ == "__main__":
    unittest.main()
