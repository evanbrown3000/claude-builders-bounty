import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("changelog", ROOT / "scripts/generate_changelog.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changelog test ")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test Fixture")
        self.git("config", "user.email", "fixture@example.invalid")

    def git(self, *args):
        return MODULE.git(self.repo, *args)

    def commit(self, message):
        self.git("commit", "--allow-empty", "-qm", message)

    def test_since_lightweight_tag_all_categories_and_breaking(self):
        self.commit("feat: old release")
        self.git("tag", "v1")
        for subject in ("feat(cli): new command", "fix: Unicode café", "refactor!: new interface", "remove: obsolete flag"):
            self.commit(subject)
        output = MODULE.generate(self.repo)
        self.assertNotIn("old release", output)
        for text in ("### Added", "new command", "### Fixed", "Unicode café", "### Changed", "**BREAKING** new interface", "### Removed", "obsolete flag", "after `v1`"):
            self.assertIn(text, output)

    def test_no_tag_and_unconventional_subjects(self):
        self.commit("Add initial command")
        self.commit("Update docs [example](url)")
        output = MODULE.generate(self.repo)
        self.assertIn("all reachable commits", output)
        self.assertIn("Add initial command", output)
        self.assertIn(r"Update docs \[example\](url)", output)
        self.assertEqual(output, MODULE.generate(self.repo))

    def test_at_tag_has_no_commits(self):
        self.commit("initial")
        self.git("tag", "v1")
        self.assertEqual(MODULE.generate(self.repo).count("- None."), 4)

    def test_nearest_reachable_tag_not_unrelated_tag(self):
        self.commit("initial")
        self.git("tag", "v1")
        self.commit("fix: current")
        current = self.git("rev-parse", "HEAD")
        self.git("checkout", "--orphan", "unrelated")
        self.commit("other branch")
        self.git("tag", "v99")
        self.git("checkout", current)
        self.assertIn("after `v1`", MODULE.generate(self.repo))

    def test_empty_repository_fails(self):
        with self.assertRaises(ValueError):
            MODULE.generate(self.repo)

    def test_shallow_repository_fails(self):
        self.commit("initial")
        destination = self.repo / "shallow"
        self.git("clone", "--depth", "1", self.repo.as_uri(), str(destination))
        with self.assertRaisesRegex(ValueError, "Shallow repository"):
            MODULE.generate(destination)

    def test_wrapper_stdout_and_existing_file_protection(self):
        self.commit("feat: working")
        output = self.repo / "CHANGELOG.md"
        args = ["bash", str(ROOT / "changelog.sh"), "--repo", str(self.repo)]
        first = subprocess.run(args + ["--output", str(output)], capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        original = output.read_bytes()
        second = subprocess.run(args + ["--output", str(output)], capture_output=True, text=True)
        self.assertEqual(second.returncode, 1)
        self.assertEqual(output.read_bytes(), original)
        stdout = subprocess.run(args + ["--output", "-"], capture_output=True, text=True)
        self.assertEqual(stdout.stdout.encode(), original)
        forced = subprocess.run(args + ["--output", str(output), "--force"], capture_output=True, text=True)
        self.assertEqual(forced.returncode, 0, forced.stderr)


if __name__ == "__main__":
    unittest.main()
