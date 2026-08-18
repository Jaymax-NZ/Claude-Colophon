#!/usr/bin/env python3
"""Give a repository an identicon that Claude emits at the end of every turn.

Run once per repository. What lands in the target repository is four data files
and a markdown block -- no code, no dependency on this script, nothing to keep
updated. Re-run only if the git remote changes.

    "${CLAUDE_PLUGIN_ROOT}/skills/repo-identicon/repo-identicon.py" [PATH]

Writes `.identicon/` at the repository root -- base64 for the transcript
literal, a raster, a vector and the colour -- and adds (or refreshes) the
instruction block in `CLAUDE.md` that carries the same image inline.

Shipped as the `repo-identicon` skill of the `claude-colophon` plugin. The
derivation is specified by the Repository-Identicon standard, whose conformance
apparatus -- a vendored reference library and its pinned vectors -- deliberately
stays with the standard rather than travelling here: this file computes a
constant, and carrying a test suite to do it would be absurd. The two are held
to each other by a test where the vectors live.

**Why an instruction rather than a hook**, given that a hook would not depend on
the model choosing to comply. No hook output field can display an image: a
`systemMessage` is delivered as plain text with the event name prefixed to each
line. The only channel in a GUI chat client that renders markdown is an
assistant message, and only the model writes those. So the deterministic
mechanism cannot render, and the mechanism that renders cannot be made
deterministic. This is the second of the two, chosen knowingly.

**Size is chosen by the cell, `--cell 1` to `--cell 5`, defaulting to 3.** The
client sizes the image from the PNG's own dimensions, and raw HTML is printed
as literal text so `<img width>` cannot override it. Pixels are the only
control there is. Verified by rendering one identicon at 15x15 and 84x84 in a
single message: the small one sat inline in the text flow, the large one was
wrapped in a bordered card.

The cell is what anyone actually has an opinion about -- how heavy the mark
sits beside a line of text -- so that, and not the total, is the knob. Each of
the five gives a canvas that divides exactly: 7, 12, 17, 22, 27.

A repository's choice is read back out of its own installed PNG, so re-running
keeps it. Pass `--cell` only to change it.

The derivation is Claude-State-Panel's `docs/project-identicon-spec.md`, whose
pattern and colour conform to stewartlord/identicon.js. The conformance
apparatus -- the vendored library and its pinned vectors -- stays in that
repository, where it is checked. Shipping it here to install a per-repository
constant would be carrying a test suite to compute a string that never changes.
"""

import base64
import hashlib
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib

GRID = 5

# The canvas is described by its cell rather than by its total, because the cell
# is the thing anyone actually has an opinion about -- how heavy the mark sits
# beside a line of text -- and because a total picked directly can fail to
# divide. 30 did: it left a stray pixel after the grid and the border, so the
# mark sat fractionally off-centre.
#
# A one-pixel border at every cell size. It is a separating margin, not a frame;
# scaling it would make it a design element, and at cell 1 it would swallow the
# pattern.
BORDER = 1

# 1 to 5. Below 1 there is no pattern, and above 5 the client stops rendering it
# inline and wraps it in a bordered card -- verified by rendering one identicon
# at 15x15 and 84x84 in a single message.
CELLS = (1, 2, 3, 4, 5)
DEFAULT_CELL = 3


def canvas(cell):
    """Total pixel side for a cell size: 5 cells plus a border either end.

    Every value this yields is one the general geometry below resolves back to
    exactly -- `_geometry(canvas(n)) == (n, BORDER)` for all of CELLS -- so the
    two ways of describing the same canvas cannot disagree.
    """
    return GRID * cell + 2 * BORDER

# The reference fixes both rather than deriving them from the digest.
SATURATION = 0.7
LIGHTNESS = 0.5

# An optional committed one-line seed overriding the derived key, so a project
# can pin its identicon across a rename or a move between forges.
OVERRIDE_FILENAME = ".claude-state-identicon"

# One directory rather than four root entries, so a fifth rendering costs
# nothing at the top level. Hidden, because these are derived artifacts of a
# repository rather than part of it -- and nothing that reads them is browsing
# a listing to find them. Every consumer arrives by a path it was told.
DIRECTORY = ".identicon"

