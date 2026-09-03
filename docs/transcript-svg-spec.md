# The transcript SVG

How to generate the mark that Claude emits at the end of every turn, as an SVG
rather than a raster. Written for whoever is working on the identicon generator:
everything here was measured against real clients on 2 September 2026, and none
of it is derivable from the SVG specification alone.

**This is not `.identicon/repository-identicon.svg`.** That artifact is square,
it goes in a README, and nothing here should change it. This describes a
*transcript literal* — the same kind of thing as the base64 PNG already in the
`CLAUDE.md` block, and it never becomes a file.

## What this has to achieve

Stated as constraints, because most of them turned out to be forced rather than
chosen:

1. **One mark, emitted at the end of every turn, legible on Android, on the web
   and in the desktop app.** A session migrates between them mid-conversation --
   this one went Android, then Chrome, then desktop -- so a mark sized for one
   is wrong on the next within the same transcript.
2. **The session cannot know where it is displayed.** Not merely unavailable:
   undefined. Rendering happens after emission, possibly on several devices,
   possibly in a scrollback days later. `CLAUDE_CODE_ENTRYPOINT` and the
   session's `origin` both report where it *started*.
3. **A per-platform size can therefore only be something the reader states**,
   and that statement decays exactly as the mark does -- it goes stale at the
   moment they switch devices, which is the same problem one layer up.
4. **The size should be adjustable at output**, per reader and ideally per
   platform.
5. **The artifact should be as small as possible**, since it lives in a
   repository and in `CLAUDE.md`.

Constraints 4 and 5 pull against the encoding: raw SVG is editable by changing
two digits, base64 is not editable at all, and Android accepts only base64. See
**The cost model** below for what that forces.

## What the clients actually do

Three clients, one account, the same afternoon: Claude on Android, Claude Code on
the web in Chrome, and Claude Desktop driving a remote session.

### What the document must contain

| | Android | web / desktop |
|---|---|---|
| `xmlns` | optional | **required** |
| at least one of `viewBox` or `width`+`height` | **required** | required |
| `fill` | optional (defaults black) | optional |

Neither client needs both geometry attributes. Android takes the aspect ratio
from whichever is present and the size from the column; the desktop takes the
displayed size from `width`/`height` and falls back to `viewBox` without them.

### How it must be encoded

Six spellings of one identical document:

| | desktop | Android |
|---|---|---|
| `data:image/svg+xml;base64,` padded, lowercase | renders | renders |
| `data:image/svg+xml;charset=utf-8;base64,` | renders | renders |
| `data:IMAGE/SVG+XML;base64,` -- type uppercased | renders | renders |
| `;base64,` with the padding stripped | renders | **fails** |
| `;BASE64,` -- token uppercased | renders | **fails** |
| `data:text/xml;base64,` | **fails** | renders |
| percent-escaped, minimal or total | renders | fails |
| unescaped, raw | renders | fails |
| entity-escaped (`&lt;`, `&#32;`) | **fails** | fails |
| no media type at all | fails | fails |
| inline HTML `<img src=... width=...>` | **fails** | **fails** |

Three of those rows are the interesting ones.

**The type is compared case-insensitively and the token is not.** `IMAGE/SVG+XML`
is accepted on Android while `;BASE64` is refused, in the same string. That is
the closest thing to seeing the implementation that we have: a normalised lookup
for the media type, and a literal comparison for the transfer encoding.

**`text/xml` renders on Android and fails on the desktop** -- the one place
being lax loses you the desktop rather than the phone.

**Inline HTML is not rendered anywhere.** Every mark must go through markdown
`![]()`, which is *why* the aspect ratio is the only size control that exists:
there is no element to put a `width` on.

`;charset=utf-8;base64,` also renders on both, so Android does parse media-type
parameters properly -- it is not matching a fixed prefix. It then requires the
`base64` token in lowercase and the payload correctly padded, neither of which
RFC 2397 demands. **Emit exactly `data:image/svg+xml;base64,` and standard,
padded, standard-alphabet base64.**

The shape of that table is the danger: every deviation passes on a desktop and
fails on a phone. A change made and checked on a desktop looks correct and
silently breaks the client it matters most for, so it wants an assertion in the
generator rather than a note in a comment.

### The destination must be a data URI

Markdown `![]()` is the only channel -- inline HTML renders nowhere -- and what
goes in the destination is itself a client difference:

| destination | desktop | Android |
|---|---|---|
| `data:image/svg+xml;base64,…` | renders | renders |
| `https://raw.githubusercontent.com/…/strip.svg` | **a link** | renders inline |
| a GitHub `blob` page, with or without `?raw=1` | a link | `?raw=1` renders |
| a repository-relative path, `strip.svg` or `docs/strip.svg` | a link | a link |
| an absolute container path or `file://` URL | a link | a link |

**A remote URL would be much cheaper than a literal** -- around 110 characters
against 315, editable as a file rather than re-encoded, and a size change
becomes two digits in a repository rather than a tool call at emission. It is
ruled out only because the desktop turns it into a link instead of an image.

Paths cannot work in principle: the transcript is not served from the
repository, and the container's filesystem is reachable from nothing but the
container, which is discarded when the session ends.

### Entity references are not decoded in link destinations

`&lt;svg…&gt;` fails on both clients, and this one is worth stating separately
because it is not about images. As far as I can recall the CommonMark
specification says entity and numeric references are recognised in link
destinations -- I could not check, the domain is blocked from this environment --
but the finding does not depend on that. The escaped and unescaped spellings of
one identical URL were compared directly: the raw one renders on the desktop,
the entity one does not.

