"""The skill carries the generator's PNG into CLAUDE.md, and nothing else.

There are no pinned colours, rasters or vectors here any more. This repository
does not derive an identicon, so a literal recording what one looks like would
be testing Repository-Identicon through a copy -- which is the arrangement that
was just removed.

What is left divides in two, and the split is deliberate:

- **The instruction block**, tested by importing the module and handing it a
  literal directly. No generator, no network, no git. These are the tests that
  must never skip, because the CLAUDE.md write is the one thing that would
  destroy a user's file if it went wrong.
- **The end-to-end run**, which needs the generator installed and skips without
  it. A skip reads exactly like a pass, so it is confined to a single test
  whose absence is obvious rather than spread through the suite.
"""

import base64
import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

SKILL = pathlib.Path(__file__).resolve().parent.parent / "skills" / "repo-identicon"
INSTALLER = SKILL / "repo-identicon.py"

INSTRUCTIONS = "CLAUDE.md"
PNG_NAME = ".identicon/repository-identicon.png"

# A remote that cannot resolve to anything real, so no test can accidentally
# depend on a network or on whatever this checkout's own origin happens to be.
REMOTE = "git@github.com:example/fabricated.git"

# Not a real PNG. `image_literal` base64s whatever bytes are at the path and
# does not parse them, so a recognisable string proves the encoding without
# involving an image.
FAKE_PNG = b"\x89PNG\r\n\x1a\nnot-a-real-image"
FAKE_B64 = base64.b64encode(FAKE_PNG).decode("ascii")


def load():
    """The installer as a module. Its filename has a hyphen, so not `import`."""
    spec = importlib.util.spec_from_file_location("repo_identicon", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


skill = load()

# The generated constants document, taken from the installer rather than
# repeated here: if it ever moves back into a file the user owns, these tests
# should follow it there and keep asserting it is rewritten wholesale.
LOCAL_NAME = skill.LOCAL_NAME


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True,
                   capture_output=True)


def run(*args, cwd=None):
    """The installer, as a user invokes it: a subprocess, not an import."""
    return subprocess.run([sys.executable, str(INSTALLER), *args],
                          capture_output=True, text=True, timeout=120, cwd=cwd)


def generator_available():
    if shutil.which(skill.GENERATOR):
        return True
    return pathlib.Path(skill.SIBLING).exists()


