# The transcript SVG

How to generate the mark that Claude emits at the end of every turn, as an SVG
rather than a raster. Written for whoever is working on the identicon generator:
everything here was measured against real clients on 2 September 2026, and none
of it is derivable from the SVG specification alone.

**This is not `.identicon/repository-identicon.svg`.** That artifact is square,
it goes in a README, and nothing here should change it. This describes a
*transcript literal* — the same kind of thing as the base64 PNG already in the
`CLAUDE.md` block, and it never becomes a file.

## What the clients actually do

Three clients, one account, the same afternoon: Claude on Android, Claude Code on
the web in Chrome, and Claude Desktop driving a remote session.

| behaviour | Android | web / desktop |
|---|---|---|
| `data:image/svg+xml;base64,` | renders | renders |
| `data:image/svg+xml,` percent-encoded | failed once, see below | not retested |
| `width` / `height` attributes | **ignored** | honoured |
| `width` / `height` in `pt` | **ignored** | not retested |
| `style="width:17px"` | **ignored** | not retested |
| omitting `width`/`height` entirely | **ignored** | not retested |
| omitting `viewBox` entirely | **ignored** | not retested |
| `viewBox` aspect ratio | **honoured** | honoured |
| a square SVG | wrapped in a bordered card | wrapped in a bordered card |
| a letterboxed SVG | no card | no card |
| first sight of a unique image | needs a tap | renders |
| any later sight of the same bytes | renders, no tap | renders |

The Android column is not a list of quirks to work around one at a time. It is
one behaviour: **the mark is scaled to fill the column, and the only property
that survives is the aspect ratio.** Six different ways of declaring a size were
tried, including declaring none at all, and every one of them was overridden.

### The sizing law

    rendered size = column width x (mark units / viewBox width)

That is the whole of it, and it is the only lever. It also means the mark's size
is a *fraction of the reader's column* rather than a pixel count, which is
device-independent by construction — the one property none of the raster
approaches could offer.

### Two things this replaces

**The raster needs a different size per client and cannot be told which.** A
62px PNG reads correctly on Android and is four times too large on a desktop; a
17px PNG is correct on a desktop and invisible on Android. The factor was
measured at 4x on the cell (3.65x on the canvas, the difference being the
1-pixel border that does not scale).

**There is no way to detect the client.** `CLAUDE_CODE_ENTRYPOINT` reports where
the *session started*, not what is rendering: it read `remote_mobile` for an
hour while the reader was in Chrome. `origin` in the session record is likewise
stamped at creation. And the question has no answer at emission time anyway —
rendering happens afterwards, possibly on several devices, possibly in a
scrollback days later. `PERMISSIONS.md` documents that variable as the probe for
choosing a render form; for size it is not merely unreliable, it is answering a
different question.

**The text form does not fill the gap.** Android has no glyphs for
U+1CD00-U+1CDE5, so the octants render as tofu. `text-identicon.py`'s docstring
records the block octants as verified against Konsole, which remains true and is
now known to be terminal-only.

## The form to emit

    <svg xmlns="http://www.w3.org/2000/svg" width="84" height="7"
         viewBox="0 0 84 7" preserveAspectRatio="xMinYMid meet">
      <path fill="#rrggbb" d="..."/>
    </svg>

- **`width` and `height` must match the `viewBox`**, not the mark. A client that
  honours them then draws the strip at natural size with the mark at its true
  pixel size; a client that ignores them fits the strip to the column and the
  aspect ratio does the work. One file, both correct, nothing to choose.
- **Keep them.** They are ignored only by Android. Dropping them costs
  correctness in every other consumer and gains nothing.
- **`preserveAspectRatio="xMinYMid meet"`** pins the mark to the left edge. The
  default is `xMidYMid`, which centres it in the empty box.
- **Base64, not percent-encoding** -- provisionally. See the caveat below.
- The ratio is the only number that varies, and `width` and `viewBox` must both
  carry it. Editing one and not the other letterboxes the mark inside the wrong
  box on any compliant renderer, and looks fine on Android — a divergence worth
  asserting against.

### Choosing the ratio

Judged on a phone against a 5x5 mark: 8:1 and 12:1 hold the pattern, 20:1 and
30:1 lose it — the grid degrades into a smudge before it becomes too small to
see. **12:1 is the recommendation.** The ratio is independent of the cell size,
so it is a separate control from `--cell` and has no cap.

## Generating the path

Three encodings of the same 5x5 grid, measured over 500 identicons from real
keys, as characters of `d`:

| method | cell 5 mean | cell 5 max | cell 1 mean | cell 1 max |
|---|---|---|---|---|
| one subpath per filled cell, with `z` | 159.2 | 293 | 136.8 | 253 |
| horizontally merged runs | 89.2 | 155 | 74.9 | 130 |
| **contour trace** | **68.4** | **119** | **60.6** | **109** |

Contour is shorter than run-merging in 397 of 500, tied in 9, longer in 94 —
sparse and checkered grids favour runs, because a scattered pattern is nearly
all perimeter. Picking the shorter of the two per repository gains 1.2
characters over always tracing, which is not worth a second encoder in a program
whose virtue is that it computes a constant.

`z` is redundant for a fill-only path — SVG closes a subpath implicitly for
filling — and drops one character per subpath. The contour form needs it kept if
a stroke is ever added.

### The algorithm

Standard contour tracing; the same step potrace calls path decomposition.

1. For each filled cell, take the edges whose neighbour is empty.
2. Wind them clockwise in a y-down system — top left-to-right, right
   top-to-bottom, bottom right-to-left, left bottom-to-top. Outer contours then
   come out clockwise and holes counter-clockwise, so the **nonzero fill rule
   empties the holes with no special case**.
3. Chain the directed edges into closed loops.
4. Drop collinear vertices.
5. Emit each loop as `M x y` then alternating `h` and `v` deltas, then `z`.

**The check that makes it safe:** the shoelace area of the loops must equal the
count of filled cells. One line, catches a mis-wound hole or a mis-chained loop,
and belongs with the conformance vectors rather than here.

## The one weak claim in here

**Percent-encoding is recorded as failing on Android on a single confounded
trial.** The URI that failed differed from the ones that worked in two ways at
once: it was percent-encoded *and* it declared a width against a mismatched
viewBox. A mismatch ought to letterbox rather than fail, so the encoding is the
likely cause -- but that is an inference, not the measurement the table implies.

Everything else here was varied one property at a time. Re-run it as a
single-variable test before relying on it: identical SVG bytes, one base64, one
percent-encoded, both on a phone. Until then, base64 is the safe default on the
evidence that it works everywhere, rather than on evidence that the alternative
does not.

## The open decision

The byte counts above have two columns because the cell size is not free in a
vector, though not for the reason it matters in a raster.

The border is 1 unit regardless of cell, so the cell sets the *proportion* of
margin to mark: 1/27 at cell 5, 1/7 at cell 1. Unit cells cost 8 characters
fewer and give a visibly fatter frame; cell 5 costs 8 more and matches the
raster exactly. Scaling cannot reconcile them — scaling multiplies the border
too, which is what it means for a proportion to be a proportion.

**Whether the vector should match the raster's proportions, or be allowed its
own, is a design call rather than a measurement.** It has not been made.

## What this costs

A typical contour at cell 1 is about 211 bytes of SVG and a 315-character
literal, against 234 for the 62px PNG. An 81-character premium on every turn,
for a mark that is the right size on a phone, in a browser and in the desktop
remote, with no detection and no choice to make.
