"""Session membership is decided by the tricolour's contents, not by the path.

The case that matters is a git worktree: the desktop app gives parallel sessions
their own, so one project's sessions have different working directories under a
different parent. Grouping by path prefix would split them, and would join two
unrelated projects that happen to share a parent. Every test here is about that
distinction.

The fixtures deliberately use different glyph shapes. A tricolour is three emoji
and not necessarily three squares, and nothing in the helper may depend on which
shapes it finds.
"""

import pathlib
import subprocess
import sys
import tempfile
import unittest

HELPER = (pathlib.Path(__file__).resolve().parent.parent
          / "skills" / "tricolour" / "tricolour.py")

TRICOLOUR_NAME = ".identicon/repository-identicon.tricolour"
TRICOLOUR = "🟥🟫🟥\n"
OTHER = "🔵🔵🟠\n"


def git(root, *args):
    subprocess.run(["git", "-C", str(root),
                    "-c", "user.email=test@example.com",
                    "-c", "user.name=Test",
                    *args], check=True, capture_output=True)


def run(*args):
    return subprocess.run([sys.executable, str(HELPER), *[str(a) for a in args]],
                          capture_output=True, text=True, timeout=60)


def make_repo(root, tricolour):
    (root / ".identicon").mkdir(parents=True, exist_ok=True)
    (root / TRICOLOUR_NAME).write_text(tricolour, encoding="utf-8")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "identicon")


class TricolourCase(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.repo = self.tmp / "project"
        self.repo.mkdir()
        make_repo(self.repo, TRICOLOUR)
        self.addCleanup(self._tmp.cleanup)

    def matches(self, result):
        return [line.split("\t", 1)[1] for line in result.stdout.splitlines()
                if line.startswith("match\t")]


class TestTheTricolour(TricolourCase):

    def test_it_is_reported_for_the_reference_repository(self):
        result = run("--repo", self.repo)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(f"tricolour\t{TRICOLOUR.strip()}", result.stdout)

    def test_a_repository_with_no_identicon_exits_one_and_matches_nothing(self):
        """The guarantee that a project without an identicon is never touched."""
        bare = self.tmp / "unmarked"
        bare.mkdir()
        git(bare, "init", "-q")
        result = run("--repo", bare, self.repo)
        self.assertEqual(1, result.returncode)
        self.assertEqual([], self.matches(result))

    def test_a_tricolour_of_other_shapes_is_read_the_same_way(self):
        """Squares today, circles tomorrow. The helper compares strings and has
        no opinion about glyphs."""
        round_ = self.tmp / "round"
        round_.mkdir()
        make_repo(round_, OTHER)
        result = run("--repo", round_)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(f"tricolour\t{OTHER.strip()}", result.stdout)


class TestMembership(TricolourCase):

    def test_a_worktree_of_the_same_repository_matches(self):
        """Different path, same seed, same mark -- so the same session group."""
        tree = self.tmp / "elsewhere" / "a-worktree"
        git(self.repo, "worktree", "add", "-q", "-b", "side", str(tree))
        result = run("--repo", self.repo, tree)
        self.assertEqual([str(tree)], self.matches(result))

    def test_a_neighbour_with_a_different_tricolour_does_not_match(self):
        """Sitting in the same parent directory is not membership."""
        other = self.tmp / "other-project"
        other.mkdir()
        make_repo(other, OTHER)
        result = run("--repo", self.repo, other)
        self.assertEqual([], self.matches(result))

    def test_a_path_that_is_not_a_repository_is_ignored(self):
        loose = self.tmp / "loose"
        loose.mkdir()
        result = run("--repo", self.repo, loose)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], self.matches(result))

    def test_a_vanished_path_is_ignored_rather_than_fatal(self):
        """A session's working directory can be deleted while it is listed."""
        result = run("--repo", self.repo, self.tmp / "never-existed")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], self.matches(result))


if __name__ == "__main__":
    unittest.main()
