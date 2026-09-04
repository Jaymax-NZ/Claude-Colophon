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

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

HELPER = (pathlib.Path(__file__).resolve().parent.parent
          / "skills" / "tricolour" / "tricolour.py")

SETTINGS_NAME = ".identicon/settings.json"
TRICOLOUR = "🟥🟫🟥"
OTHER = "🔵🔵🟠"


def git(root, *args):
    subprocess.run(["git", "-C", str(root),
                    "-c", "user.email=test@example.com",
                    "-c", "user.name=Test",
                    *args], check=True, capture_output=True)


def run(*args):
    return subprocess.run([sys.executable, str(HELPER), *[str(a) for a in args]],
                          capture_output=True, text=True, timeout=60)


def make_repo(root, tricolour):
    """A repository carrying the generator's settings and nothing else.

    Only `renders.tricolour` is populated. The helper must read that field and
    not reconstruct the value from `identicon.current.tricolour`, so a fixture
    that omits the shape-and-colour pairs entirely proves it does not.
    """
    (root / ".identicon").mkdir(parents=True, exist_ok=True)
    (root / SETTINGS_NAME).write_text(
        json.dumps({"renders": {"tricolour": tricolour}}), encoding="utf-8")
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

    def test_unreadable_settings_are_treated_as_no_identicon(self):
        """A half-written or hand-mangled settings file must not crash a run
        that is only ever advisory."""
        broken = self.tmp / "broken"
        broken.mkdir()
        make_repo(broken, TRICOLOUR)
        (broken / SETTINGS_NAME).write_text("{not json", encoding="utf-8")
        self.assertEqual(1, run("--repo", broken).returncode)
        self.assertEqual([], self.matches(run("--repo", self.repo, broken)))

    def test_settings_without_the_render_field_matches_nothing(self):
        """Present but empty is not the same as absent, and neither is a match."""
        empty = self.tmp / "empty"
        empty.mkdir()
        make_repo(empty, TRICOLOUR)
        (empty / SETTINGS_NAME).write_text(
            json.dumps({"identicon": {"current": {}}}), encoding="utf-8")
        self.assertEqual(1, run("--repo", empty).returncode)

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


class TestStripping(unittest.TestCase):
    """A leading tricolour is recognised by position and count, never by glyph.

    Matching the current value would only ever find marks already correct, and
    matching squares would skip every tricolour drawn from another shape. Both
    are the failure this stripping exists to prevent, so the fixtures use
    shapes the repository does not currently issue.
    """

    def strip(self, title):
        return helper().strip_tricolour(title)

    def test_a_tricolour_of_the_current_colours_is_removed(self):
        self.assertEqual("Console routes", self.strip("🟣🟥🟣 Console routes"))

    def test_a_tricolour_of_other_colours_is_removed_too(self):
        """A mark left over from before a remap is exactly what goes stale."""
        self.assertEqual("Console routes", self.strip("🟥🟫🟥 Console routes"))

    def test_a_multi_code_point_tricolour_is_counted_as_three(self):
        """Hearts carry U+FE0F, so this is six code points and three clusters."""
        self.assertEqual(3, len(helper().clusters("❤️💛❤️")))
        self.assertEqual("Hearts", self.strip("❤️💛❤️ Hearts"))

    def test_a_title_that_is_only_a_tricolour_leaves_nothing(self):
        """Real state: it happens when a title was never generated."""
        self.assertEqual("", self.strip("🟣🟥🟣"))

    def test_two_tricolours_are_both_removed(self):
        self.assertEqual("Doubled", self.strip("🟣🟥🟣 🟥🟫🟥 Doubled"))

    def test_a_single_decorative_emoji_survives(self):
        """Three-and-a-space is what keeps a user's own decoration safe."""
        self.assertEqual("🎉 Party time", self.strip("🎉 Party time"))

    def test_a_title_with_no_tricolour_is_unchanged(self):
        self.assertEqual("Console routes", self.strip("Console routes"))

    def test_an_empty_title_is_unchanged(self):
        self.assertEqual("", self.strip(""))


class TestSelf(TricolourCase):
    """`--self` prints a line to paste, for a session that has no tools.

    `set_session_title` is an `mcp__ccd*` tool. A console session has none and
    cannot rename itself by any route, so the fallback is to print the command
    and let a person paste it. Reading the title needs no tools, which is why
    the fallback works exactly where the tools do not.
    """

    SESSION = "0123abcd-0000-0000-0000-000000000000"

    def titled(self, title):
        """A fake Claude Code state directory holding `title` for this repo."""
        home = self.tmp / "home"
        project = (home / ".claude" / "projects"
                   / str(self.repo).replace("/", "-") / self.SESSION)
        project.mkdir(parents=True, exist_ok=True)
        if title is not None:
            (project / "custom-title.json").write_text(
                json.dumps({"customTitle": title}), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(HELPER), "--self"],
            cwd=str(self.repo), capture_output=True, text=True, timeout=60,
            env={"HOME": str(home), "PATH": "/usr/bin:/bin",
                 "CLAUDE_CODE_SESSION_ID": self.SESSION})

    def field(self, result, name):
        for line in result.stdout.splitlines():
            if line.startswith(f"{name}\t"):
                return line.split("\t", 1)[1]
        return None

    def test_an_unmarked_title_yields_a_rename_command(self):
        result = self.titled("Console routes")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(f"/rename {TRICOLOUR} Console routes",
                         self.field(result, "rename"))

    def test_a_stale_tricolour_is_replaced_rather_than_stacked(self):
        """Running twice after a remap must not leave two marks."""
        result = self.titled("🔵🔵🟠 Console routes")
        self.assertEqual(f"/rename {TRICOLOUR} Console routes",
                         self.field(result, "rename"))

    def test_an_already_correct_title_emits_no_command(self):
        """A command that changes nothing invites a pointless paste."""
        result = self.titled(f"{TRICOLOUR} Console routes")
        self.assertEqual("yes", self.field(result, "current"))
        self.assertIsNone(self.field(result, "rename"))

    def test_a_session_with_no_title_is_marked_with_the_tricolour_alone(self):
        result = self.titled(None)
        self.assertEqual(f"/rename {TRICOLOUR}", self.field(result, "rename"))

    def test_a_repository_with_no_identicon_still_refuses(self):
        """The fallback must not invent a mark the repository does not have."""
        loose = self.tmp / "loose"
        loose.mkdir()
        result = subprocess.run(
            [sys.executable, str(HELPER), "--self"], cwd=str(loose),
            capture_output=True, text=True, timeout=60)
        self.assertEqual(1, result.returncode)
        self.assertNotIn("rename", result.stdout)


def helper():
    """The helper imported as a module, for the pure string functions."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("tricolour_helper", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
