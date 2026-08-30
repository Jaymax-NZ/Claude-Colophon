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
        _, _, _, extra = skill.parse(["x", str(self.root), "--", "--block", "5"])
        self.assertEqual(["--block", "5"], extra)

        with self.assertRaises(SystemExit):
            skill.parse(["x", str(self.root), "--block", "5"])


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


if __name__ == "__main__":
    unittest.main()
