import unittest

from gptauto.executor import next_action
from gptauto.model import Criterion, Gate, GateStatus, GateStep, State, Task


class ExecutorTests(unittest.TestCase):
    def task(self, *, state=State.EXECUTE, pr_ci=GateStatus.PASSED, merge=GateStatus.WAITING, conclusion="success"):
        return Task(
            "GA-test",
            "v1.2.3: ship",
            "o/r",
            [Criterion("done")],
            state=state,
            plan=[
                GateStep(Gate.PR_CI, status=pr_ci),
                GateStep(Gate.MERGE, status=merge),
            ],
            metadata={
                "pr_number": "7",
                "head_sha": "abc",
                "run_id": "42",
                "workflow_name": "CI",
                "workflow_conclusion": conclusion,
                "completion_gate": "release",
            },
        )

    def test_ci_passed_merge_waiting_becomes_merge_action(self):
        action = next_action(self.task())
        self.assertEqual(action["action"], "merge")
        self.assertEqual(action["pr_number"], "7")

    def test_failure_becomes_repair_request(self):
        action = next_action(self.task(pr_ci=GateStatus.FAILED, conclusion="failure"))
        self.assertEqual(action["action"], "repair_request")
        self.assertEqual(action["run_id"], "42")

    def test_verify_waits_for_post_merge_evidence(self):
        action = next_action(self.task(state=State.VERIFY, merge=GateStatus.PASSED))
        self.assertEqual(action["action"], "verify")

    def test_done_is_terminal(self):
        action = next_action(self.task(state=State.DONE, merge=GateStatus.PASSED))
        self.assertEqual(action["action"], "done")


if __name__ == "__main__":
    unittest.main()
