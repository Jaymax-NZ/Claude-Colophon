# Identicon

## Sign every response with this repository's identicon

Emit the turn mark below, verbatim, as the last line of every response in
this repository. Nothing after it.

**Also emit it immediately before asking the user anything** -- as the last
line of the text preceding a question, including before a tool call that
puts a question to them. A turn that ends in a question may never reach a
turn-end at all, so it is both the turn most likely to lose the mark and the
one where the reader most needs it: they are being asked to stop and decide,
and which project is asking is part of the question.

Which size to emit is a reader's choice, stated once in `~/.claude/CLAUDE.md`
and applying to every repository with an identicon. Absent a stated choice,
use block 3.

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

## Turn mark

One per block size. Emit the one matching your size preference.

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
