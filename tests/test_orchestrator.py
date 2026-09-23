import unittest
from gptauto.github import RunSummary
from gptauto.model import Criterion,Gate,GateStatus,GateStep,State,Task
from gptauto.orchestrator import Orchestrator,canonicalize_task
class FakeGitHub:
    def __init__(self,run=None,pr=None,release=None):self.run=run or RunSummary("completed","success",42);self.pr=pr or {"merged":True};self.release=release
    def latest_run(self,**kwargs):return self.run
    def classify_run(self,r):return "passed" if r.status=="completed" and r.conclusion=="success" else ("failed" if r.status=="completed" else "waiting")
    def pull(self,n):return self.pr
    def release_by_tag(self,t):return self.release
class OrchestratorTests(unittest.TestCase):
    def task(self,g):
        return Task("t","goal","o/r",[Criterion("verified")],state=State.EXECUTE,plan=[GateStep(g)],metadata={"work_branch":"fix/x","work_head_sha":"abc","pr_number":7,"default_branch":"main","merge_sha":"def","release_tag":"v1.0.0"})
    def test_waiting_ci_stays_waiting(self):
        t=self.task(Gate.PR_CI);d=Orchestrator(FakeGitHub(RunSummary("in_progress",None,9))).reconcile_once(t);self.assertEqual(d.action,"wait");self.assertEqual(t.plan[0].status,GateStatus.WAITING)
    def test_passed_ci_marks_only_selected_gate(self):
        t=self.task(Gate.PR_CI);Orchestrator(FakeGitHub()).reconcile_once(t);self.assertEqual(t.plan[0].status,GateStatus.PASSED)
    def test_merge_observation(self):
        t=self.task(Gate.MERGE);Orchestrator(FakeGitHub()).reconcile_once(t);self.assertEqual(t.plan[0].status,GateStatus.PASSED)
    def test_release_requires_evidence(self):
        t=self.task(Gate.RELEASE);self.assertEqual(Orchestrator(FakeGitHub()).reconcile_once(t).action,"wait")
    def test_protocol_v2_task_outlives_execution(self):
        t=self.task(Gate.PR_CI)
        t.plan[0].status=GateStatus.WAITING
        state=canonicalize_task(t)
        self.assertEqual(state["protocol"],"gptauto.task-state/v2")
        self.assertFalse(state["terminal_done"])
        self.assertEqual(state["phase"],"RUNNING")

    def test_repair_generation_has_stable_continuation_identity(self):
        t=self.task(Gate.PR_CI)
        t.plan[0].status=GateStatus.FAILED
        t.metadata["current_pr_head_sha"]="abc"
        state=canonicalize_task(t)
        self.assertEqual(state["phase"],"REPAIR_REQUIRED")
        self.assertTrue(state["continuation_required"])
        self.assertEqual(state["continuation_key"],"t:1:abc")
if __name__=="__main__":unittest.main()
