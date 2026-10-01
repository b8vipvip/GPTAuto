"""Read and validate GPTAuto consumer registry.

The registry intentionally only produces sync candidates. It does not
perform repository writes; consumers are updated through PR based flows.
"""

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class Consumer:
    repository: str
    auto_sync: bool = False
    status: str = "unknown"
    sync_mode: str = "pull_request"


class ConsumerRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> list[Consumer]:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        consumers = payload.get("consumers", [])
        return [
            Consumer(
                repository=item["repository"],
                auto_sync=bool(item.get("auto_sync")),
                status=item.get("status", "unknown"),
                sync_mode=item.get("sync_mode", "pull_request"),
            )
            for item in consumers
        ]

    def sync_candidates(self) -> list[Consumer]:
        return [
            item
            for item in self.load()
            if item.auto_sync and item.status == "active"
        ]
