import unittest
from gptauto.github import RunSummary
from gptauto.model import State, Task
from gptauto.orchestrator import Orchestrator

class FakeGitHub:
    def __init__(self, run=None, pr=None, release=None):
        self.run=run or RunSummary("completed","success",42); self.pr=pr or {"merged":True}; self.release=release
    def latest_run(self, **kwargs): return self.run
    def classify_run(self, r): return "passed" if r.conclusion=="success" else ("waiting" if r.status!="completed" else "failed")
    def pull(self,n): return self.pr
    def release_by_tag(self,t): return self.release

class OrchestratorTests(unittest.TestCase):
    def task(self,state):
        return Task("t","goal","o/r",["verified"],state=state,metadata={"work_branch":"fix/x","pr_number":7,"default_branch":"main","release_tag":"v1.0.0"})
    def test_waiting_ci_is_not_completion(self):
        t=self.task(State.WAIT_CI); g=FakeGitHub(RunSummary("in_progress",None,9))
        d=Orchestrator(g).reconcile_once(t); self.assertEqual(d.action,"wait"); self.assertEqual(t.state,State.WAIT_CI)
    def test_failed_ci_enters_analysis(self):
        t=self.task(State.WAIT_CI); g=FakeGitHub(RunSummary("completed","failure",9))
        Orchestrator(g).reconcile_once(t); self.assertEqual(t.state,State.ANALYZE)
    def test_passed_ci_advances(self):
        t=self.task(State.WAIT_CI); Orchestrator(FakeGitHub()).reconcile_once(t); self.assertEqual(t.state,State.MERGE)
    def test_merged_pr_advances(self):
        t=self.task(State.MERGE); Orchestrator(FakeGitHub()).reconcile_once(t); self.assertEqual(t.state,State.MAIN_CI)
    def test_release_requires_evidence(self):
        t=self.task(State.RELEASE); t.release_required=True
        d=Orchestrator(FakeGitHub(release=None)).reconcile_once(t); self.assertEqual(d.action,"wait")
        Orchestrator(FakeGitHub(release={"draft":False})).reconcile_once(t); self.assertEqual(t.state,State.VERIFY)

if __name__=="__main__": unittest.main()
