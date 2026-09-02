#!/usr/bin/env python3
"""Carry a repository's identicon into `CLAUDE.md`.

This script does not derive anything. The identicon -- the key, the colour, the
grid, and every rendered artifact under `.identicon/` -- is produced by
Repository-Identicon, which is the standard and its reference implementation.
This file runs that generator and then does the one thing the generator does
not: place or refresh the inline `data:` image in `CLAUDE.md` that Claude Code
emits at the end of every turn.

**Why the derivation is not here.** It used to be, vendored, on the argument
that a Claude Code plugin is copied whole and has no dependency mechanism. The
cost of that argument was two implementations of one constant, free to drift,
held together only by a test comparing committed literals. A mark that differs
between the plugin and the standard is worse than a mark that needs a second
tool installed, because nothing tells you it has happened.

Packaging -- how a user who installed only the plugin obtains the generator --
is deliberately unresolved. For now the generator is a prerequisite and its
absence is a clear error rather than a silent fallback to a second derivation.

    repo-identicon.py [PATH] [--no-instruct] [--dry-run]
                      [--session-title | --no-session-title]
                      [-- GENERATOR ARGS]

`--session-title` adds an opt-in section asking Claude to carry the identicon
tricolour in the session title as well; `--no-session-title` removes it. Neither
is the default, because a re-run exists to pick up a changed mark and must not
turn a separate behaviour on or off on the way past.

`--` forwards the remainder to the generator untouched, so `--block`, `--seed`,
`--remap` and the rest are reachable without being re-declared here.
"""

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


# --------------------------------------------------------------------------
# The generator. Located, never reimplemented.

GENERATOR = "repository-identicon"

# Where to look when it is not on PATH. A sibling checkout is how these three
# repositories sit on the machine they are developed on, and finding it there
# saves an install step during development. It is a convenience, not a
# contract: anything shipped depends on PATH.
SIBLING = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))),
    "Repository-Identicon", "repository-identicon.py")


def find_generator():
    """The generator's command line, or a refusal naming what is missing."""
    found = shutil.which(GENERATOR)
    if found:
        return [found]
    if os.path.exists(SIBLING) and os.access(SIBLING, os.X_OK):
        return [SIBLING]
    raise SystemExit(
        f"{GENERATOR} not found on PATH, and no checkout at {SIBLING}.\n"
        "This plugin no longer carries its own copy of the derivation. Install\n"
        "Repository-Identicon, or check it out beside this repository.")


def run_generator(path, extra=()):
    """Run `apply` against `path`. The generator's own output goes to the user.

    Its exit status is passed through rather than interpreted. It refuses for
    reasons this script has no business second-guessing -- a mapping version it
    will not draw, a path outside a repository -- and each refusal already
    carries the remedy in its message.
    """
    command = [*find_generator(), "apply", *extra, path]
    completed = subprocess.run(command)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


# --------------------------------------------------------------------------
# The artifact layout, which belongs to the standard. These names are read, not
# computed: this script needs to find the PNG the generator wrote, and that is
# the whole of its interest in the directory.

DIRECTORY = ".identicon"
STEM = "repository-identicon"
PNG_NAME = f"{DIRECTORY}/{STEM}.png"

INSTRUCTIONS_NAME = "CLAUDE.md"

MARKDOWN_IMAGE = re.compile(r"!\[\]\(data:image/png;base64,[A-Za-z0-9+/=]+\)")

# The session-title instruction, which is opt-in and separate from the turn
# mark. Emitting an image at the end of a reply changes nothing outside the
# conversation; renaming sessions changes what the user sees in their session
# list, including sessions they are not looking at. The second is not implied by
# wanting the first, so it is not installed by wanting the first.
TITLE_HEADING = "## Carry the identicon in the session title"

TITLE_INSTRUCTION = f"""{TITLE_HEADING}

On an early turn, run `/tricolour`. It puts this repository's emoji tricolour
at the front of this session's title, and of every other open session on this
repository, so that the session list is scannable by project rather than by
reading each row.

The tricolour is the whole mark for a single line: a session title cannot hold
the 5x5 pattern, which needs two.

Opt out by deleting this section. Nothing regenerates it -- `--session-title`
adds it and `--no-session-title` removes it, and neither is the default.
"""