# Four files, each usable by a consumer that knows nothing about this tool and
# does no parsing at all. That is the whole design: `cat .identicon/colour`
# yields a colour, `<img src=".identicon/icon.svg">` yields an image. Rolling
# them into one file would be readable by every tool that knows the format,
# which is one tool.
#
# `png.b64` is not a duplicate of `icon.png`. The CLAUDE.md instruction embeds
# the image as a `data:` URI, which needs exactly these characters and cannot
# reference a path; a README needs a path and cannot use base64. Two consumers,
# two forms, one image -- and the tests prove they are the same image.
B64_NAME = f"{DIRECTORY}/png.b64"
PNG_NAME = f"{DIRECTORY}/icon.png"
SVG_NAME = f"{DIRECTORY}/icon.svg"
COLOUR_NAME = f"{DIRECTORY}/colour"

# What the artifact was called before it moved into the directory. Removed on
# install, so a repository does not end up carrying both and no consumer has to
# guess which one is current.
SUPERSEDED = ("repository-identicon-png.b64",)

INSTRUCTIONS_NAME = "CLAUDE.md"

MARKDOWN_IMAGE = re.compile(r"!\[\]\(data:image/png;base64,[A-Za-z0-9+/=]+\)")


# --------------------------------------------------------------------------
# The key. Getting this right matters more than anything else here: two tools
# that disagree about the key agree about nothing else.


def normalise_key(path):
    """Reduce a filesystem path to a stable string.

    The *fallback* key. A path is not stable across machines, containers, or
    the per-session git worktrees the desktop app creates.
    """
    absolute = os.path.abspath(os.path.expanduser(str(path)))
    return absolute.rstrip(os.sep) or os.sep


def normalise_remote_url(url):
    """Reduce a git remote URL to `host/owner/repo`, lowercased.

    Every spelling of one repository must collapse to one key, so an SSH
    checkout and an HTTPS checkout of the same project share an identicon:

        git@github.com:Owner/Repo.git
        https://github.com/Owner/Repo.git
        https://token@github.com/Owner/Repo
        ssh://git@github.com:2222/Owner/Repo.git   ->  github.com/owner/repo

    The host is kept, so `github.com/a/b` and `gitlab.com/a/b` stay distinct.
    Returns None for a local-path remote, which is no more portable than the
    working directory and so earns no special treatment.
    """
    if not url:
        return None
    url = url.strip().rstrip("/")
    if not url or url.startswith("/") or url.startswith("file://"):
        return None

    if "://" in url:
        scheme, _, rest = url.partition("://")
        if scheme.lower() == "file":
            return None
        authority, _, path = rest.partition("/")
    elif ":" in url:
        # scp-like: [user@]host:path
        authority, _, path = url.partition(":")
    else:
        return None

    if "@" in authority:
        authority = authority.rpartition("@")[2]
    host = authority.partition(":")[0]  # drop any port

    path = path.strip("/")
    if path.lower().endswith(".git"):
        path = path[: -len(".git")]

    parts = [part for part in path.split("/") if part]
    if not host or not parts:
        return None
    return "/".join([host] + parts).lower()


def _git(args, cwd):
    """Run a git command, returning stripped stdout or None if it fails."""
    try:
        completed = subprocess.run(["git", "-C", str(cwd), *args],
                                   capture_output=True, text=True)
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def repo_toplevel(path):
    """The working tree root, or None outside a repository.

    In a worktree this is the worktree's own root, not the main checkout --
    which is exactly why it is not the key.
    """
    return _git(["rev-parse", "--show-toplevel"], path)


def repo_remote_url(path):
    """The origin URL, falling back to whichever remote is listed first."""
    url = _git(["remote", "get-url", "origin"], path)
    if url:
        return url
    remotes = _git(["remote"], path)
    if not remotes:
        return None
    return _git(["remote", "get-url", remotes.splitlines()[0].strip()], path)


