import json,tempfile,unittest
from pathlib import Path
from gptauto.audit import write_audit
from gptauto.engine import begin_verify,criterion,finish,gate,plan_ready,start
from gptauto.model import CriterionStatus,GateStatus,Task
from gptauto.planner import GoalPlanner

class AuditTests(unittest.TestCase):
    def task(self):
        t=Task("GA-test","修改 README 文档","o/r",[]);t.record("created",kind="goal");start(t);GoalPlanner().apply(t);plan_ready(t);return t
    def test_writes_four_audit_files(self):
        t=self.task()
        with tempfile.TemporaryDirectory() as d:
            paths=write_audit(t,d)
            self.assertEqual({"directory","task_log","state","events","summary"},set(paths))
            for k in ["task_log","state","events","summary"]:self.assertTrue(Path(paths[k]).exists())
            data=json.loads(Path(paths["state"]).read_text(encoding="utf-8"));self.assertEqual("GA-test",data["task_id"])
    def test_final_summary_proves_done(self):
        t=self.task()
        for s in t.plan:gate(t,s.gate,GateStatus.PASSED,"commit abc")
        begin_verify(t)
        for i in range(len(t.definition_of_done)):criterion(t,i,CriterionStatus.PASSED,"verified")
        finish(t)
        with tempfile.TemporaryDirectory() as d:
            paths=write_audit(t,d);summary=Path(paths["summary"]).read_text(encoding="utf-8")
            self.assertIn("State: **DONE**",summary);self.assertIn("Complete: **YES**",summary)
    def test_passed_criterion_requires_evidence(self):
        t=self.task()
        for s in t.plan:gate(t,s.gate,GateStatus.PASSED,"ok")
        begin_verify(t)
        with self.assertRaises(Exception):criterion(t,0,CriterionStatus.PASSED,"")
    def test_completion_receipt_records_terminal_provenance(self):
        t=self.task()
        t.metadata.update({"provenance":"reconciler","run_id":"12345"})
        for s in t.plan:gate(t,s.gate,GateStatus.PASSED,"ok")
        begin_verify(t)
        for i in range(len(t.definition_of_done)):criterion(t,i,CriterionStatus.PASSED,"verified")
        finish(t)
        with tempfile.TemporaryDirectory() as d:
            paths=write_audit(t,d);receipt=json.loads(Path(paths["completion"]).read_text(encoding="utf-8"))
            self.assertEqual("reconciler",receipt["provenance"])
            self.assertEqual("12345",receipt["terminal_evidence_run_id"])
if __name__=="__main__":unittest.main()
