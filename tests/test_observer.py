import json
import tempfile
import unittest
from pathlib import Path

from gptauto.observer import capture, observed_task_id, release_expected


class ObserverTests(unittest.TestCase):
    def test_pr_id_is_stable_across_pr_push_ci_and_release(self):
        expected = observed_task_id("o/r", "12", "aaa")
        self.assertEqual(expected, observed_task_id("o/r", "12", "bbb", "merge"))
        self.assertEqual(expected, observed_task_id("o/r", "12", "merge", "merge"))

    def test_versioned_pr_implies_release_completion_gate(self):
        self.assertTrue(release_expected("v0.5.81: fix model verification"))
        self.assertTrue(release_expected("修复并发布正式版"))
        self.assertTrue(release_expected("chore: release v1.2.3"))
        self.assertFalse(release_expected("chore: sync GPTAuto v0.6.1"))
        self.assertFalse(release_expected("chore: sync GPTAuto v0.6.2", "Validate without requiring Release."))
        self.assertFalse(release_expected("docs: document v1.2.3 migration"))
        self.assertFalse(release_expected("docs: clarify setup"))

    def test_capture_creates_diagnostics_and_marks_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            r = capture(
                "o/r",
                "pull_request",
                "main",
                "fix/x",
                "abc",
                "12",
                "Fix bug",
                "open",
                "false",
                "",
                "77",
                "dev",
                d,
            )
            self.assertEqual(r["provenance"], "repository_observer")
            self.assertEqual(r["state"], "EXECUTE")
            state = json.loads(Path(r["paths"]["state"]).read_text())
            self.assertEqual(state["metadata"]["task_type"], "observed")

    def test_merge_is_verify_not_done(self):
        with tempfile.TemporaryDirectory() as d:
            r = capture(
                "o/r",
                "pull_request",
                "main",
                "fix/x",
                "abc",
                "12",
                "Fix",
                "closed",
                "true",
                "def",
                "78",
                "dev",
                d,
            )
            self.assertEqual(r["state"], "VERIFY")
            self.assertEqual(r["completion_gate"], "main_ci")

    def test_non_release_task_finishes_after_main_ci(self):
        with tempfile.TemporaryDirectory() as d:
            r = capture(
                "o/r",
                "workflow_run",
                "main",
                "main",
                "def",
                "12",
                "Fix",
                "closed",
                "true",
                "def",
                "79",
                "dev",
                d,
                workflow_name="CI",
                workflow_conclusion="success",
                main_ci_conclusion="success",
                main_ci_run_id="79",
            )
            self.assertEqual(r["state"], "DONE")
            self.assertEqual(r["completion_gate"], "main_ci")

    def test_release_task_waits_after_main_ci_then_finishes_on_release(self):
        with tempfile.TemporaryDirectory() as d:
            main_ci = capture(
                "o/r",
                "workflow_run",
                "main",
                "main",
                "def",
                "12",
                "v1.2.3: Fix",
                "closed",
                "true",
                "def",
                "80",
                "dev",
                d,
                workflow_name="CI",
                workflow_conclusion="success",
                pr_ci_conclusion="success",
                pr_ci_run_id="70",
                main_ci_conclusion="success",
                main_ci_run_id="80",
            )
            release = capture(
                "o/r",
                "workflow_run",
                "main",
                "main",
                "def",
                "12",
                "v1.2.3: Fix",
                "closed",
                "true",
                "def",
                "81",
                "dev",
                d,
                workflow_name="Release",
                workflow_conclusion="success",
                release_tag="v1.2.3",
                pr_ci_conclusion="success",
                pr_ci_run_id="70",
                main_ci_conclusion="success",
                main_ci_run_id="80",
            )
            self.assertEqual(main_ci["task_id"], release["task_id"])
            self.assertEqual(main_ci["state"], "VERIFY")
            self.assertEqual(release["state"], "DONE")
            self.assertEqual(release["completion_gate"], "release")


    def test_release_task_finishes_when_release_precedes_main_ci(self):
        with tempfile.TemporaryDirectory() as d:
            release_first = capture(
                "o/r",
                "workflow_run",
                "main",
                "main",
                "def",
                "12",
                "v1.2.3: Fix",
                "closed",
                "true",
                "def",
                "81",
                "dev",
                d,
                workflow_name="Release",
                workflow_conclusion="success",
                release_conclusion="success",
                release_run_id="81",
            )
            ci_later = capture(
                "o/r",
                "workflow_run",
                "main",
                "main",
                "def",
                "12",
                "v1.2.3: Fix",
                "closed",
                "true",
                "def",
                "82",
                "dev",
                d,
                workflow_name="CI",
                workflow_conclusion="success",
                main_ci_conclusion="success",
                main_ci_run_id="82",
                release_conclusion="success",
                release_run_id="81",
            )
            self.assertEqual(release_first["state"], "VERIFY")
            self.assertEqual(ci_later["state"], "DONE")
            self.assertEqual(release_first["task_id"], ci_later["task_id"])


    def test_capture_accumulates_history_from_previous_state(self):
        with tempfile.TemporaryDirectory() as d:
            first = capture(
                "o/r", "pull_request", "main", "fix/x", "abc", "12",
                "Fix", "open", "false", "", "90", "dev", d,
            )
            second = capture(
                "o/r", "workflow_run", "main", "fix/x", "abc", "12",
                "Fix", "open", "false", "", "91", "dev", d,
                workflow_name="CI", workflow_conclusion="success",
                pr_ci_conclusion="success", pr_ci_run_id="91",
            )
            self.assertEqual(first["task_id"], second["task_id"])
            state = json.loads(Path(second["paths"]["state"]).read_text())
            events = Path(second["paths"]["events"]).read_text().strip().splitlines()
            self.assertGreaterEqual(len(state["history"]), 3)
            self.assertEqual(len(events), len(state["history"]))
            self.assertTrue(any(e["kind"] == "time_budget" for e in state["history"]))
            self.assertEqual(json.loads(events[0])["kind"], "observation")
            self.assertEqual(sum(json.loads(e)["kind"] == "observation" for e in events), 2)


if __name__ == "__main__":
    unittest.main()
