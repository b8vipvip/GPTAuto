from __future__ import annotations
from dataclasses import dataclass
from .engine import Signal, advance
from .github import GitHubClient
from .model import State, Task

@dataclass(frozen=True)
class Decision:
    action: str
    reason: str

class Orchestrator:
    """Observe GitHub and advance only transitions that can be proven automatically."""
    def __init__(self, client: GitHubClient):
        self.github=client

    def decide(self, task: Task) -> Decision:
        m=task.metadata
        if task.state==State.PR:
            n=m.get("pr_number")
            if not n: return Decision("wait","PR number has not been recorded")
            return Decision("opened",f"PR #{n} recorded")

        if task.state==State.WAIT_CI:
            branch=m.get("work_branch")
            if not branch: return Decision("blocked","work_branch is required")
            run=self.github.latest_run(branch=branch)
            c=self.github.classify_run(run)
            if c=="passed": return Decision("passed",f"PR branch CI run {run.run_id} passed")
            if c=="failed": return Decision("failed",f"PR branch CI run {run.run_id} failed")
            return Decision("wait",f"PR CI is {run.status}")

        if task.state==State.MERGE:
            n=m.get("pr_number")
            if not n: return Decision("blocked","pr_number is required")
            pr=self.github.pull(int(n))
            if pr.get("merged"): return Decision("merged",f"PR #{n} is merged")
            return Decision("wait",f"PR #{n} is not merged yet")

        if task.state==State.MAIN_CI:
            default=m.get("default_branch","main")
            run=self.github.latest_run(branch=default,event="push")
            c=self.github.classify_run(run)
            if c=="passed": return Decision("passed",f"default-branch CI run {run.run_id} passed")
            if c=="failed": return Decision("failed",f"default-branch CI run {run.run_id} failed")
            return Decision("wait",f"default-branch CI is {run.status}")

        if task.state==State.RELEASE:
            if not task.release_required: return Decision("skipped","task does not require a release")
            tag=m.get("release_tag")
            if not tag: return Decision("blocked","release_tag is required")
            release=self.github.release_by_tag(tag)
            if release and not release.get("draft"): return Decision("released",f"release {tag} exists")
            return Decision("wait",f"release {tag} is not published yet")

        if task.state==State.VERIFY:
            checks=m.get("verification",{})
            if checks.get("passed") is True: return Decision("verified",checks.get("reason","acceptance verification passed"))
            if checks.get("passed") is False: return Decision("failed",checks.get("reason","acceptance verification failed"))
            return Decision("wait","final verification evidence has not been recorded")

        return Decision("wait",f"{task.state.value} requires a worker action")

    def reconcile_once(self, task: Task) -> Decision:
        d=self.decide(task)
        if d.action=="wait": return d
        advance(task,Signal(d.action,d.reason))
        return d
