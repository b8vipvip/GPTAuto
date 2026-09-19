import tempfile,unittest
from pathlib import Path
from gptauto.observer import capture,observed_task_id
class ObserverTests(unittest.TestCase):
 def test_pr_id_is_stable_across_synchronize_and_close(self):
  self.assertEqual(observed_task_id("o/r","12","aaa"),observed_task_id("o/r","12","bbb"))
 def test_capture_creates_diagnostics_and_marks_provenance(self):
  with tempfile.TemporaryDirectory() as d:
   r=capture("o/r","pull_request","main","fix/x","abc","12","Fix bug","open","false","","77","dev",d)
   self.assertEqual(r["provenance"],"repository_observer");self.assertEqual(r["state"],"EXECUTE")
   state=json.loads(Path(r["paths"]["state"]).read_text());self.assertEqual(state["metadata"]["task_type"],"observed")
 def test_merged_pr_is_done(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(capture("o/r","pull_request","main","fix/x","abc","12","Fix","closed","true","def","78","dev",d)["state"],"DONE")
import json
if __name__=="__main__":unittest.main()
