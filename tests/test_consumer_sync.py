import json
import tempfile
import unittest
from pathlib import Path

from gptauto.consumer_sync.registry import ConsumerRegistry
from gptauto.consumer_sync.release_dispatch import build_release_dispatch_plan


class ConsumerSyncTests(unittest.TestCase):
    def test_registry_selects_only_active_auto_sync_consumers(self):
        payload = {
            "consumers": [
                {"repository": "owner/a", "status": "active", "auto_sync": True},
                {"repository": "owner/b", "status": "paused", "auto_sync": True},
                {"repository": "owner/c", "status": "active", "auto_sync": False},
            ]
        }
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "consumers.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            candidates = ConsumerRegistry(path).sync_candidates()
        self.assertEqual([item.repository for item in candidates], ["owner/a"])

    def test_release_dispatch_plan_is_version_bound(self):
        plan = build_release_dispatch_plan(
            [
                {"repository": "owner/a", "status": "active", "auto_sync": True},
                {"repository": "owner/b", "status": "disabled", "auto_sync": True},
            ],
            "v0.15.6",
        )
        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0].repository, "owner/a")
        self.assertEqual(plan[0].event, "gptauto_release_published")
        self.assertEqual(plan[0].version, "v0.15.6")

    def test_release_workflow_fans_out_and_degrades_to_scheduled_recovery(self):
        text = Path(".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("Fan out release to registered consumers", text)
        self.assertIn("gptauto.consumer_sync.release_dispatch", text)
        self.assertIn("repos/$repository/dispatches", text)
        self.assertIn("gptauto_release_published", Path("gptauto/consumer_sync/release_dispatch.py").read_text(encoding="utf-8"))
        self.assertIn("GPTAUTO_CONSUMER_TOKEN", text)
        self.assertIn("Legacy consumer listener detected", text)
        self.assertIn("gh workflow run gptauto-sync.yml", text)
        self.assertIn("steps.publish.outputs.created == 'true'", text)
        self.assertIn("Immediate cross-repository dispatch: deferred", text)
        self.assertIn("scheduled GPTAuto Consumer Sync remains authoritative", text)
        self.assertIn("exit 0", text)

    def test_consumer_sync_accepts_exact_release_dispatch(self):
        text = Path("consumer-template/gptauto-sync.yml").read_text(encoding="utf-8")
        self.assertIn("repository_dispatch:", text)
        self.assertIn("types: [gptauto_release_published]", text)
        self.assertIn("REQUESTED_VERSION", text)
        self.assertIn("SOURCE_REPOSITORY", text)
        self.assertIn('[[ "$SOURCE_REPOSITORY" == "b8vipvip/GPTAuto" ]]', text)
        self.assertIn('git clone --depth 1 --branch "$REQUESTED_VERSION"', text)
        self.assertIn('"v$ver" != "$REQUESTED_VERSION"', text)
        self.assertIn("schedule:", text)

    def test_status_workflow_scans_public_consumers_without_cross_repo_token(self):
        text = Path(".github/workflows/consumer-sync-status.yml").read_text(encoding="utf-8")
        self.assertIn("Consumer Sync Status", text)
        self.assertIn("CROSS_REPO_TOKEN", text)
        self.assertIn("raw.githubusercontent.com", text)
        self.assertIn("api.github.com", text)
        self.assertIn(".github/gptauto/VERSION", text)
        self.assertIn("check-runs?per_page=100", text)
        self.assertIn("public read-only GitHub endpoints", text)
        self.assertIn("gptauto-consumer-sync-status", text)
        self.assertIn("GPTAuto consumer sync status", text)
        self.assertIn("gh issue edit", text)
        self.assertIn("gh issue create", text)


if __name__ == "__main__":
    unittest.main()
