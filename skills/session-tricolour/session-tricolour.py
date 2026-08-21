#!/usr/bin/env python3
"""Prefix a Claude session's name with its repository's tricolour.

The deterministic half of the feature: reading the mark, recognising it in a
title, putting it there, taking it out, and working out which sessions belong to
this repository. The renaming itself is a tool call and belongs to the model --
nothing here talks to a session manager, and nothing here needs to.

**This script never derives a tricolour.** It reads one, from `.identicon/`, or
it reports that there is none. The squares are produced by the identicon
generator from a derivation that is specified and conformance-tested with the
standard; a second implementation is a second answer, and two answers about one
repository's identity is the failure this arrangement exists to prevent. See
`docs/session-tricolour-spec.md`.

    session-tricolour.py --status  [PATH]
    session-tricolour.py --triple  [PATH]
    session-tricolour.py --tag     TITLE [PATH]
    session-tricolour.py --untag   TITLE [PATH]
    session-tricolour.py --matches URL   [PATH]
    session-tricolour.py --enable  [PATH]
    session-tricolour.py --disable [PATH]
    session-tricolour.py --selftest

PATH defaults to the working directory and is resolved to the repository root,
so running from a subdirectory is fine.

Exit codes are the interface for the two questions that are answered by a code
rather than by output: **3** means this repository has no identicon, and **4**
means it has one but has opted out of tagging. Both are ordinary answers. A
caller that treats either as an error has misread the feature: the absence of an
identicon is the absence of a mark, not a fault to repair.

Standard library only.
"""

import importlib.util
import os
import re
import subprocess
import sys

# --------------------------------------------------------------------------
# The artifacts. Names are the generator's, repeated here rather than imported,
# because they are the *interface* between two programs: if the generator
# renames a file, this must fail loudly at a known place rather than silently
# following along and finding nothing.
# --------------------------------------------------------------------------

DIRECTORY = ".identicon"
STEM = "repository-identicon"

# Preferred first. It does not exist yet -- the generator will split the
# tricolour out of the text form into a file of its own -- and preferring it
# now means that split needs no change here: the day the file appears, it wins.
TRICOLOUR_NAME = f"{DIRECTORY}/{STEM}.tricolour"

# The interim reading, and the only place in this program that knows the text
# form's shape. Two lines of octants, the last one ending in a space and the
# three squares. Taking the tail is a kludge with a scheduled end; keeping it
# to one function is what makes the end cheap.
TEXT_NAME = f"{DIRECTORY}/{STEM}.txt"

INSTRUCTIONS_NAME = "CLAUDE.md"

# The switch. Its presence in CLAUDE.md is what opts a repository in, so this
# heading is load-bearing: it is how removal finds what to remove, and how a
# fresh session's instruction was got there in the first place.
HEADING = "## Tag this session with this repository's tricolour"

SQUARES = 3

NO_IDENTICON = 3
OPTED_OUT = 4


