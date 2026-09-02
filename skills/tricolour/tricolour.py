#!/usr/bin/env python3
"""Which open sessions belong to this repository's identicon.

Reads `renders.tricolour` from `.identicon/settings.json` -- the emoji tricolour
the generator writes, already rendered -- for a reference repository and for
each candidate path, and reports the candidates whose tricolour is identical.

    tricolour.py [--repo PATH] [CANDIDATE ...]

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


def main(argv):
    args = argv[1:]
    reference = os.getcwd()

    if args and args[0] == "--repo":
        if len(args) < 2:
            raise SystemExit("--repo needs a path")
        reference, args = args[1], args[2:]
    elif args and args[0].startswith("-"):
        if args[0] in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        raise SystemExit(f"unrecognised flag: {args[0]}")

    wanted = tricolour_at(reference)
    if wanted is None:
        print(f"no identicon for {reference}", file=sys.stderr)
        return 1

    print(f"tricolour\t{wanted}")
    for candidate in args:
        if tricolour_at(candidate) == wanted:
            print(f"match\t{candidate}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
