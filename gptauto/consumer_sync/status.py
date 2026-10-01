"""Consumer Sync lifecycle status helpers.

This module keeps consumer synchronization states explicit so release fan-out,
scheduled recovery, and manual sync use the same vocabulary.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


SYNC_STATES = {
    "discovered",
    "registered",
    "syncing",
    "pr_created",
    "ci_running",
    "merged",
    "failed",
    "removed",
}


@dataclass(frozen=True)
class ConsumerSyncStatus:
    repository: str
    state: str
    version: Optional[str] = None
    pr: Optional[int] = None
    updated_at: str = ""

    def __post_init__(self):
        if self.state not in SYNC_STATES:
            raise ValueError(f"unknown consumer sync state: {self.state}")

    def as_dict(self):
        return {
            "repository": self.repository,
            "state": self.state,
            "version": self.version,
            "pr": self.pr,
            "updated_at": self.updated_at or datetime.now(timezone.utc).isoformat(),
        }
