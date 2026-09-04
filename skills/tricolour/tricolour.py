#!/usr/bin/env python3
"""Which open sessions belong to this repository's identicon.

Reads `renders.tricolour` from `.identicon/settings.json` -- the emoji tricolour
the generator writes, already rendered -- for a reference repository and for
each candidate path, and reports the candidates whose tricolour is identical.

    tricolour.py [--repo PATH] [CANDIDATE ...]
    tricolour.py [--repo PATH] --self

**The match is on the tricolour's contents, never on the path.** Two sessions in
separate git worktrees of one repository have different working directories and
the same seed, so they must group together; two repositories that merely sit
near each other on disk must not. Comparing the artifact gets both right, and
gets them right without this script knowing anything about how the mark is
derived -- including which glyphs the tricolour is drawn from, which is not
fixed.

It also means a repository with no `.identicon/` matches nothing and is
reported as nothing, so a caller cannot accidentally act on one.

Output is one record per line, `field<TAB>value`:

    tricolour	🟥🟫🟥
    match	/home/justin/Code/Isolated/Repository-Identicon/some-worktree

Exit 1, with no `match` lines, when the reference repository has no tricolour.
There is nothing to apply in that case, and an empty success would read as
"checked, nothing matched" rather than "this repository has no identicon".
"""

import json
import os
import subprocess
import sys
import unicodedata

DIRECTORY = ".identicon"
SETTINGS_NAME = f"{DIRECTORY}/settings.json"

# Where the tricolour sits in the generator's settings. A rendered string, ready
# to use -- this script does not assemble it from the shape-and-colour pairs
# under `identicon.current.tricolour`, because assembling it would be deriving
# it, and the generator has already done that.
RENDER_PATH = ("renders", "tricolour")


