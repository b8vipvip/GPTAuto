"""Release fan-out planning for GPTAuto consumers.

The planner intentionally does not mutate consumer repositories. It produces
an explicit dispatch plan that can be executed by the sync workflow.
"""

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ConsumerDispatch:
    repository: str
    event: str
    version: str


def build_release_dispatch_plan(consumers: Iterable[dict], version: str):
    plan = []
    for consumer in consumers:
        if consumer.get("status") != "active":
            continue
        if not consumer.get("auto_sync", False):
            continue
        plan.append(
            ConsumerDispatch(
                repository=consumer["repository"],
                event="gptauto_release_published",
                version=version,
            )
        )
    return plan
