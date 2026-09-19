import unittest
from datetime import datetime, timedelta, timezone

from gptauto.model import Criterion, Task
from gptauto.time_budget import TimeBudget, apply, classify


class TimeBudgetTests(unittest.TestCase):
    def task_at(self, minutes):
        now = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
        task = Task("GA-time", "goal", "o/r", [Criterion("done")])
        task.created_at = (now - timedelta(minutes=minutes)).isoformat()
        return task, now

    def test_budget_levels(self):
        expected = [(29, "NORMAL"), (30, "SOFT_WARNING"), (40, "HANDOFF_READY"),
                    (45, "CHECKPOINT"), (48, "UI_TIMEOUT_GUARD")]
        for minutes, level in expected:
            task, now = self.task_at(minutes)
            self.assertEqual(classify(task, now)["level"], level)

    def test_apply_persists_checkpoint_metadata_and_event(self):
        task, now = self.task_at(48)
        status = apply(task, now)
        self.assertEqual(status["action"], "detach")
        self.assertEqual(task.metadata["time_budget_level"], "UI_TIMEOUT_GUARD")
        self.assertEqual(task.metadata["chat_session_elapsed_minutes"], 48.0)
        self.assertEqual(task.history[-1].kind, "time_budget")

    def test_same_level_does_not_duplicate_transition_event(self):
        task, now = self.task_at(45)
        apply(task, now)
        count = len(task.history)
        apply(task, now)
        self.assertEqual(len(task.history), count)


if __name__ == "__main__":
    unittest.main()
