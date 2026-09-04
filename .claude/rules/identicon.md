# Identicon

## Sign every response with this repository's identicon

Emit the mark, verbatim, as the last line of every response in this
repository. Nothing after it. Which of the two renderings to use is
decided by the test under *Which rendering to emit*, below.

**Also emit it immediately before asking the user anything** -- as the last
line of the text preceding a question, including before a tool call that
puts a question to them. A turn that ends in a question may never reach a
turn-end at all, so it is both the turn most likely to lose the mark and the
one where the reader most needs it: they are being asked to stop and decide,
and which project is asking is part of the question.

## Which rendering to emit

There are two, and choosing between them is a **test, not a judgement**.
Check whether this session has any `mcp__ccd*` tools:

- **Present** -- a desktop-hosted pane, which renders markdown images.
  Emit one of the literals from `## Turn mark`, and nothing else.
- **Absent** -- a console session or a headless `claude -p` run, where a
  `data:` URI arrives as a wall of base64 and nothing else. Emit the
  `## Sextant` block, then a space, then the `## Tricolour` value.

Those tools are injected by the desktop app, so asking whether they exist
*is* the question asked directly. `CLAUDE_CODE_ENTRYPOINT` (`cli` versus
`claude-desktop`) and `TERM` corroborate it at the cost of a command; the
tool check costs nothing.

**This is not a preference and does not belong in a preference file.** An
earlier version said only "where a terminal needs the pattern", left the
test unstated, and the image won by default -- emitted into console
sessions as unreadable base64 more than once.

Which *size*, and sextant versus octant, are reader's choices, stated once
in `~/.claude/CLAUDE.md` and applying to every repository with an
identicon. Absent a stated choice, use block 3 and sextant.

A text rendering is monochrome. A sextant or octant is one glyph covering
several cells and cannot be coloured per cell, so the colour rides in the
tricolour beside it -- which is also how it survives a channel that strips
ANSI.

**Never base64 another file to make the mark.** The literals below are the
only ones. `-128` and `-256` in `.identicon/` exist for favicons and
avatars; embedded in a reply they render as a large
bordered card rather than an inline mark, because the client sizes the image
from its own pixel dimensions and raw `<img width>` is printed as literal
text. Observed 2026-09-02 in a cloud session, which had no copy of this rule
and reached for a raster instead.

**Never assemble the tricolour yourself.** Use `renders.tricolour` from
`.identicon/settings.json`, or the `## Tricolour` value below, verbatim.
The shape-and-colour pairs beside it in settings are the generator's
workings, not an instruction to rebuild the string -- the same cloud session
produced a different arrangement of the right colours by doing that.

**Why this is an instruction rather than a hook**, given that an instruction
depends on compliance and a hook does not: no hook output field can display
an image. A hook's `systemMessage` arrives as plain text, one event-name
prefix per line. The only channel in a GUI chat client that renders markdown
is an assistant message, and only the model writes those. So the
deterministic mechanism cannot render, and the mechanism that renders cannot
be made deterministic. This is the second of the two, chosen knowingly.

## About this file

Generated from `.identicon/settings.json` and rewritten in full on every
run of `/repo-identicon`. **Do not edit it** -- put anything of your own in
`CLAUDE.local.md`, which this plugin never touches.

Committed, because nothing in it is anyone's preference: it holds every
rendering variant, and every checkout derives the same ones from the same
settings. Choosing between them is a reader's business, and that choice
belongs in `~/.claude/CLAUDE.md`, where it applies to every repository with
an identicon rather than to this one.

It carries no `paths:` frontmatter, deliberately. An unscoped rule is
re-injected from disk after compaction, like the project-root `CLAUDE.md`; a
scoped one is reloaded only when a file it matches is read, and a mark
emitted on every turn must not depend on that.

## Turn mark

One per block size. Emit the one matching your size preference.

Each is a PNG of the identicon: a 5x5 grid inside a one-pixel border,
derived from the repository's identity rather than from its path, so it is
the same in every checkout on every machine.

- block 1: ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAcAAAAHCAYAAADEUlfTAAAAHklEQVR4nGMgCM7In/oPwuhsDAV4JUjTCZNEpgkCAGj0LfXTkuivAAAAAElFTkSuQmCC)
- block 2: ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAALklEQVR4nGMgC5yRP/UfGRMSJ10DLgU4FZKsAZdCov1AsU0YCinWgItPuQZiAACL8bfRn65LrwAAAABJRU5ErkJggg==)
- block 3: ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABEAAAARCAYAAAA7bUf6AAAANUlEQVR4nGOgGjgjf+o/NkySmsFjCDGKCWocPIYQo5GggYPHEGRAtsbBbwgx4ljB4DGEHAAAEyOdpFuFVmYAAAAASUVORK5CYII=)
- block 4: ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABYAAAAWCAYAAADEtGw7AAAAPUlEQVR4nGOgKTgjf+o/Pky2+lGD0dUTrZFog9DBCDaYVIOItmjUYJRwRgZUMwgdjBoMB4Q0jhpMtDxNAQBkGt9fkErzngAAAABJRU5ErkJggg==)
- block 5: ![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABsAAAAbCAYAAACN1PRVAAAARUlEQVR4nGOgOzgjf+o/MZgqekctG3qWUWIIyQZjA6OWDW7LKDGYZAeMWjb0LMMGaGYwNjBq2fCwjBJ1eMGoZUPPMloAAKAYfRElkHoZAAAAAElFTkSuQmCC)

## Tricolour

🟣🟥🟣

## Sextant

```
🬩🬵🬃
🬨🬬🬀
```

## Octant

```
▂𜺠𜺣
𜶛𜶫𜴀
```

## Ascii

```
[][]  [][]
  [][][]  
[][][][][]
  [][][]  
  []  []  
```