# From the heading to the next one at the same level, or to the end. Written as
# a lookahead so the following section's heading is not consumed with it.
TITLE_SECTION = re.compile(
    r"\n*" + re.escape(TITLE_HEADING) + r".*?(?=\n## |\Z)", re.S)


# --------------------------------------------------------------------------
# Writing, guarded. Preserved unchanged from the version that carried the
# derivation: these are file-safety properties, not identicon behaviour.


def _within(root, path):
    """The path, guaranteed to be inside `root`, or a refusal.

    Both are fully resolved first, so a symlinked repository root does not read
    as an escape and a symlink *out* of the tree does not read as containment.
    This script is pointed at a directory the caller names, and the whole of
    its authority is to write one file under that directory; a check is
    cheaper than trusting every path that reaches it.
    """
    real_root = os.path.realpath(root)
    real_path = os.path.realpath(path)
    if real_path != real_root and not real_path.startswith(real_root + os.sep):
        raise SystemExit(f"refusing to write outside {real_root}: {real_path}")
    return real_path


def _write_atomically(path, data):
    """Replace a file's contents, or leave it exactly as it was.

    A plain open-and-write has a window in which the file is truncated and the
    new bytes are not yet down. Losing that race costs the user's entire
    `CLAUDE.md`, so the write goes through a temp file and a rename, which is
    atomic within a filesystem. `os.replace` also resolves the destination
    symlink rather than replacing the link.
    """
    target = os.path.realpath(path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    binary = isinstance(data, bytes)
    handle, temporary = tempfile.mkstemp(dir=os.path.dirname(target),
                                         prefix=".identicon-")
    try:
        mode, encoding = ("wb", None) if binary else ("w", "utf-8")
        with os.fdopen(handle, mode, encoding=encoding) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except BaseException:
        # Including KeyboardInterrupt: an interrupted run must not leave a
        # dotfile behind in someone's repository.
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def _read(path, binary=False):
    """A file's contents, or None if absent. Unreadable is an error, not absent.

    The difference matters: treating an undecodable `CLAUDE.md` as missing
    would append a fresh block and destroy whatever was actually in it.
    """
    if not os.path.exists(path):
        return None
    try:
        if binary:
            with open(path, "rb") as handle:
                return handle.read()
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError) as error:
        raise SystemExit(f"cannot read {path}: {error}")


# --------------------------------------------------------------------------
# The instruction block, which is this repository's whole remaining job.


def image_literal(root):
    """The generator's PNG as a markdown inline image.

    A `data:` URI is the one form the artifact directory cannot supply, because
    it carries bytes and cannot reference a path. That is the entire reason
    this script exists alongside the generator rather than inside it.
    """
    png = _read(_within(root, os.path.join(root, PNG_NAME)), binary=True)
    if png is None:
        raise SystemExit(
            f"{PNG_NAME} is missing after the generator ran; nothing to embed.")
    return f"![](data:image/png;base64,{base64.b64encode(png).decode('ascii')})"


def block_for(literal):
    """The CLAUDE.md section, written once and thereafter only refreshed."""
    return f"""## Sign every response with this repository's identicon

Emit this line, verbatim, as the last line of every response in this
repository. Nothing after it.

**Also emit it immediately before asking the user anything** -- as the last
line of the text preceding a question, including before a tool call that puts
a question to them. A turn that ends in a question may never reach a turn-end
at all, so it is both the turn most likely to lose the mark and the one where
the reader most needs it: they are being asked to stop and decide, and which
project is asking is part of the question.

{literal}

It is a PNG of this repository's identicon: a 5x5 grid inside a border,
derived from the repository's identity rather than from its path, so it is the
same in every checkout on every machine.

The pixel size is deliberately not written down here. A re-run refreshes the
image above but leaves this prose alone -- as it must, so that a repository
which has rewritten the explanation keeps its wording -- and a number nothing
refreshes is a number that goes stale.
`{PNG_NAME}` is the record.

`{DIRECTORY}/` holds the same mark in every form a consumer might want, each
usable with no parsing at all. `{PNG_NAME}` for a README or anywhere that
refuses SVG, `{DIRECTORY}/{STEM}.svg` where a forge renders it,
`{DIRECTORY}/{STEM}.colour` for a prompt or a badge, and the text renderings
for a terminal. The directory itself is the list; the generator decides what
is in it.

Each name repeats the directory on purpose, so that a file still says what it is
once it has been copied somewhere else.

The literal above is base64 of the PNG, which is the one form a file cannot
provide: a `data:` URI carries its bytes and cannot reference a path.

Do not edit any of them by hand, including the literal above -- regenerate the
whole set with `/repo-identicon`.

**Why this is an instruction rather than a hook**, given that an instruction
depends on compliance and a hook does not: no hook output field can display an
image. A hook's `systemMessage` arrives as plain text, one event-name prefix
per line. The only channel in a GUI chat client that renders markdown is an
assistant message, and only the model writes those. So the deterministic
mechanism cannot render, and the mechanism that renders cannot be made
deterministic. This is the second of the two, chosen knowingly.
"""


