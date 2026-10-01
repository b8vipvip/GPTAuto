import unittest

from gptauto.model import Criterion, CriterionStatus, Gate, GateStatus, GateStep, State, Task
from gptauto.orchestrator import canonicalize_task


class CanonicalLifecycleTests(unittest.TestCase):
    def task(self, *, release=True, main=GateStatus.WAITING, rel=GateStatus.WAITING):
        criteria = [
            Criterion("trace", CriterionStatus.PASSED, "event"),
            Criterion("merged", CriterionStatus.PASSED, "sha"),
            Criterion(
                "main",
                CriterionStatus.PASSED if main == GateStatus.PASSED else CriterionStatus.PENDING,
                "run" if main == GateStatus.PASSED else "",
            ),
        ]
        plan = [
            GateStep(Gate.MERGE, status=GateStatus.PASSED, evidence="sha"),
            GateStep(Gate.MAIN_CI, status=main, evidence="run" if main == GateStatus.PASSED else ""),
        ]
        if release:
            plan.append(GateStep(Gate.RELEASE, status=rel, evidence="v1.2.3" if rel == GateStatus.PASSED else ""))
            criteria.append(
                Criterion(
                    "release",
                    CriterionStatus.PASSED if rel == GateStatus.PASSED else CriterionStatus.PENDING,
                    "v1.2.3" if rel == GateStatus.PASSED else "",
                )
            )
        return Task(
            "GA-x",
            "v1.2.3 release",
            "o/r",
            criteria,
            state=State.VERIFY,
            plan=plan,
            metadata={"release_required": release},
        )

    def test_post_merge_ci_precedes_release(self):
        a = canonicalize_task(self.task())
        self.assertEqual(a["phase"], "POST_MERGE_CI")
        self.assertFalse(a["terminal_done"])

    def test_release_is_required_after_main_ci(self):
        a = canonicalize_task(self.task(main=GateStatus.PASSED))
        self.assertEqual(a["phase"], "RELEASE")
        self.assertEqual(a["completion_lease"], "ACTIVE")

    def test_only_full_dod_releases_lease(self):
        t = self.task(main=GateStatus.PASSED, rel=GateStatus.PASSED)
        a = canonicalize_task(t)
        self.assertEqual(a["phase"], "DONE")
        self.assertEqual(t.state, State.DONE)
        self.assertTrue(a["allow_foreground_exit"])

    def test_proposed_done_without_evidence_is_revoked(self):
        t = self.task(main=GateStatus.PASSED)
        t.state = State.DONE
        a = canonicalize_task(t)
        self.assertEqual(a["phase"], "RELEASE")
        self.assertEqual(t.state, State.VERIFY)

    def test_current_head_workflow_failure_is_canonical_repair(self):
        t = self.task(main=GateStatus.WAITING)
        t.metadata.update({"workflow_conclusion": "failure", "event_head_sha": "abc", "current_pr_head_sha": "abc"})
        a = canonicalize_task(t)
        self.assertEqual(a["phase"], "REPAIR_REQUIRED")
        self.assertEqual(a["repair_owner"], "repair_pipeline")

    def test_superseded_failure_is_not_canonical_repair(self):
        t = self.task(main=GateStatus.WAITING)
        t.metadata.update({"workflow_conclusion": "failure", "event_head_sha": "old", "current_pr_head_sha": "abc"})
        a = canonicalize_task(t)
        self.assertNotEqual(a["phase"], "REPAIR_REQUIRED")

    def test_failure_opens_one_tiered_repair_generation(self):
        t = self.task(main=GateStatus.FAILED)
        a = canonicalize_task(t)
        self.assertEqual(a["phase"], "REPAIR_REQUIRED")
        self.assertEqual(a["generation"], 1)
        self.assertEqual(a["repair_owner"], "repair_pipeline")
        b = canonicalize_task(t)
        self.assertEqual(b["generation"], 1)

    def test_repair_owner_clears_after_failure_is_resolved(self):
        t = self.task(main=GateStatus.FAILED)
        canonicalize_task(t)
        t.plan[1].status = GateStatus.WAITING
        t.metadata["workflow_conclusion"] = ""
        a = canonicalize_task(t)
        self.assertNotEqual(a["phase"], "REPAIR_REQUIRED")
        self.assertEqual(a["repair_owner"], "")

    def test_action_required_is_user_action_not_repair(self):
        t = self.task(main=GateStatus.WAITING)
        t.metadata.update(
            {
                "workflow_conclusion": "action_required",
                "event_head_sha": "abc",
                "current_pr_head_sha": "abc",
                "blocked_reason": "workflow_approval_required",
            }
        )
        a = canonicalize_task(t)
        self.assertEqual(a["phase"], "USER_ACTION_REQUIRED")
        self.assertEqual(t.state, State.BLOCKED)
        self.assertEqual(a["generation"], 0)
        self.assertEqual(a["repair_owner"], "")
        self.assertEqual(a["completion_lease"], "BLOCKED")
        self.assertTrue(a["allow_foreground_exit"])
        self.assertEqual(a["blocked_reason"], "workflow_approval_required")

    def test_superseded_action_required_does_not_block_current_head(self):
        t = self.task(main=GateStatus.WAITING)
        t.metadata.update({"workflow_conclusion": "action_required", "event_head_sha": "old", "current_pr_head_sha": "abc"})
        a = canonicalize_task(t)
        self.assertNotEqual(a["phase"], "USER_ACTION_REQUIRED")


if __name__ == "__main__":
    unittest.main()
