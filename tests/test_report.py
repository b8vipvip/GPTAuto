import tempfile,unittest
from gptauto.model import Criterion,Task
from gptauto.registry import diagnostic_report,register
class ReportTests(unittest.TestCase):
 def test_report_contains_task_id_artifact_and_prompt(self):
  t=Task("GA-abcdef123456","修复 GPTWork","b8vipvip/GPTWork",[Criterion("done")]);t.bind(pr_number="235",run_id="99")
  with tempfile.TemporaryDirectory() as d:
   register(t,d,artifact_name="gptauto-"+t.task_id);r=diagnostic_report(d)
   self.assertTrue(r["found"]);self.assertEqual(r["task_id"],t.task_id);self.assertEqual(r["artifact_name"],"gptauto-GA-abcdef123456");self.assertIn("GA-abcdef123456",r["analysis_prompt"])
if __name__=="__main__":unittest.main()