class TreeCase(unittest.TestCase):
    """A throwaway directory holding a fabricated PNG where one is expected."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        png = self.root / PNG_NAME
        png.parent.mkdir(parents=True)
        png.write_bytes(FAKE_PNG)
        self.addCleanup(self._tmp.cleanup)

    def read(self, name):
        return (self.root / name).read_text(encoding="utf-8")


class TestTheLiteral(TreeCase):

    def test_it_is_base64_of_the_png_on_disk(self):
        """The transcript mark and the committed raster are one image. A file
        holding a second copy would be free to disagree, which is why the
        literal is embedded rather than referenced."""
        self.assertEqual(f"![](data:image/png;base64,{FAKE_B64})",
                         skill.image_literal(str(self.root)))

    def test_a_missing_png_is_an_error_and_not_an_empty_literal(self):
        """An empty `data:` URI renders as a broken image in every turn, and
        nothing downstream would report why."""
        (self.root / PNG_NAME).unlink()
        with self.assertRaises(SystemExit):
            skill.image_literal(str(self.root))


class TestTheInstruction(TreeCase):

    def install(self, place=True):
        return skill.instruct(str(self.root), skill.image_literal(str(self.root)),
                              place)

    def test_a_block_is_written_where_there_is_none(self):
        self.install()
        self.assertIn(FAKE_B64, self.read(INSTRUCTIONS))

    def test_surrounding_prose_survives_a_rerun(self):
        """A repository that has rewritten the explanation keeps its wording;
        only the literal is swapped."""
        self.install()
        marker = "A sentence this repository wrote for itself.\n"
        (self.root / INSTRUCTIONS).write_text(
            self.read(INSTRUCTIONS) + marker, encoding="utf-8")

        (self.root / PNG_NAME).write_bytes(b"different-bytes-entirely")
        self.install()

        text = self.read(INSTRUCTIONS)
        self.assertIn(marker, text)
        self.assertNotIn(FAKE_B64, text)
        self.assertIn(base64.b64encode(b"different-bytes-entirely").decode(), text)

    def test_an_unchanged_literal_rewrites_nothing(self):
        """A re-run that touched the file would show up as noise in every diff."""
        self.install()
        self.assertIsNone(self.install())

    def test_two_literals_are_refused(self):
        """Two can disagree with each other and nothing would catch it, so the
        tool stops rather than picking one."""
        self.install()
        text = self.read(INSTRUCTIONS)
        (self.root / INSTRUCTIONS).write_text(text + "\n" + text, encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.install()

    def test_no_instruct_writes_no_block(self):
        """Asking for artifacts is not asking for every turn in the repository
        to change."""
        self.install(place=False)
        self.assertFalse((self.root / INSTRUCTIONS).exists())

    def test_no_instruct_still_refreshes_one_already_there(self):
        """Leaving a committed literal disagreeing with the artifacts beside it
        is worse than either updating or removing it."""
        self.install()
        (self.root / PNG_NAME).write_bytes(b"newer")
        self.install(place=False)
        self.assertIn(base64.b64encode(b"newer").decode(), self.read(INSTRUCTIONS))

    def test_an_unreadable_instructions_file_is_not_treated_as_absent(self):
        """Appending a fresh block over an undecodable file would destroy
        whatever was actually in it."""
        (self.root / INSTRUCTIONS).write_bytes(b"\xff\xfe not utf-8 \xff")
        with self.assertRaises(SystemExit):
            self.install()


class TestItRefusesRatherThanGuesses(TreeCase):

    def test_it_will_not_write_outside_the_root(self):
        with self.assertRaises(SystemExit):
            skill._within(str(self.root), "/etc/passwd")

    def test_an_unknown_flag_is_refused(self):
        result = run(str(self.root), "--dryrun")
        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.root / INSTRUCTIONS).exists(),
                         "a typo fell through to a real install")

    def test_generator_flags_are_only_taken_after_a_separator(self):
        """`--block` is the generator's, and this script must not silently
        swallow it as one of its own."""
        extra = skill.parse(["x", str(self.root), "--", "--block", "5"])[3]
        self.assertEqual(["--block", "5"], extra)

        with self.assertRaises(SystemExit):
            skill.parse(["x", str(self.root), "--block", "5"])


class TestTheSessionTitleSection(TreeCase):
    """Opt-in, and separate from the turn mark: renaming sessions changes what
    the user sees in rows they are not looking at."""

    def install(self, title=None):
        return skill.instruct(str(self.root), skill.image_literal(str(self.root)),
                              True, title)

    def test_it_is_absent_unless_asked_for(self):
        self.install()
        self.assertNotIn(skill.TITLE_HEADING, self.read(INSTRUCTIONS))

    def test_it_is_added_on_request(self):
        self.install(title=True)
        self.assertIn(skill.TITLE_HEADING, self.read(INSTRUCTIONS))

    def test_adding_it_twice_writes_one_copy(self):
        self.install(title=True)
        self.install(title=True)
        self.assertEqual(1, self.read(INSTRUCTIONS).count(skill.TITLE_HEADING))

    def test_a_plain_rerun_neither_adds_nor_removes_it(self):
        """A re-run picks up a changed mark. It must not decide this too."""
        self.install(title=True)
        before = self.read(INSTRUCTIONS)
        self.install()
        self.assertEqual(before, self.read(INSTRUCTIONS))

    def test_it_can_be_removed_without_taking_the_block_with_it(self):
        self.install(title=True)
        self.install(title=False)
        text = self.read(INSTRUCTIONS)
        self.assertNotIn(skill.TITLE_HEADING, text)
        self.assertIn(FAKE_B64, text)

    def test_removing_it_leaves_a_later_section_intact(self):
        """The section ends at the next heading, not at the end of the file."""
        self.install(title=True)
        (self.root / INSTRUCTIONS).write_text(
            self.read(INSTRUCTIONS) + "\n## Something this repository added\n\nKeep me.\n",
            encoding="utf-8")
        self.install(title=False)
        text = self.read(INSTRUCTIONS)
        self.assertNotIn(skill.TITLE_HEADING, text)
        self.assertIn("Keep me.", text)


@unittest.skipUnless(generator_available(),
                     "Repository-Identicon is not installed; the end-to-end "
                     "path cannot be exercised")
class TestEndToEnd(unittest.TestCase):
    """One test, deliberately. It is the only thing here that needs the
    generator, and a suite that skipped wholesale would look green."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "remote", "add", "origin", REMOTE)
        self.addCleanup(self._tmp.cleanup)

    def test_the_literal_matches_the_png_the_generator_wrote(self):
        result = run(str(self.root))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

        png = (self.root / PNG_NAME).read_bytes()
        expected = base64.b64encode(png).decode("ascii")
        self.assertIn(expected, (self.root / INSTRUCTIONS).read_text())

    def test_the_local_document_carries_every_block_size(self):
        """The point of the file: the reader picks, so all five must be there."""
        self.assertEqual(0, run(str(self.root)).returncode)
        text = (self.root / LOCAL_NAME).read_text()
        for block in (1, 2, 3, 4, 5):
            with self.subTest(block=block):
                self.assertIn(f"- block {block}: ![](data:image/png;base64,", text)

    def test_the_local_document_carries_the_text_renderings(self):
        self.assertEqual(0, run(str(self.root)).returncode)
        text = (self.root / LOCAL_NAME).read_text()
        for heading in ("## Tricolour", "## Sextant", "## Octant"):
            with self.subTest(heading=heading):
                self.assertIn(heading, text)

    def test_no_local_writes_no_local_document(self):
        self.assertEqual(0, run(str(self.root), "--no-local").returncode)
        self.assertFalse((self.root / LOCAL_NAME).exists())

    def test_a_second_run_leaves_the_local_document_untouched(self):
        self.assertEqual(0, run(str(self.root)).returncode)
        before = (self.root / LOCAL_NAME).read_bytes()
        self.assertEqual(0, run(str(self.root)).returncode)
        self.assertEqual(before, (self.root / LOCAL_NAME).read_bytes())

    def test_the_user_s_own_local_file_is_never_touched(self):
        """CLAUDE.local.md is the documented place for a user's own project
        preferences. This plugin writes a file it owns outright instead, because
        sharing one with hand-written content means parsing that content
        correctly on every run and destroying it when the parse is wrong."""
        mine = self.root / "CLAUDE.local.md"
        content = "# Mine\n\nSandbox URL: http://localhost:9999\n"
        mine.write_text(content, encoding="utf-8")

        self.assertEqual(0, run(str(self.root)).returncode)

        self.assertEqual(content, mine.read_text(encoding="utf-8"))
        self.assertTrue((self.root / LOCAL_NAME).exists())
        self.assertNotEqual(LOCAL_NAME, "CLAUDE.local.md")


if __name__ == "__main__":
    unittest.main()
