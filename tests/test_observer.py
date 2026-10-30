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
        self.assertFalse(release_expected("fix(admin): distinguish queued GitHub checks from last completed release result"))
        self.assertFalse(release_expected("fix: show release notes without publishing"))
        self.assertTrue(release_expected("release: v0.1.60 publish verified image"))
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

    def test_release_task_waits_after_main_ci_then_finishes_on_published_release(self):
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
            green_release_run = capture(
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
                pr_ci_conclusion="success",
                pr_ci_run_id="70",
                main_ci_conclusion="success",
                main_ci_run_id="80",
            )
            published = capture(
                "o/r",
                "release",
                "main",
                "main",
                "def",
                "12",
                "v1.2.3: Fix",
                "closed",
                "true",
                "def",
                "82",
                "github-actions[bot]",
                d,
                release_tag="v1.2.3",
                release_state="published",
                pr_ci_conclusion="success",
                pr_ci_run_id="70",
                main_ci_conclusion="success",
                main_ci_run_id="80",
                release_run_id="81",
            )
            self.assertEqual(main_ci["task_id"], green_release_run["task_id"])
            self.assertEqual(main_ci["task_id"], published["task_id"])
            self.assertEqual(main_ci["state"], "VERIFY")
            self.assertEqual(green_release_run["state"], "VERIFY")
            self.assertEqual(published["state"], "DONE")
            self.assertEqual(published["completion_gate"], "release")
            receipt = json.loads(Path(published["paths"]["completion"]).read_text())
            self.assertTrue(receipt["complete"])
            self.assertTrue(receipt["release_published"])
            self.assertEqual(receipt["release_tag"], "v1.2.3")
            self.assertEqual(receipt["main_ci_run_id"], "80")
            self.assertEqual(receipt["release_run_id"], "81")

    def test_release_task_finishes_when_published_release_precedes_main_ci(self):
        with tempfile.TemporaryDirectory() as d:
            release_first = capture(
                "o/r",
                "release",
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
                release_tag="v1.2.3",
                release_state="published",
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
                release_published="true",
                release_id="1234",
                release_tag="v1.2.3",
            )
            self.assertEqual(release_first["state"], "VERIFY")
            self.assertEqual(ci_later["state"], "DONE")
            self.assertEqual(release_first["task_id"], ci_later["task_id"])

    def test_green_release_workflow_without_publication_is_not_terminal(self):
        with tempfile.TemporaryDirectory() as d:
            result = capture(
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
                "83",
                "dev",
                d,
                workflow_name="Release",
                workflow_conclusion="success",
                main_ci_conclusion="success",
                main_ci_run_id="82",
                release_conclusion="success",
                release_run_id="83",
            )
            self.assertEqual(result["state"], "VERIFY")
            self.assertNotIn("completion", result["paths"])

    def test_reconciler_pins_release_intent_and_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            forced_release = capture(
                "o/r",
                "reconcile",
                "main",
                "main",
                "def",
                "12",
                "Fix without version text",
                "closed",
                "true",
                "def",
                "90",
                "github-actions[bot]",
                d,
                pr_ci_conclusion="success",
                pr_ci_run_id="70",
                main_ci_conclusion="success",
                main_ci_run_id="80",
                release_conclusion="success",
                release_run_id="81",
                release_required_override="true",
                provenance="reconciler",
                release_published="true",
                release_id="9001",
                release_tag="v1.2.3",
            )
            self.assertEqual(forced_release["state"], "DONE")
            self.assertTrue(forced_release["release_required"])
            self.assertEqual(forced_release["completion_gate"], "release")
            self.assertEqual(forced_release["provenance"], "reconciler")
            receipt = json.loads(Path(forced_release["paths"]["completion"]).read_text())
            self.assertEqual(receipt["provenance"], "reconciler")
            self.assertEqual(receipt["terminal_evidence_run_id"], "90")
            self.assertEqual(receipt["release_run_id"], "81")
            self.assertTrue(receipt["release_published"])
            self.assertEqual(receipt["release_id"], "9001")
            self.assertEqual(receipt["release_tag"], "v1.2.3")

            forced_no_release = capture(
                "o/r",
                "reconcile",
                "main",
                "main",
                "def",
                "13",
                "v9.9.9: title changed after merge",
                "closed",
                "true",
                "def",
                "91",
                "github-actions[bot]",
                d,
                main_ci_conclusion="success",
                main_ci_run_id="82",
                release_required_override="false",
                provenance="reconciler",
            )
            self.assertEqual(forced_no_release["state"], "DONE")
            self.assertFalse(forced_no_release["release_required"])
            self.assertEqual(forced_no_release["completion_gate"], "main_ci")


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


    def test_pull_request_refresh_clears_prior_workflow_failure_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            capture(
                "o/r", "workflow_run", "main", "fix/x", "abc", "12",
                "Fix", "open", "false", "", "100", "dev", d,
                workflow_name="CI", workflow_conclusion="failure",
            )
            refreshed = capture(
                "o/r", "pull_request", "main", "fix/x", "abc", "12",
                "Fix", "open", "false", "", "101", "dev", d,
            )
            state = json.loads(Path(refreshed["paths"]["state"]).read_text())
            self.assertEqual(state["metadata"]["run_id"], "101")
            self.assertEqual(state["metadata"]["workflow_name"], "")
            self.assertEqual(state["metadata"]["workflow_conclusion"], "")
            self.assertEqual(state["metadata"]["event"], "pull_request")



    def test_duplicate_observer_evidence_does_not_dispatch_twice(self):
        with tempfile.TemporaryDirectory() as d:
            base = dict(
                repo="o/r", event="pull_request", default_branch="main",
                branch="fix/x", head_sha="abc", pr_number="12",
                pr_title="Fix", pr_state="open", pr_merged="false",
                log_root=d,
            )
            first = capture(**base, run_id="100", actor="dev",
                            pr_ci_status="in_progress", pr_ci_run_id="77")
            duplicate = capture(**base, run_id="101", actor="bot",
                                pr_ci_status="in_progress", pr_ci_run_id="77")
            self.assertTrue(first["dispatch_required"])
            self.assertFalse(duplicate["dispatch_required"])
            self.assertEqual(first["dispatch_key"], duplicate["dispatch_key"])
            changed = capture(**base, run_id="102", actor="dev",
                              pr_ci_status="completed", pr_ci_conclusion="success",
                              pr_ci_run_id="77")
            self.assertTrue(changed["dispatch_required"])
            self.assertNotEqual(changed["dispatch_key"], duplicate["dispatch_key"])
            attempt = capture(**base, run_id="103", actor="dev",
                              pr_ci_status="completed", pr_ci_conclusion="success",
                              pr_ci_run_id="77", pr_ci_run_attempt="2")
            self.assertTrue(attempt["dispatch_required"])
            self.assertFalse(capture(**base, run_id="104", actor="dev",
                                     pr_ci_status="completed", pr_ci_conclusion="success",
                                     pr_ci_run_id="77", pr_ci_run_attempt="2")["dispatch_required"])

    def test_manual_recovery_bypasses_observation_dedupe(self):
        with tempfile.TemporaryDirectory() as d:
            base = dict(repo="o/r", default_branch="main", branch="fix/x",
                        head_sha="abc", pr_number="12", pr_title="Fix",
                        pr_state="open", pr_merged="false", log_root=d)
            capture(**base, event="pull_request", run_id="1")
            forced = capture(**base, event="workflow_dispatch", run_id="2")
            self.assertTrue(forced["dispatch_required"])
            self.assertFalse(capture(**base, event="pull_request", run_id="3")["dispatch_required"])

    def test_terminal_task_does_not_rerun_on_new_ci_event(self):
        with tempfile.TemporaryDirectory() as d:
            base = dict(repo="o/r", default_branch="main", branch="main",
                        head_sha="def", pr_number="12", pr_title="Fix",
                        pr_state="closed", pr_merged="true",
                        merge_sha="def", log_root=d,
                        main_ci_conclusion="success")
            first = capture(**base, event="workflow_run", run_id="1",
                            main_ci_run_id="100", workflow_name="CI",
                            workflow_conclusion="success")
            second = capture(**base, event="workflow_run", run_id="2",
                             main_ci_run_id="101", workflow_name="CI",
                             workflow_conclusion="success")
            self.assertEqual(first["phase"], "DONE")
            self.assertEqual(second["phase"], "DONE")
            self.assertFalse(second["dispatch_required"])

if __name__ == "__main__":
    unittest.main()
