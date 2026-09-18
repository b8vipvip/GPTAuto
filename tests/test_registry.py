import tempfile,unittest
from pathlib import Path
from gptauto.model import Criterion,Task
from gptauto.registry import latest,register
class RegistryTests(unittest.TestCase):
 def test_register_and_latest(self):
  t=Task("GA-123456789abc","修复 qnbot","b8vipvip/qnbot",[Criterion("CI 全绿")]);t.bind(branch="fix/x",pr_number="301",run_id="123")
  with tempfile.TemporaryDirectory() as d:
   p=register(t,d,artifact_name="gptauto-"+t.task_id);self.assertTrue(Path(p).exists());x=latest(d);self.assertEqual(x["pr_number"],"301");self.assertEqual(x["artifact_name"],"gptauto-GA-123456789abc")
 def test_binding_is_audited(self):
  t=Task("GA-123456789abc","goal","owner/repo",[Criterion("done")]);t.bind(head_sha="abc",merge_sha="def");self.assertEqual(t.history[-1].kind,"binding")
if __name__=="__main__":unittest.main()
