#!/usr/bin/env python3
"""Which open sessions belong to this repository's identicon.

Reads `.identicon/repository-identicon.tricolour` -- three emoji squares the
generator writes -- for a reference repository and for each candidate path, and
reports the candidates whose triple is identical.

    tricolour.py [--repo PATH] [CANDIDATE ...]

**The match is on the triple's contents, never on the path.** Two sessions in
separate git worktrees of one repository have different working directories and
the same seed, so they must group together; two repositories that merely sit
near each other on disk must not. Comparing the artifact gets both right, and
gets them right without this script knowing anything about how the mark is
derived.

It also means a repository with no `.identicon/` matches nothing and is
reported as nothing, so a caller cannot accidentally act on one.

Output is one record per line, `field<TAB>value`:

    triple	🟥🟫🟥
    match	/home/justin/Code/Isolated/Repository-Identicon/some-worktree

Exit 1, with no `match` lines, when the reference repository has no triple.
There is nothing to apply in that case, and an empty success would read as
"checked, nothing matched" rather than "this repository has no identicon".
"""

import os
import subprocess
import sys

DIRECTORY = ".identicon"
STEM = "repository-identicon"
TRICOLOUR_NAME = f"{DIRECTORY}/{STEM}.tricolour"


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


def triple_at(path):
    """The triple for the repository containing `path`, or None.

    None covers every uninteresting case at once -- not a directory, not a
    repository, no identicon installed, unreadable -- because the caller does
    the same thing in all of them: leave that session alone.
    """
    root = toplevel(path)
    if root is None:
        return None
    try:
        with open(os.path.join(root, TRICOLOUR_NAME), encoding="utf-8") as handle:
            value = handle.read().strip()
    except (OSError, UnicodeDecodeError):
        return None
    return value or None


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

    wanted = triple_at(reference)
    if wanted is None:
        print(f"no identicon for {reference}", file=sys.stderr)
        return 1

    print(f"triple\t{wanted}")
    for candidate in args:
        if triple_at(candidate) == wanted:
            print(f"match\t{candidate}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
