import unittest
from pathlib import Path


class ObserverWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = Path("consumer-template/gptauto-observer.yml").read_text(encoding="utf-8")

    def test_gh_api_never_receives_jq_variable_flags(self):
        self.assertNotIn("--jq --arg ", self.text)
        self.assertNotIn("--jq --argjson ", self.text)

    def test_watchdog_filters_comment_body_with_standalone_jq(self):
        self.assertIn('gh api "repos/$REPOSITORY/issues/$pr/comments?per_page=100" 2>/dev/null |', self.text)
        self.assertIn('jq -r --arg marker "$marker"', self.text)

    def test_superseded_run_scan_slurps_pages_before_standalone_jq(self):
        self.assertIn('actions/runs?event=pull_request&branch=$HEAD_REF&per_page=100" --paginate --slurp |', self.text)
        self.assertIn('jq -r --argjson pr "$PR_NUMBER" --arg head "$CURRENT_HEAD"', self.text)
        self.assertIn(".[].workflow_runs[]", self.text)


if __name__ == "__main__":
    unittest.main()
