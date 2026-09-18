import unittest
from gptauto.engine import ProtocolError, Signal, advance, is_complete
from gptauto.model import State, Task

class EngineTests(unittest.TestCase):
    def task(self): return Task("t1","ship fix","o/r",["verified"],max_repair_attempts=2)
    def test_happy_path(self):
        t=self.task()
        for x in ["accepted","ready","committed","opened","passed","merged","passed","skipped","verified"]: advance(t,Signal(x))
        self.assertEqual(t.state,State.DONE); self.assertTrue(is_complete(t))
    def test_ci_failure_repair_loop(self):
        t=self.task()
        for x in ["accepted","ready","committed","opened","failed","fixable","committed","passed"]: advance(t,Signal(x))
        self.assertEqual(t.state,State.MERGE); self.assertEqual(t.repair_attempts,1)
    def test_repair_budget_blocks(self):
        t=self.task(); t.state=State.ANALYZE; t.repair_attempts=2; advance(t,Signal("fixable")); self.assertEqual(t.state,State.BLOCKED)
    def test_invalid_transition(self):
        with self.assertRaises(ProtocolError): advance(self.task(),Signal("merged"))

if __name__=="__main__": unittest.main()