The mechanism is that the payload arrives with `&lt;svg` as *character data
rather than markup*, so the document has no tags at all and no root element.
That is a harder failure than a bad URL, which is why it fails even on the
lenient desktop loader.

Anything relying on an entity inside a URL will silently fail on both clients.

### How it fails, which says where it failed

Android has two failure modes and they are at different layers.

- **Nothing at all** -- no image element was created. A CommonMark link
  destination cannot contain raw spaces, so the markdown parser never formed an
  image and the URI was never looked at.
- **A broken-image placeholder** -- the destination parsed, an image element
  exists, and the *loader* rejected the URI.
- **A clickable link** -- the destination parsed and was then routed away from
  the image loader entirely, because it is not a data URI. The most misleading
  of the three, since something visibly appeared.

Web and desktop show neither, because both layers there are lenient: raw spaces
are accepted in a destination, and non-base64 payloads are accepted by the
loader. Every client difference recorded here is one of those two layers.

### Sizing and presentation

| behaviour | Android | web / desktop |
|---|---|---|
| `width` / `height` as the displayed size | **ignored** | honoured |
| `width` / `height` in `pt` | ignored | not retested |
| `style="width:17px"` | ignored | not retested |
| `viewBox` aspect ratio | **honoured** | honoured |
| a square SVG | wrapped in a bordered card | wrapped in a bordered card |
| a letterboxed SVG | no card | no card |
| first sight of a unique image | needs a tap | renders |
| any later sight of the same bytes | renders, no tap | renders |

The sizing column is not a list of quirks to work around one at a time. It is
one behaviour: **on Android the mark is scaled to fill the column, and the only
property that survives is the aspect ratio.** Five ways of declaring a size were
tried -- the attributes, points, inline CSS, and omitting one or the other -- and
every one was overridden. Omitting *both* is different in kind: with no aspect
ratio to derive a height from there is nothing to draw, and the image does not
render at all rather than rendering at the wrong size.

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
- **Base64, padded, lowercase token.** Measured, not assumed; see the encoding
  table above.
- **Keep `xmlns`.** The desktop refuses the document without it.
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

The vector carries the repository's own cell size, the one the raster uses --
it is the same mark, and the 1-unit border against that cell is what gives it
its proportions.

Three encodings of the same 5x5 grid, measured over 500 identicons from real
keys, as characters of `d`, at each end of the cell range:

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

## The cost model

Two costs, and they are paid at different rates. **`CLAUDE.md` is read once per
session. The literal is emitted on every turn.** Everything else follows from
that asymmetry.

**Adjusting the size at output is not free.** Base64 cannot be edited in place,
and a model cannot base64 in its head, so every size change costs a tool call at
emission -- paid every turn it happens. Keeping raw SVG in the file to make the
digits editable does not avoid this, because Android needs the encoded form
regardless.

**So carry a menu, not a source.** Three or four pre-encoded literals at
different ratios cost a few hundred bytes once per session, and make selection
free: copy the line, no encoding, no tool call. Choosing wrongly with a single
literal costs every turn, forever. A small menu is strictly cheaper than one
editable source.

**Changing size has a second cost.** Images are cached by content and the first
sight of a unique byte sequence requires a tap on Android. Every new size is a
new byte sequence, so frequent adjustment spends the very glanceability the mark
exists for. A stable choice is tapped once.

**And the two clients read different attributes.** The desktop takes its size
from `width`/`height`; Android takes it from the viewBox ratio against the
column. One literal serves both, but the two numbers must be chosen together and
nothing checks that they agree -- an easy edit to get half right.

## What is measured and what is not

Everything in the tables above was observed on both clients, one property at a
time, except where a cell says otherwise. Two habits produced most of the wrong
turns on the way here and are worth inheriting:

**A blanket answer hides a client difference.** "Assume it renders on the
desktop unless I say otherwise" cost a false conclusion that `xmlns` was
optional -- the one variant where the desktop was the whole question was the one
the blanket covered. Ask per variant, per client.

**Vary one property.** The first percent-encoding trial changed the encoding
*and* mismatched `width` against `viewBox`, and was recorded as a measurement
for a day. A later single-variable run reached the same conclusion, which was
luck rather than vindication.

### The mechanism route was tried and is closed

An Android debug session would have turned these rules into a mechanism. It was
attempted on a Pixel 10 Pro over wireless debugging, package
`com.anthropic.claude`:

- `adb shell cat /proc/net/unix | grep webview_devtools` returns nothing, so
  there is **no debuggable WebView**. The transcript is rendered natively and
  `chrome://inspect` has nothing to attach to. The sizing behaviour is a native
  view's content scaling, not CSS -- there is no stylesheet to override.
- `adb logcat` filtered to the app's pid, across a render of four fresh failing
  variants, produced **zero lines**. Release logging is stripped.

So the black-box rules above are the answer, not a stopgap. The
`Base64.decode`-behind-a-`startsWith` hypothesis remains the best explanation of
the encoding column and remains unverified.

## What this costs

A typical contour is about 211 bytes of SVG and a 315-character literal,
against 234 for the 62px PNG. An 81-character premium on every turn,
for a mark that is the right size on a phone, in a browser and in the desktop
remote, with no detection and no choice to make.
