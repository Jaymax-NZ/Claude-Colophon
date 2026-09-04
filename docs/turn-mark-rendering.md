# Rendering the turn mark

Findings from 2026-09-02, established by emitting candidates into a live chat
pane and a live mobile client and reading the result. Every "verified" below
means someone looked at it on the surface named.

Four beliefs this repository was built on are false. They are listed first
because code and prose still depend on them.

## Falsified

**"A `data:` URI carries its bytes and cannot reference a path."** Stated in
`CLAUDE.md`, `README.md`, the generated rule and the installer docstring, and
used to justify the entire base64 apparatus. A relative path renders:
`![](.identicon/repository-identicon.svg)` displayed in a desktop pane.

**"Pixels are the only control there is."** Recorded 2026-08-17 after rendering
one identicon at 15x15 and 84x84, and true of PNG. An SVG's `viewBox` ratio
controls apparent size, and a client honours `width`/`height` where they fit.

**"Base64 is necessary."** True of PNG, which is binary. SVG is text and travels
percent-encoded, which is shorter and legible.

**A bordered card is not a size law.** `test_turn_identicon.py` in
Claude-State-Panel records a preview that "rendered oversized regardless of its
pixels" through a file-card channel. Card rendering is channel-dependent as well
as size-dependent, and a carded mark is degraded rather than disqualified.

## What renders

| form | desktop | mobile |
|---|---|---|
| PNG, base64 `data:` URI | yes | yes |
| SVG, base64 `data:` URI | yes | yes |
| SVG, percent-encoded `data:` URI | yes | yes |
| SVG, relative path | yes | not tested |
| PNG, relative path | not tested | not tested |
| raw inline `<svg>` markup | not tested | not tested |

Percent-encoded and base64 forms of the same SVG rendered identically, so base64
has no remaining justification for this format.

## Size

An SVG with no `viewBox` is fixed at its `width`/`height`. One with a `viewBox`
wider than its content is letterboxed: the client fits it to the column, and the
ratio decides the resulting height. Widening the box makes the mark smaller.

Verified on mobile in a 400 px column:

| ratio | `viewBox` height 17 | apparent |
|---|---|---|
| 8:1 | `0 0 136 17` | ~50 px |
| 12:1 | `0 0 204 17` | ~33 px |
| 20:1 | `0 0 340 17` | ~20 px |
| 30:1 | `0 0 510 17` | ~13 px |

The same ratio does not give the same size on both surfaces, because it is a
fraction of the reading column. 12:1 and 20:1 were both too large on desktop.

`preserveAspectRatio="xMinYMid meet"` pins the mark to the left of the
letterbox. Without it the mark centres itself in the empty space as the ratio
widens.

**The letterbox scales the border with the geometry.** That is the one thing the
`@4x` raster gets wrong -- it doubles the border while quadrupling the block --
and the 62 px raster too, where the border stayed one device pixel.

## The form verified on mobile

```
<svg xmlns="http://www.w3.org/2000/svg" width="324" height="27"
     viewBox="0 0 324 27" preserveAspectRatio="xMinYMid meet">
  <path fill="#cc1fca" d="M1 1h5v5H1z…"/>
</svg>
```

371 bytes raw, 431 percent-encoded. `width` is honoured where it fits, so a
desktop pane wider than 324 px renders the mark at 27 px; a phone ignores it,
fits the column, and the 12:1 ratio gives about 33 px.

## Encoding cost

Same geometry, three ways of writing it:

| form | raw | percent-encoded |
|---|---|---|
| 17 `<rect>`, `fill` on each -- as the generator writes it | 1063 | 1321 |
| `fill` hoisted to `<svg>`, rects bare | 806 | 962 |
| single `<path>` | 342 | 398 |

The committed SVG writes `fill="#cc1fca"` seventeen times, which is 255 bytes of
one colour. A minimiser reduced the path form further to 313 bytes by using the
absolute `H` command where a cell's x is a single digit, which is one character
shorter than the relative `h-5` there.

For comparison: five PNG block sizes as base64 literals cost 732 characters and
serve one surface each. One percent-encoded SVG costs about 400 and serves any
size from two digits.

**Rewriting rects into a path is the generator's change, not this repository's.**
It writes the SVG; re-rendering the same geometry here would be re-deriving the
artifact.

## Surface detection is wrong in the shipped rule

The generated rule routes on whether the session has `mcp__ccd*` tools: present
means a desktop pane and an image, absent means a console and the text pair.

That is two branches for at least three surfaces. A **cloud session** has no
`mcp__ccd*` tools and renders images correctly, including on mobile. The rule as
written sends it to sextants.

What is actually verified:

| surface | `CLAUDE_CODE_ENTRYPOINT` | `mcp__ccd*` | renders images |
|---|---|---|---|
| desktop pane | `claude-desktop` | present | yes |
| console | `cli` | absent | no |
| cloud / mobile | not measured | absent | **yes** |

The missing measurement is the cloud session's entrypoint. Until it is taken,
the correct predicate is unknown, and `mcp__ccd*` is not it.

## Open

- Which ratio suits a desktop pane. 12:1 and 20:1 are too large; 30:1, 40:1,
  50:1 and 65:1 were emitted for comparison and not yet judged.
- Whether a `viewBox`-less SVG stays at its `width` on mobile. If it does, the
  fixed form is safe everywhere and the letterbox is an opt-in enlargement.
- Whether a relative path renders on mobile and in a cloud session. If it does,
  the carrier question closes: the file is referenced, not embedded, and nothing
  needs refreshing when the mark changes.
- Whether a path resolves against the session's working directory or the
  repository root. A session started in a subdirectory would break a
  cwd-relative reference.

## What this invalidates in this repository

- `image_literal()`, and the base64 encoding it performs.
- The `## Turn mark` five-literal menu in the generated rule.
- The sentence about `data:` URIs in `CLAUDE.md`, `README.md`, the rule and the
  installer docstring.
- "Never edit the mark", which was written when the carrier was opaque. A
  percent-encoded SVG can be proofread, so editing `viewBox` and `width` is
  checkable in a way editing base64 never was. Editing a `rect`, a `path` or a
  `fill` remains forbidden -- that is the mark itself.

None of it has been changed yet. The branch already carries several
restructurings and a competing implementation is unmerged.
