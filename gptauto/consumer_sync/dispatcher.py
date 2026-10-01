"""Create synchronization plans for consumer repositories."""

from dataclasses import dataclass
from .registry import Consumer


@dataclass(frozen=True)
class SyncPlan:
    repository: str
    mode: str
    operation: str = "sync"


def build_sync_plan(consumer: Consumer) -> SyncPlan:
    if not consumer.auto_sync:
        raise ValueError("consumer is not enabled for sync")
    return SyncPlan(
        repository=consumer.repository,
        mode=consumer.sync_mode,
    )