def toplevel(path):
    """The repository root containing `path`, or None.

    Asking git rather than walking up: a worktree's root is not the directory
    holding `.git`, and only git knows the difference. Worktrees are the whole
    reason this lookup exists -- the desktop app gives parallel sessions their
    own -- so getting them wrong would defeat the grouping.
    """
    if not os.path.isdir(path):
        return None
    try:
        done = subprocess.run(["git", "-C", path, "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, check=False)
    except OSError:
        return None
    if done.returncode != 0:
        return None
    return done.stdout.strip() or None


def tricolour_at(path):
    """The tricolour for the repository containing `path`, or None.

    None covers every uninteresting case at once -- not a directory, not a
    repository, no identicon installed, unreadable -- because the caller does
    the same thing in all of them: leave that session alone.
    """
    root = toplevel(path)
    if root is None:
        return None
    try:
        with open(os.path.join(root, SETTINGS_NAME), encoding="utf-8") as handle:
            settings = json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None

    value = settings
    for step in RENDER_PATH:
        if not isinstance(value, dict):
            return None
        value = value.get(step)
    if not isinstance(value, str):
        return None
    return value.strip() or None


# --------------------------------------------------------------------------
# The session's own title, for a session that cannot set it.
#
# `set_session_title` is an `mcp__ccd*` tool, injected by the desktop app. A
# console session and a headless run have none, so they cannot rename
# themselves by any route: `/rename` is a built-in the client executes and the
# model never sees, and a prompt enqueued by CronCreate arrives as text rather
# than as a command. Writing the title files does not work either -- the client
# holds the title in memory and writes those files on change rather than
# reading them back. All four were tested on 2026-09-04.
#
# What is left is to print the line a person can paste. Reading the title needs
# no tools, so the fallback works exactly where the tools do not.

# Claude Code stores a project under the working directory path with the
# separators replaced.
STATE = os.path.expanduser("~/.claude/projects")

# Attach to the preceding cluster rather than starting a new one. One emoji is
# not one code point: a variation selector, a skin-tone modifier, a keycap or a
# zero-width joiner each continue the cluster before them.
_VARIATION = {0xFE0E, 0xFE0F}
_MODIFIERS = range(0x1F3FB, 0x1F400)
_JOINER = 0x200D
_KEYCAP = 0x20E3


def clusters(text):
    """`text` split into grapheme clusters, near enough for emoji.

    Counting code points reads a heart-based tricolour -- U+2764 U+FE0F three
    times, six code points -- as six glyphs and so as "not a tricolour", which
    leaves a stale mark in place. That is the one failure stripping exists to
    prevent, so the counting has to be cluster-wise.
    """
    out, joined = [], False
    for character in text:
        point = ord(character)
        attaches = (joined
                    or point in _VARIATION
                    or point in _MODIFIERS
                    or point == _KEYCAP
                    or point == _JOINER
                    or unicodedata.combining(character))
        if out and attaches:
            out[-1] += character
        else:
            out.append(character)
        joined = point == _JOINER
    return out


def _pictographic(cluster):
    """Whether a cluster reads as an emoji rather than as text."""
    first = cluster[0]
    return unicodedata.category(first) == "So" or 0x1F000 <= ord(first) <= 0x1FAFF


def strip_tricolour(title):
    """`title` with any leading tricolours removed.

    Recognised by position and count -- three pictographic clusters at the very
    start, then a space or the end -- never by which glyphs they are. Matching
    the current value would only ever find marks that are already correct, and
    matching squares would skip every tricolour drawn from another shape.

    Repeatedly, because removing one of two leaves the other.
    """
    while title:
        parts = clusters(title)
        if len(parts) < 3 or not all(_pictographic(p) for p in parts[:3]):
            return title
        if len(parts) == 3:
            return ""
        if parts[3] != " ":
            return title
        title = "".join(parts[4:])
    return title


def own_title():
    """This session's title as the local client last wrote it, or None.

    Two files carry it and neither needs a tool. `custom-title.json` holds a
    title set by `/rename` or by `set_session_title`; the transcript holds
    `aiTitle` for a session the server named and nobody has renamed. Reading
    only `aiTitle` finds nothing for any session this skill has already
    touched, which is every session it would be run on twice.
    """
    session = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session:
        return None
    project = os.path.join(STATE, os.getcwd().replace(os.sep, "-"))

    custom = os.path.join(project, session, "custom-title.json")
    try:
        with open(custom, encoding="utf-8") as handle:
            title = json.load(handle).get("customTitle")
        if title:
            return title
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        pass

    title = None
    try:
        with open(os.path.join(project, f"{session}.jsonl"), encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict):
                    title = record.get("customTitle") or record.get("aiTitle") or title
    except (OSError, UnicodeDecodeError):
        return None
    return title or None


def report_self(wanted):
    """Print the tricolour, this session's title, and the line to paste."""
    print(f"tricolour\t{wanted}")

    title = own_title()
    if title is None:
        print("title\t(unknown)")
    else:
        print(f"title\t{title}")

    bare = strip_tricolour(title or "")
    marked = f"{wanted} {bare}" if bare else wanted
    if title == marked:
        print("current\tyes")
        return 0
    print(f"rename\t/rename {marked}")
    return 0


def main(argv):
    args = argv[1:]
    reference = os.getcwd()
    myself = False

    if args and args[0] == "--repo":
        if len(args) < 2:
            raise SystemExit("--repo needs a path")
        reference, args = args[1], args[2:]

    if args and args[0] == "--self":
        myself, args = True, args[1:]

    if args and args[0].startswith("-"):
        if args[0] in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        raise SystemExit(f"unrecognised flag: {args[0]}")

    wanted = tricolour_at(reference)
    if wanted is None:
        print(f"no identicon for {reference}", file=sys.stderr)
        return 1

    if myself:
        return report_self(wanted)

    print(f"tricolour\t{wanted}")
    for candidate in args:
        if tricolour_at(candidate) == wanted:
            print(f"match\t{candidate}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
