# Claude-Colophon

## Sign every response with this repository's identicon

Emit this line, verbatim, as the last line of every response in this
repository. Nothing after it.

**Also emit it immediately before asking the user anything** -- as the last
line of the text preceding a question, including before a tool call that puts
a question to them. A turn that ends in a question may never reach a turn-end
at all, so it is both the turn most likely to lose the mark and the one where
the reader most needs it: they are being asked to stop and decide, and which
project is asking is part of the question.

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABsAAAAbCAYAAACN1PRVAAAARUlEQVR4nGOgOzgjf+o/MZgqekctG3qWUWIIyQZjA6OWDW7LKDGYZAeMWjb0LMMGaGYwNjBq2fCwjBJ1eMGoZUPPMloAAKAYfRElkHoZAAAAAElFTkSuQmCC)

It is a PNG of this repository's identicon: a 5x5 grid inside a one-pixel
border, derived from the repository's identity rather than from its path, so it
is the same in every checkout on every machine.

The pixel size is deliberately not written down here. A re-run refreshes the
image above but leaves this prose alone -- as it must, so that a repository
which has rewritten the explanation keeps its wording -- and a number nothing
refreshes is a number that goes stale.
`.identicon/repository-identicon.png` is the record.

`.identicon/settings.json` is the record. It carries the seed, the colour, the
5x5 matrix, the tricolour as shape-and-colour pairs, and under `renders` the
ready-made strings: `renders.tricolour`, and `renders.blockDrawing` with
`sextant`, `octant` and `ascii`. Read a field; do not reassemble one from the
parts beside it.

`.identicon/` also holds the rasters and the vector —
`repository-identicon.png` for a README or anywhere that refuses SVG,
`repository-identicon.svg` where a forge renders it, and `-128`, `-256` and
`@4x` for a favicon, an avatar or a display that scales.

**Which variant to use is a reader's choice, not this repository's.**
`.claude/rules/identicon-constants.md` is generated per checkout, is gitignored,
and holds every turn-mark size alongside each text rendering. Size and
glyph-family preferences belong in `~/.claude/CLAUDE.md`, where they apply to
every repository carrying an identicon rather than to this one.

That file is rewritten in full on every run and must not be edited.
`CLAUDE.local.md` is yours and this plugin never writes to it.

The pattern in a text rendering is monochrome because a sextant is one glyph per
several cells and cannot be coloured per cell, so the colour rides in the emoji
tricolour — which is also how it survives a channel that strips ANSI.

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