def _vendored(relative, name):
    """Load a sibling of this file within the plugin, or None if it is absent.

    A plugin is copied whole and has no dependency mechanism, so the pieces
    reach each other by path. Absence is survivable for some callers and fatal
    for others, which is why this returns rather than raises.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The palette, for *recognising* squares in a title -- never for choosing them.
# Imported rather than copied: one list of nine characters, in one place, in
# the module that defines what they mean.
_TEXT = _vendored(os.path.join("..", "repo-identicon", "text-identicon.py"),
                  "text_identicon")

# The generator, for identity resolution and nothing else: which remote names
# this repository, and how two spellings of one remote collapse to one key.
# Both are the standard's answers to "are these the same repository", and a
# second implementation of either is a second answer -- so they are shared.
#
# Nothing else is taken from it. Not its atomic write, not its git helpers,
# however convenient: it is a vendored copy that will be replaced wholesale when
# the tricolour becomes a file of its own, and every borrowed private is an
# entanglement to be undone on that day. Couple to the standard, never to the
# mechanics of whoever currently implements it.
_GENERATOR = _vendored(os.path.join("..", "repo-identicon", "repo-identicon.py"),
                       "repo_identicon")


def palette_characters():
    """The nine squares, as a set. Requires the vendored renderer."""
    if _TEXT is None:
        raise SystemExit(
            "cannot recognise a tricolour: the vendored text renderer is "
            "missing from the plugin, and its palette is the only definition "
            "of which characters are squares")
    return {entry[0] for entry in _TEXT.PALETTE}


# --------------------------------------------------------------------------
# Where we are
# --------------------------------------------------------------------------

def repository_root(path=None):
    """The repository root containing `path`, or `path` itself outside one."""
    start = os.path.abspath(path or os.getcwd())
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             cwd=start, capture_output=True, text=True,
                             check=False, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return start
    return top.stdout.strip() if top.returncode == 0 else start


def read_tricolour(root):
    """This repository's three squares, or None if it has no identicon.

    The dedicated file if it exists, otherwise the tail of the text form. The
    fallback is the interim reading and this is the only function that performs
    it; when the generator ships `.tricolour`, delete the second half and
    nothing else changes.
    """
    dedicated = os.path.join(root, TRICOLOUR_NAME)
    if os.path.exists(dedicated):
        with open(dedicated, encoding="utf-8") as handle:
            squares = handle.read().strip()
        return squares or None

    text = os.path.join(root, TEXT_NAME)
    if not os.path.exists(text):
        return None
    with open(text, encoding="utf-8") as handle:
        lines = [line for line in handle.read().split("\n") if line.strip()]
    if not lines:
        return None
    tail = lines[-1].rstrip()[-SQUARES:]
    return tail if len(tail) == SQUARES else None


def opted_in(root):
    """Whether CLAUDE.md carries the tagging section."""
    path = os.path.join(root, INSTRUCTIONS_NAME)
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as handle:
        return HEADING in handle.read()


# --------------------------------------------------------------------------
# Titles
#
# One shape, recognised and produced in one place: three squares, a space, the
# rest. Everything else about a title is none of our business and is preserved
# exactly, including whatever the auto-titler chose.
# --------------------------------------------------------------------------

def _prefix_pattern():
    squares = "".join(re.escape(c) for c in sorted(palette_characters()))
    # A trailing VS16 after a square is tolerated on the way in: we never write
    # one, but a client that round-trips a title through its own encoder might.
    return re.compile(f"^(?:[{squares}]️?){{{SQUARES}}}[  ]*")


def existing_prefix(title):
    """The tricolour already on `title`, squares only, or None."""
    match = _prefix_pattern().match(title)
    if not match:
        return None
    return "".join(c for c in match.group(0) if c in palette_characters())


def untag(title):
    """`title` with any tricolour prefix removed.

    A title that is *only* a tricolour keeps it, because the alternative is
    renaming a session to the empty string -- destroying the only thing left
    that identifies it in order to tidy up a prefix.
    """
    stripped = _prefix_pattern().sub("", title)
    return stripped if stripped.strip() else title


def tag(title, tricolour):
    """`title` carrying `tricolour`, replacing any tricolour already there.

    Idempotent, and self-correcting rather than merely safe to repeat: a title
    marked with a stale triple -- after a re-seed, or a repository rename --
    converges on the current one instead of accumulating both.
    """
    return f"{tricolour} {untag(title)}".strip()


# --------------------------------------------------------------------------
# Which sessions are ours
#
# This reads a remote URL to *compare* it, never to produce a mark from it. The
# two look alike and are not: comparison asks whether two names denote one
# repository, which is exactly what the generator's normalisation is for.
# --------------------------------------------------------------------------

def matches(url, root):
    """Whether `url` denotes the repository at `root`."""
    if _GENERATOR is None:
        raise SystemExit("cannot match sessions: the generator is missing from "
                         "the plugin, and its normalisation is the definition "
                         "of when two remotes are one repository")
    mine = _GENERATOR.repo_remote_url(root)
    if not mine:
        return False
    return (_GENERATOR.normalise_remote_url(url)
            == _GENERATOR.normalise_remote_url(mine))


# --------------------------------------------------------------------------
# The switch
# --------------------------------------------------------------------------

SECTION = f"""{HEADING}