# --------------------------------------------------------------------------
# The local document. Repository constants, every variant a user might pick,
# written to a gitignored file so the choice of which to use stays with the
# reader rather than with whoever ran the generator last.
#
# **It is not `CLAUDE.local.md`.** That file is the documented place for a
# user's own project preferences -- sandbox URLs, test data -- and it exists in
# repositories that have never heard of this plugin. A generated document must
# not share a file with hand-written content, because keeping them apart then
# depends on parsing the user's prose correctly on every run, and the failure
# mode is destroying it.
#
# `.claude/rules/` is the purpose-built alternative: files there load at launch
# with the same priority as `.claude/CLAUDE.md`, one file per topic, so this one
# can be owned outright and rewritten without reading anything first.
# Named for the subject, not for today's contents. It holds constants now;
# anything else per-checkout and identicon-shaped belongs here too, and a file
# called `identicon-constants.md` would have to be renamed to accept it.
#
# **No `paths:` frontmatter, deliberately.** An unscoped rule is re-injected
# from disk after compaction, exactly like the project-root CLAUDE.md. A scoped
# one is only reloaded when Claude reads a file it matches, which for a mark
# emitted on every turn would mean it silently stops being available partway
# through a long session.
LOCAL_NAME = ".claude/rules/identicon.md"
SETTINGS_NAME = f"{DIRECTORY}/settings.json"

BLOCKS = (1, 2, 3, 4, 5)


