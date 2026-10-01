import json
import tempfile
from pathlib import Path

from gptauto.executor import next_action
from gptauto.observer import capture
from gptauto.orchestrator import canonicalize_task


def test_action_required_capture_is_blocked_not_repair():
    with tempfile.TemporaryDirectory() as d:
        result = capture(
            "o/r",
            "workflow_run",
            "main",
            "fix/x",
            "abc",
            "12",
            "v1.2.3: Fix",
            "open",
            "false",
            "",
            "101",
            "github-actions[bot]",
            d,
            workflow_name="CI",
            workflow_conclusion="action_required",
            pr_ci_status="completed",
            pr_ci_conclusion="action_required",
            pr_ci_run_id="101",
            pr_ci_actor="github-actions[bot]",
            pr_ci_run_attempt="1",
            current_pr_head_sha="abc",
            blocked_reason="workflow_approval_required",
        )
        state = json.loads(Path(result["paths"]["state"]).read_text())
        assert result["phase"] == "USER_ACTION_REQUIRED"
        assert result["state"] == "BLOCKED"
        assert result["generation"] == 0
        assert state["metadata"]["repair_owner"] == ""
        assert state["metadata"]["blocked_reason"] == "workflow_approval_required"
        assert state["metadata"]["pr_ci_run_id"] == "101"
        assert state["metadata"]["pr_ci_run_attempt"] == "1"
        action = next_action(type(state) and __import__("gptauto.model", fromlist=["Task"]).Task.from_dict(state))
        assert action["action"] == "user_action_required"
        assert action["completion_lease"]["host_control"]["next_host_action"] == "REQUEST_USER_ACTION"


def test_in_progress_refresh_clears_previous_approval_block():
    with tempfile.TemporaryDirectory() as d:
        first = capture(
            "o/r",
            "workflow_run",
            "main",
            "fix/x",
            "abc",
            "12",
            "Fix",
            "open",
            "false",
            "",
            "101",
            "github-actions[bot]",
            d,
            workflow_name="CI",
            workflow_conclusion="action_required",
            pr_ci_status="completed",
            pr_ci_conclusion="action_required",
            pr_ci_run_id="101",
            current_pr_head_sha="abc",
            blocked_reason="workflow_approval_required",
        )
        second = capture(
            "o/r",
            "workflow_run",
            "main",
            "fix/x",
            "abc",
            "12",
            "Fix",
            "open",
            "false",
            "",
            "101",
            "github-actions[bot]",
            d,
            workflow_name="CI",
            workflow_conclusion="",
            pr_ci_status="in_progress",
            pr_ci_conclusion="",
            pr_ci_run_id="101",
            pr_ci_run_attempt="2",
            current_pr_head_sha="abc",
        )
        assert first["phase"] == "USER_ACTION_REQUIRED"
        assert second["phase"] == "PR_CI"
        state = json.loads(Path(second["paths"]["state"]).read_text())
        assert state["metadata"]["blocked_reason"] == ""
        assert state["metadata"]["pr_ci_status"] == "in_progress"
        assert state["metadata"]["pr_ci_run_attempt"] == "2"


def test_watchdog_observation_of_failed_latest_ci_reopens_repair_generation():
    with tempfile.TemporaryDirectory() as d:
        result = capture(
            "o/r",
            "workflow_dispatch",
            "main",
            "fix/x",
            "abc",
            "12",
            "Fix",
            "open",
            "false",
            "",
            "200",
            "github-actions[bot]",
            d,
            pr_ci_status="completed",
            pr_ci_conclusion="failure",
            pr_ci_run_id="199",
            current_pr_head_sha="abc",
        )
        state = json.loads(Path(result["paths"]["state"]).read_text())
        authority = canonicalize_task(__import__("gptauto.model", fromlist=["Task"]).Task.from_dict(state))
        assert result["phase"] == "REPAIR_REQUIRED"
        assert authority["phase"] == "REPAIR_REQUIRED"
        assert result["generation"] == 1