At the end of your first turn in this repository, and on any later turn where
you notice it missing, make this session's name begin with this repository's
three coloured squares, so that a list of sessions can be told apart without
being read.

The squares are the whole of
`{TRICOLOUR_NAME}` if that file exists,
and otherwise the last three characters of the last line of
`{TEXT_NAME}`.
Read them from there. Do not work them out from the colour, the remote, or
anything else: one repository, one mark, one thing that produces it.

Then, if this client gives you a tool that can rename a session:

- ask it for this session's current name;
- if that name already starts with those three squares, do nothing;
- otherwise set the name to the three squares, a space, and the name as it was
  -- replacing any three squares already on the front.

A prefix rather than a suffix, because a list of session names truncates on the
right, which is where a suffix would be.

**Not at the start of a session.** The name is generated from the first prompt
a few seconds in, and anything set before that is overwritten.

If this client has no such tool, or refuses to rename this session, do nothing
and say nothing -- this is a convenience about legibility and must not become
the noisiest thing in the transcript. If it can rename other sessions but not
this one, this one can be named by another session, which must be *given* these
three squares rather than working them out for itself.

To stop this, remove this section: its presence is the switch.
"""


def _section_bounds(text):
    """(start, end) of the tagging section in `text`, or None."""
    start = text.find(HEADING)
    if start == -1:
        return None
    following = re.compile(r"^## ", re.MULTILINE).search(text, start + len(HEADING))
    return start, following.start() if following else len(text)


def _write(root, text):
    """Replace CLAUDE.md, via a temporary file and a rename.

    The rename is the point: an interrupted run leaves the previous file whole
    rather than truncated. Someone else\'s prose is in there.
    """
    path = os.path.join(root, INSTRUCTIONS_NAME)
    temporary = f"{path}.session-tricolour.tmp"
    with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def enable(root):
    """Add the tagging section. Returns what happened."""
    path = os.path.join(root, INSTRUCTIONS_NAME)
    existing = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            existing = handle.read()
    if _section_bounds(existing):
        return "already opted in"
    separator = "" if not existing else ("\n" if existing.endswith("\n\n")
                                         else "\n\n" if existing.endswith("\n")
                                         else "\n\n")
    _write(root, existing + separator + SECTION)
    return f"opted in: added the section to {INSTRUCTIONS_NAME}"


def disable(root):
    """Remove the tagging section. Returns what happened."""
    path = os.path.join(root, INSTRUCTIONS_NAME)
    if not os.path.exists(path):
        return "already opted out"
    with open(path, encoding="utf-8") as handle:
        existing = handle.read()
    bounds = _section_bounds(existing)
    if not bounds:
        return "already opted out"
    start, end = bounds
    _write(root, (existing[:start].rstrip("\n") + "\n" + existing[end:]).rstrip("\n") + "\n")
    return f"opted out: removed the section from {INSTRUCTIONS_NAME}"


# --------------------------------------------------------------------------
# Self-check
# --------------------------------------------------------------------------

def selftest():
    triple = "\U0001F7EA\U0001F7EA\U0001F7E5"
    other = "\U0001F7E9\U0001F7E5\U0001F7E9"

    assert tag("Fix the parser", triple) == f"{triple} Fix the parser"
    # Idempotent, and convergent on a changed mark.
    assert tag(tag("Fix the parser", triple), triple) == f"{triple} Fix the parser"
    assert tag(f"{triple} Fix the parser", other) == f"{other} Fix the parser"
    assert untag(f"{triple} Fix the parser") == "Fix the parser"
    assert untag("Fix the parser") == "Fix the parser"
    assert existing_prefix(f"{triple} Fix the parser") == triple
    assert existing_prefix("Fix the parser") is None

    # Two squares are not a tricolour, and a title of squares is not a prefix
    # to be stripped -- stripping it would leave nothing at all.
    assert existing_prefix("\U0001F7EA\U0001F7EA Fix") is None
    assert untag(triple) == triple

    # A variation selector on the way in is tolerated; we never write one.
    assert untag(f"\U0001F7EA️\U0001F7EA\U0001F7E5 Fix") == "Fix"

    # Round trip through a title that already looks like ours.
    assert untag(tag("a", triple)) == "a"

    # The section is findable, removable, and removal is idempotent.
    import tempfile
    with tempfile.TemporaryDirectory() as root:
        with open(os.path.join(root, INSTRUCTIONS_NAME), "w") as handle:
            handle.write("# Project\n\nProse.\n\n## After\n\nMore.\n")
        assert not opted_in(root)
        enable(root)
        assert opted_in(root)
        assert enable(root) == "already opted in"
        after = open(os.path.join(root, INSTRUCTIONS_NAME)).read()
        assert "## After" in after and "More." in after, after
        disable(root)
        assert not opted_in(root)
        assert "## After" in open(os.path.join(root, INSTRUCTIONS_NAME)).read()
        assert disable(root) == "already opted out"

    # Reading is a read: with no artifacts there is no tricolour, and that is
    # an answer rather than a failure.
    with tempfile.TemporaryDirectory() as root:
        assert read_tricolour(root) is None
        os.makedirs(os.path.join(root, DIRECTORY))
        with open(os.path.join(root, TEXT_NAME), "w", encoding="utf-8") as handle:
            handle.write(f"      \n\U0001CD32\U0001CD31\U0001CD0A {triple}\n")
        assert read_tricolour(root) == triple
        # The dedicated file wins the moment it exists.
        with open(os.path.join(root, TRICOLOUR_NAME), "w", encoding="utf-8") as handle:
            handle.write(other + "\n")
        assert read_tricolour(root) == other
    return True


# --------------------------------------------------------------------------

def _main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    verb, rest = argv[0], argv[1:]

    if verb == "--selftest":
        selftest()
        print("selftest: ok")
        return 0

    if verb in ("--tag", "--untag", "--matches"):
        if not rest:
            print(f"{verb} needs an argument", file=sys.stderr)
            return 2
        subject, rest = rest[0], rest[1:]
    else:
        subject = None

    if len(rest) > 1:
        print(f"expected at most one path, got {len(rest)}", file=sys.stderr)
        return 2
    root = repository_root(rest[0] if rest else None)

    if verb == "--untag":
        print(untag(subject))
        return 0

    tricolour = read_tricolour(root)

    if verb == "--status":
        print(f"root      {root}")
        print(f"tricolour {tricolour or '(none: no identicon here)'}")
        print(f"tagging   {'on' if opted_in(root) else 'off'}")
        if tricolour and not opted_in(root):
            print(f"\nThis repository has a mark but has opted out of tagging "
                  f"sessions with it.\nTo opt in: {sys.argv[0]} --enable")
        return 0

    if verb == "--enable":
        if tricolour is None:
            print("no identicon here: run /repo-identicon first", file=sys.stderr)
            return NO_IDENTICON
        print(enable(root))
        return 0

    if verb == "--disable":
        print(disable(root))
        return 0

    if verb == "--matches":
        return 0 if matches(subject, root) else 1

    if tricolour is None:
        print("no identicon here", file=sys.stderr)
        return NO_IDENTICON

    if verb == "--triple":
        print(tricolour)
        return 0

    if verb == "--tag":
        if not opted_in(root):
            print("this repository has opted out of session tagging",
                  file=sys.stderr)
            return OPTED_OUT
        print(tag(subject, tricolour))
        return 0

    print(f"unknown option: {verb}\n\n{__doc__}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