def _settings(root):
    """The generator's settings for this repository, or a refusal."""
    path = _within(root, os.path.join(root, SETTINGS_NAME))
    raw = _read(path)
    if raw is None:
        raise SystemExit(f"{SETTINGS_NAME} is missing; run the generator first.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise SystemExit(f"cannot parse {path}: {error}")


def _rendered_png(root, block):
    """One block size as PNG bytes, asked of the generator.

    The sizes are not in settings, so they are requested rather than derived.
    Five subprocesses, once per repository, is the right price for never
    computing a pixel here.
    """
    command = [*find_generator(), "render", "--block", str(block),
               "--format", "png", "--out", "-", root]
    done = subprocess.run(command, capture_output=True)
    if done.returncode != 0:
        raise SystemExit(done.stderr.decode("utf-8", "replace").strip()
                         or f"generator failed rendering block {block}")
    return done.stdout


def local_document(root):
    """Every variant, laid out for a reader to choose from."""
    settings = _settings(root)
    renders = settings.get("renders", {})
    drawing = renders.get("blockDrawing", {})

    lines = [
        "# Identicon constants for this repository",
        "",
        "Generated from `.identicon/settings.json` and rewritten in full on every",
        "run of `/repo-identicon`. **Do not edit it** -- put anything of your own in",
        "`CLAUDE.local.md`, which this plugin never touches.",
        "",
        "It is gitignored, and it holds every rendering variant so that which one to",
        "use is your choice rather than this repository's. State that choice in",
        "`~/.claude/CLAUDE.md`, where it applies to every repository with an",
        "identicon.",
        "",
        "## Turn mark",
        "",
        "One per block size. Emit the one matching your size preference.",
        "",
    ]
    for block in BLOCKS:
        literal = (f"![](data:image/png;base64,"
                   f"{base64.b64encode(_rendered_png(root, block)).decode('ascii')})")
        lines.append(f"- block {block}: {literal}")

    lines += ["", "## Tricolour", "", renders.get("tricolour", "(absent)"), ""]

    for name in ("sextant", "octant", "ascii"):
        rows = drawing.get(name)
        if not rows:
            continue
        lines += [f"## {name.capitalize()}", "", "```", *rows, "```", ""]

    return "\n".join(lines).rstrip("\n") + "\n"


def write_local(root):
    """Write the local document, or None if it was already current."""
    target = _within(root, os.path.join(root, LOCAL_NAME))
    wanted = local_document(root)
    if _read(target) == wanted:
        return None
    _write_atomically(target, wanted)
    return target


def instruct(root, literal, place=True, title=None):
    """Place or refresh the literal in CLAUDE.md. Returns what changed.

    An existing block is refreshed *in place* by swapping the one literal, so a
    repository that has edited the surrounding prose keeps its edits.

    `place=False` refreshes an existing literal but does not add one. Asking
    for artifacts is not asking for every turn in the repository to change, and
    withdrawing an instruction a repository has committed is not something to
    do as a side effect either -- so an existing block is kept current, and an
    absent one stays absent.

    `title` is True to add the session-title section, False to remove it, and
    None to leave whatever is there. None is the default because a re-run
    exists to pick up a changed mark, and must not quietly turn a behaviour on
    or off that the repository decided about separately.
    """
    instructions = _within(root, os.path.join(root, INSTRUCTIONS_NAME))
    text = _read(instructions) or ""

    found = MARKDOWN_IMAGE.findall(text)
    if len(found) > 1:
        raise SystemExit(
            f"{instructions} carries {len(found)} identicon literals; they can "
            "disagree with each other. Remove all but one, then re-run.")

    if found:
        updated = MARKDOWN_IMAGE.sub(literal, text, count=1)
    elif not place:
        updated = text
    else:
        separator = "" if not text else ("\n" if text.endswith("\n") else "\n\n")
        header = f"# {os.path.basename(root)}\n\n" if not text else ""
        updated = text + separator + header + block_for(literal)

    present = TITLE_SECTION.search(updated) is not None
    if title is True and not present:
        joiner = "" if updated.endswith("\n\n") else (
            "\n" if updated.endswith("\n") else "\n\n")
        updated = updated + joiner + TITLE_INSTRUCTION
    elif title is False and present:
        updated = TITLE_SECTION.sub("", updated).rstrip("\n") + "\n"

    if updated == text:
        return None
    _write_atomically(instructions, updated)
    return instructions


# --------------------------------------------------------------------------
# Command line.


def parse(argv):
    """Arguments, or a refusal. An unrecognised flag never reaches a write."""
    path, place, dry, extra, title, local = None, True, False, [], None, True
    rest = argv[1:]

    if "--" in rest:
        cut = rest.index("--")
        rest, extra = rest[:cut], rest[cut + 1:]

    for argument in rest:
        if argument in ("--help", "-h"):
            print(__doc__.strip())
            raise SystemExit(0)
        if argument == "--no-instruct":
            place = False
        elif argument == "--dry-run":
            dry = True
        elif argument == "--session-title":
            title = True
        elif argument == "--no-session-title":
            title = False
        elif argument == "--no-local":
            local = False
        elif argument.startswith("-"):
            raise SystemExit(f"unrecognised flag: {argument}\n"
                             "Generator flags go after `--`.")
        elif path is None:
            path = argument
        else:
            raise SystemExit(f"unexpected argument: {argument}")

    return os.path.abspath(path or os.getcwd()), place, dry, extra, title, local


def main(argv):
    path, place, dry, extra, title, local = parse(argv)

    if dry:
        run_generator(path, ["--check", *extra])
        return 0

    run_generator(path, extra)

    # The generator writes at the repository root and reports it; this script
    # is handed the same path and resolves the root the same way the generator
    # does -- by asking git, not by guessing.
    root = _toplevel(path)
    literal = image_literal(root)
    changed = instruct(root, literal, place, title)

    # Not "literal updated": the literal, the session-title section, or both may
    # have changed, and naming only one of them is wrong half the time.
    print(f"{os.path.join(root, INSTRUCTIONS_NAME)} "
          f"{'updated' if changed else 'unchanged'}")

    if local:
        written = write_local(root)
        print(f"{os.path.join(root, LOCAL_NAME)} "
              f"{'updated' if written else 'unchanged'}")
    return 0


def _toplevel(path):
    """The repository root containing `path`, or `path` itself.

    Asking git rather than walking up: a worktree's root is not the directory
    holding `.git`, and only git knows the difference.
    """
    try:
        completed = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False)
    except OSError:
        return path
    if completed.returncode != 0:
        return path
    return completed.stdout.strip() or path


if __name__ == "__main__":
    sys.exit(main(sys.argv))
