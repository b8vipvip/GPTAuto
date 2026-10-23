"""Regression contract: a maintenance main push may not rewrite an existing Release tag."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")


class ExistingTagPolicyTests(unittest.TestCase):
    def test_main_maintenance_push_skips_existing_version(self):
        self.assertIn('if [[ "$tagged" != "$SHA" ]]; then', WORKFLOW)
        self.assertIn('if [[ "$GITHUB_EVENT_NAME" == "push" ]]; then', WORKFLOW)
        self.assertIn('echo "release_exists=true" >> "$GITHUB_OUTPUT"', WORKFLOW)
        self.assertIn('bump project version for a new Release', WORKFLOW)
        self.assertIn("if: steps.tag.outputs.release_exists != 'true'", WORKFLOW)

    def test_explicit_release_with_wrong_sha_remains_an_error(self):
        self.assertIn('echo "::error::Tag $TAG points to $tagged, expected $SHA"', WORKFLOW)
        self.assertIn('exit 1', WORKFLOW)


if __name__ == "__main__":
    unittest.main()
