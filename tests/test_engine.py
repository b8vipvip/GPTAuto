import unittest
from gptauto.engine import ProtocolError,begin_verify,criterion,finish,gate,is_complete,plan_ready,start
from gptauto.model import Criterion,CriterionStatus,Gate,GateStatus,State,Task
from gptauto.planner import GoalPlanner
class EngineTests(unittest.TestCase):
    def task(self):
        t=Task("t1","修改 README 文档","o/r",[]);start(t);GoalPlanner().apply(t);plan_ready(t);return t
    def test_dynamic_happy_path(self):
        t=self.task()
        for s in t.plan:gate(t,s.gate,GateStatus.PASSED,"ok")
        begin_verify(t)
        for i in range(len(t.definition_of_done)):criterion(t,i,CriterionStatus.PASSED,"ok")
        finish(t);self.assertEqual(t.state,State.DONE);self.assertTrue(is_complete(t))
    def test_failed_gate_consumes_repair_budget(self):
        t=self.task();t.max_repair_attempts=1;gate(t,t.plan[0].gate,GateStatus.FAILED,"x");gate(t,t.plan[0].gate,GateStatus.FAILED,"x");self.assertEqual(t.state,State.BLOCKED)
    def test_unplanned_gate_is_rejected(self):
        t=self.task()
        with self.assertRaises(ProtocolError):gate(t,Gate.RELEASE,GateStatus.PASSED)
if __name__=="__main__":unittest.main()
