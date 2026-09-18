import unittest
from gptauto.engine import begin_verify,criterion,finish,gate,is_complete,plan_ready,start
from gptauto.model import Criterion,CriterionStatus,Gate,GateStatus,State,Task
from gptauto.planner import GoalPlanner
class DynamicGoalTests(unittest.TestCase):
    def make(self,goal):
        t=Task("t",goal,"o/r",[]);start(t);GoalPlanner().apply(t);plan_ready(t);return t
    def pass_all(self,t):
        for s in t.plan:gate(t,s.gate,GateStatus.PASSED,"evidence")
        begin_verify(t)
        for i in range(len(t.definition_of_done)):criterion(t,i,CriterionStatus.PASSED,"verified")
        finish(t)
    def test_document_change_does_not_require_release_or_merge(self):
        t=self.make("修改 README 文档")
        gates=[x.gate for x in t.plan];self.assertIn(Gate.COMMIT,gates);self.assertNotIn(Gate.RELEASE,gates);self.assertNotIn(Gate.MERGE,gates)
        self.pass_all(t);self.assertTrue(is_complete(t))
    def test_ci_goal_ends_at_ci_without_release(self):
        t=self.make("修复 Actions 直到 CI 全绿")
        gates=[x.gate for x in t.plan];self.assertIn(Gate.PR_CI,gates);self.assertNotIn(Gate.RELEASE,gates)
    def test_merge_goal_requires_merge_not_release(self):
        t=self.make("把代码合并到 main")
        gates=[x.gate for x in t.plan];self.assertIn(Gate.MERGE,gates);self.assertNotIn(Gate.RELEASE,gates)
    def test_release_goal_selects_release_chain(self):
        t=self.make("修复问题并发布 v1.2.3 正式版")
        gates=[x.gate for x in t.plan]
        for g in [Gate.PR,Gate.PR_CI,Gate.MERGE,Gate.MAIN_CI,Gate.RELEASE]:self.assertIn(g,gates)
    def test_done_requires_evidence_for_every_criterion(self):
        t=self.make("修改 README 文档")
        for s in t.plan:gate(t,s.gate,GateStatus.PASSED,"ok")
        begin_verify(t);self.assertFalse(is_complete(t))
if __name__=="__main__":unittest.main()