def override_key(directory):
    """The committed seed at `directory`, if there is a usable one."""
    if not directory:
        return None
    candidate = os.path.join(directory, OVERRIDE_FILENAME)
    try:
        with open(candidate, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        return None
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return None


def resolve_key(path=None):
    """Return (key, source) for a project directory.

    Precedence, most specific first:

      override   a committed .claude-state-identicon at the repository root
      remote     host/owner/repo from the git remote -- the portable one
      toplevel   the repository root path, for a repository with no remote
      path       the directory itself, outside a repository

    Only `remote` and `override` survive being cloned somewhere else. The two
    path-shaped sources are honest fallbacks, not equivalents, which is why the
    installer reports which one it used.
    """
    directory = normalise_key(path if path else os.getcwd())
    toplevel = repo_toplevel(directory)

    committed = override_key(toplevel or directory)
    if committed:
        return committed, "override"

    if toplevel:
        remote = normalise_remote_url(repo_remote_url(directory))
        if remote:
            return remote, "remote"
        return normalise_key(toplevel), "toplevel"

    return directory, "path"


# --------------------------------------------------------------------------
# The pattern and the colour, per stewartlord/identicon.js.


def _digest(key):
    """MD5 as lowercase hex.

    Hex rather than bytes because the reference consumes the digest as *hex
    characters* -- one nibble per grid cell, and the last seven characters as
    the hue.
    """
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def identicon_grid(key):
    """Return the 5x5 grid as a list of rows of bools.

    The reference's own comment: the first 15 characters of the hash control
    the pixels (even/odd), drawn down the middle first, then mirrored outwards.
    Characters 0-4 fill the centre column top to bottom, 5-9 fill column 1 and
    mirror onto 3, 10-14 fill column 0 and mirror onto 4. Even is foreground.
    """
    digest = _digest(key)
    grid = [[False] * GRID for _ in range(GRID)]
    for index in range(15):
        painted = int(digest[index], 16) % 2 == 0
        column, row = divmod(index, GRID)
        grid[row][2 - column] = painted
        grid[row][2 + column] = painted
    return grid


def identicon_hue(key):
    """Hue as a fraction of a turn, from the last seven hex characters.

    28 bits over 0xfffffff, per the reference. Drawn from the same digest as
    the grid, so colour and pattern cannot drift apart.
    """
    return int(_digest(key)[-7:], 16) / 0xFFFFFFF


def _quantise(value):
    """Round half up, not half to even.

    Python's round() is half to even; the reference language's is half up.
    Following Python here would put this out of conformance on the boundary.
    """
    return int(value * 255 + 0.5)


def _hsl_to_rgb(hue, saturation, lightness):
    """The reference's own HSL conversion, transliterated.

    Not `colorsys.hls_to_rgb`. The reference mutates its working values while
    building the sector table and indexes it with `h|16` and `h|8` -- an
    integer trick for the six-sector rotation. Standard conversion agrees on
    most inputs, but this is a conformance target, so the arithmetic is
    reproduced rather than approximated.
    """
    hue *= 6.0
    fraction = hue % 1

    spread = saturation * (lightness if lightness < 0.5 else 1 - lightness)
    high = lightness + spread
    doubled = spread * 2
    low = high - doubled

    sectors = [
        high,
        high - fraction * spread * 2,
        low,
        low,
        low + fraction * doubled,
        low + doubled,
    ]

    sector = int(hue)
    return (sectors[sector % 6],
            sectors[(sector | 16) % 6],
            sectors[(sector | 8) % 6])


def identicon_colour(key, saturation=SATURATION, lightness=LIGHTNESS):
    """The foreground colour as an (r, g, b) triple of 0-255 ints."""
    red, green, blue = _hsl_to_rgb(identicon_hue(key), saturation, lightness)
    return (_quantise(red), _quantise(green), _quantise(blue))


# --------------------------------------------------------------------------
# Raster.


def _geometry(size):
    """Cell size and margin for a square canvas.

    Cells are deliberately generous relative to the canvas so a small icon
    still reads as a pattern rather than a smudge.
    """
    cell = max(1, round(size / 5.5))
    if cell * GRID > size:
        cell = max(1, size // GRID)
    margin = (size - cell * GRID) // 2
    return cell, margin


def render_rgba(key, size):
    """Raw RGBA bytes for a square identicon. Unfilled cells are transparent."""
    grid = identicon_grid(key)
    red, green, blue = identicon_colour(key)
    cell, margin = _geometry(size)

    back = bytes((0, 0, 0, 0))
    fore = bytes((red, green, blue, 255))

    rows = []
    for y in range(size):
        row = bytearray()
        grid_y = (y - margin) // cell if cell else -1
        inside_y = margin <= y < margin + cell * GRID
        for x in range(size):
            grid_x = (x - margin) // cell if cell else -1
            inside_x = margin <= x < margin + cell * GRID
            row += fore if (inside_x and inside_y and grid[grid_y][grid_x]) else back
        rows.append(bytes(row))
    return b"".join(rows)


def _png_chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def encode_png(rgba, width, height):
    """Minimal 8-bit RGBA PNG encoder. Flat colour blocks compress to nothing."""
    stride = width * 4
    raw = b"".join(b"\x00" + rgba[y * stride:(y + 1) * stride] for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", header)
            + _png_chunk(b"IDAT", zlib.compress(raw, 9))
            + _png_chunk(b"IEND", b""))


def render_png(key, cell=DEFAULT_CELL):
    size = canvas(cell)
    return encode_png(render_rgba(key, size), size, size)


def hex_colour(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def render_svg(key, cell_size=DEFAULT_CELL):
    """The same mark as the PNG, in the same geometry, as vector.

    The viewBox is the pixel canvas rather than the 5x5 grid, so the margin the
    raster leaves around the pattern is reproduced exactly and the two
    renderings are the same picture rather than merely the same pattern.

    `width` and `height` are declared as well as the viewBox: a bare viewBox
    scales to whatever container it lands in, and markdown's `![]()` supplies
    no container, so a README would render it at full column width. A consumer
    that wants it bigger says so -- `<img src="..." width="120">` -- which is
    the right way round, since the default use is an inline mark.
    """
    size = canvas(cell_size)
    grid = identicon_grid(key)
    colour = hex_colour(identicon_colour(key))
    cell, margin = _geometry(size)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">'
    ]
    for row in range(GRID):
        for column in range(GRID):
            if grid[row][column]:
                parts.append(
                    f'<rect x="{margin + column * cell}" y="{margin + row * cell}" '
                    f'width="{cell}" height="{cell}" fill="{colour}"/>'
                )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def b64_for(key, cell=DEFAULT_CELL):
    """The committed artifact: base64 of the PNG, no wrapper, no newline."""
    return base64.b64encode(render_png(key, cell)).decode("ascii")


def image_for(key, cell=DEFAULT_CELL):
    """The markdown line the model emits.

    Empty alt text: the icon is the whole message. Alt text would print if the
    image failed to load, and a printed name beside the mark is redundant when
    you already know which window you are looking at.
    """
    return f"![](data:image/png;base64,{b64_for(key, cell)})"


# --------------------------------------------------------------------------
# Installation. Two files, both inside one repository, and nothing else -- see
# `_within` and `_write_atomically` for what that is worth in practice.


def _within(root, path):
    """The path, guaranteed to be inside `root`, or a refusal.

    Both are fully resolved first, so a symlinked repository root does not read
    as an escape and a symlink *out* of the tree does not read as containment.
    This script is pointed at a directory the caller names, and the whole of
    its authority is to write two files under that directory; a check is
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
    new bytes are not yet down. Losing that race costs a scratch artifact here
    and the user's entire `CLAUDE.md` there, so everything goes through the
    same temp-file-and-rename, which is atomic within a filesystem. `os.replace`
    also resolves the destination symlink rather than replacing the link.

    Takes `str` or `bytes`; the PNG is the one artifact that is not text.
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


def installed_cell(root):
    """The cell size a repository is already using, read out of its own PNG.

    The choice is not recorded in a config file because it does not need to be:
    the installed artifact *is* the record, and one that cannot fall out of step
    with what is actually there. Re-running without `--cell` therefore keeps
    whatever the repository chose, rather than silently reverting it to the
    default and rewriting every artifact plus the CLAUDE.md literal.

    Returns None if there is nothing installed, or if what is installed is not
    a size this tool produces -- in which case the caller falls back to the
    default rather than trying to honour a width it cannot reproduce.
    """
    path = os.path.join(root, PNG_NAME)
    raw = _read(path, binary=True)
    if not raw or len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height = struct.unpack(">II", raw[16:24])
    if width != height:
        return None
    for cell in CELLS:
        if canvas(cell) == width:
            return cell
    return None


def block_for(key, cell=DEFAULT_CELL):
    """The CLAUDE.md section, written once and thereafter only refreshed."""
    return f"""## End every response with this repository's identicon

Emit this line, verbatim, as the last line of every response in this
repository. Nothing after it.

{image_for(key, cell)}

It is a PNG of this repository's identicon: a 5x5 grid inside a one-pixel
border, derived from the repository's identity rather than from its path, so it
is the same in every checkout on every machine.

The pixel size is deliberately not written down here. A re-run refreshes the
image above but leaves this prose alone -- as it must, so that a repository
which has rewritten the explanation keeps its wording -- and a number nothing
refreshes is a number that goes stale. `.identicon/icon.png` is the record.

`{DIRECTORY}/` holds the same mark in every form a consumer might want, each
usable with no parsing at all:

| file | for |
|---|---|
| `{B64_NAME}` | the literal above; a `data:` URI cannot reference a path |
| `{PNG_NAME}` | a README, or anywhere that refuses SVG |
| `{SVG_NAME}` | a README on a forge that renders it; anything scalable |
| `{COLOUR_NAME}` | `#rrggbb`, for a prompt, a badge, or a theme |

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


def install(path, cell=None):
    """Write the artifacts and place or refresh the instruction.

    Returns a report: the key, its source, the cell size, and what changed. An
    existing block is refreshed *in place* by swapping the one literal, so a
    repository that has edited the surrounding prose keeps its edits.

    `cell` of None means "whatever this repository already chose", falling back
    to the default only where nothing is installed. A re-run is for picking up a
    changed remote, and it must not quietly resize a mark someone settled on.

    Everything is read and decided before anything is written, so a refusal
    leaves the repository exactly as it was found rather than half-installed.
    """
    key, source = resolve_key(path)
    root = repo_toplevel(path) or normalise_key(path)
    if not os.path.isdir(root):
        raise SystemExit(f"not a directory: {root}")

    if cell is None:
        cell = installed_cell(root) or DEFAULT_CELL

    instructions = _within(root, os.path.join(root, INSTRUCTIONS_NAME))

    # Every artifact ends with a newline, so each is a well-formed text file and
    # `$(cat ...)` still yields it clean -- the shell strips exactly one.
    png = render_png(key, cell)
    artifacts = {
        B64_NAME: base64.b64encode(png).decode("ascii") + "\n",
        PNG_NAME: png,
        SVG_NAME: render_svg(key, cell),
        COLOUR_NAME: hex_colour(identicon_colour(key)) + "\n",
    }

    text = _read(instructions) or ""
    found = MARKDOWN_IMAGE.findall(text)
    if len(found) > 1:
        raise SystemExit(
            f"{instructions} carries {len(found)} identicon literals; they can "
            "disagree with each other. Remove all but one, then re-run.")

    if found:
        updated = MARKDOWN_IMAGE.sub(image_for(key, cell), text, count=1)
    else:
        separator = "" if not text else ("\n" if text.endswith("\n") else "\n\n")
        header = f"# {os.path.basename(root)}\n\n" if not text else ""
        updated = text + separator + header + block_for(key, cell)

    changed = []
    for name, wanted in artifacts.items():
        target = _within(root, os.path.join(root, name))
        if _read(target, binary=isinstance(wanted, bytes)) != wanted:
            _write_atomically(target, wanted)
            changed.append(target)

    if updated != text:
        _write_atomically(instructions, updated)
        changed.append(instructions)

    # A repository carrying both the old artifact and the new one leaves every
    # consumer guessing which is current, and the stale one goes on looking
    # authoritative forever.
    removed = []
    for name in SUPERSEDED:
        stale = _within(root, os.path.join(root, name))
        if os.path.exists(stale):
            os.unlink(stale)
            removed.append(stale)

    return {"key": key, "source": source, "root": root, "cell": cell,
            "changed": changed, "removed": removed, "refreshed": bool(found)}


PORTABLE = {"remote", "override"}


def report(result, stream=sys.stdout):
    cell = result["cell"]
    print(f"key    {result['key']}", file=stream)
    print(f"source {result['source']}", file=stream)
    print(f"cell   {cell}px  ({canvas(cell)}x{canvas(cell)} PNG)", file=stream)
    root = result["root"]
    for path in result["changed"]:
        print(f"wrote  {os.path.relpath(path, root)}", file=stream)
    for path in result["removed"]:
        print(f"removed {os.path.relpath(path, root)}  (superseded)", file=stream)
    if not result["changed"] and not result["removed"]:
        print("       already up to date", file=stream)
    if result["source"] not in PORTABLE:
        print(
            f"\nWarning: the key is a filesystem path, so this identicon will "
            f"change\nif the repository is cloned elsewhere or opened in a git "
            f"worktree.\nGive the repository a git remote, or commit a one-line "
            f"{OVERRIDE_FILENAME}\nnaming it, and re-run.",
            file=stream)


# Every flag is read-only except the absence of all of them. Listed so that a
# typo -- `--dryrun` for `--dry-run` -- is refused rather than silently falling
# through to a real install, which is the one mistake here that writes files
# the caller did not ask for.
FLAGS = {"--help", "-h", "--key", "--b64", "--png", "--svg", "--colour",
         "--color", "--dry-run"}

# The one option that takes a value. Kept separate from FLAGS so that a bare
# `--cell` with nothing after it is an error rather than being swallowed.
VALUED = {"--cell"}


def parse(argv):
    """(flags, cell, paths). Raises SystemExit with a usage message on nonsense.

    Hand-rolled rather than argparse, for one reason: an unrecognised option
    must be refused, never ignored. This script's default action writes files,
    so a swallowed `--dryrun` is the one mistake that does real damage.
    """
    flags, paths, cell = set(), [], None
    remaining = list(argv)
    while remaining:
        argument = remaining.pop(0)
        name, _, inline = argument.partition("=")
        if name in VALUED:
            value = inline if _ else (remaining.pop(0) if remaining else None)
            if value is None:
                raise SystemExit(f"{name} needs a value, one of "
                                 f"{', '.join(str(c) for c in CELLS)}")
            if not value.isdigit() or int(value) not in CELLS:
                raise SystemExit(
                    f"{name} must be one of {', '.join(str(c) for c in CELLS)} "
                    f"(pixels per grid square), not {value!r}")
            cell = int(value)
        elif argument.startswith("-"):
            if argument not in FLAGS:
                raise SystemExit(f"unknown option: {argument}\n\n{__doc__}")
            flags.add(argument)
        else:
            paths.append(argument)

    if len(paths) > 1:
        raise SystemExit(f"expected at most one path, got {len(paths)}")
    return flags, cell, paths


def main(argv):
    try:
        flags, cell, paths = parse(argv[1:])
    except SystemExit as refusal:
        print(refusal, file=sys.stderr)
        return 2

    path = paths[0] if paths else os.getcwd()

    if flags & {"--help", "-h"}:
        print(__doc__)
        return 0

    if not os.path.isdir(os.path.expanduser(path)):
        print(f"not a directory: {path}", file=sys.stderr)
        return 2

    key, source = resolve_key(path)

    # For the read-only flags, an unspecified cell means the repository's own
    # choice, exactly as it does for an install -- so `--png` previews what is
    # committed rather than what the default would produce.
    root = repo_toplevel(path) or normalise_key(path)
    preview = cell or installed_cell(root) or DEFAULT_CELL

    if "--key" in flags:
        print(f"{key}\t{source}")
        return 0
    if "--b64" in flags:
        print(b64_for(key, preview))
        return 0
    if "--png" in flags:
        sys.stdout.buffer.write(render_png(key, preview))
        return 0
    if "--svg" in flags:
        sys.stdout.write(render_svg(key, preview))
        return 0
    if flags & {"--colour", "--color"}:
        print(hex_colour(identicon_colour(key)))
        return 0
    if "--dry-run" in flags:
        print(f"key    {key}")
        print(f"source {source}")
        print(f"cell   {preview}px  ({canvas(preview)}x{canvas(preview)} PNG)"
              + ("" if cell else "  (kept from what is installed)"
                 if installed_cell(root) else "  (default)"))
        print(f"under  {root}")
        for name in (B64_NAME, PNG_NAME, SVG_NAME, COLOUR_NAME,
                     INSTRUCTIONS_NAME):
            print(f"would write {name}")
        for name in SUPERSEDED:
            if os.path.exists(os.path.join(root, name)):
                print(f"would remove {name}  (superseded)")
        return 0

    report(install(path, cell))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
