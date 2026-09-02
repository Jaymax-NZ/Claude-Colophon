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

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABsAAAAbCAYAAACN1PRVAAAASUlEQVR4nGMYtOByAMN/dExYF5lg1DKqAJpZRqzBVHHAqGXDwzJiMWHT0cCoZYPbMkoMJtkBo5YNPcuwAZoZjA2MWjb0LKMFAADvj+qbXLsw2gAAAABJRU5ErkJggg==)

It is a PNG of this repository's identicon: a 5x5 grid inside a one-pixel
border, derived from the repository's identity rather than from its path, so it
is the same in every checkout on every machine.

The pixel size is deliberately not written down here. A re-run refreshes the
image above but leaves this prose alone -- as it must, so that a repository
which has rewritten the explanation keeps its wording -- and a number nothing
refreshes is a number that goes stale.
`.identicon/repository-identicon.png` is the record.

`.identicon/` holds the same mark in every form a consumer might want, each
usable with no parsing at all:

| file | for |
|---|---|
| `.identicon/repository-identicon.png` | a README, or anywhere that refuses SVG |
| `.identicon/repository-identicon.svg` | a README on a forge that renders it; anything scalable |
| `.identicon/repository-identicon.colour` | `#rrggbb`, for a prompt, a badge, or a theme |
| `.identicon/repository-identicon.tricolour` | the emoji tricolour; the whole mark for a session title, a tab title, or any single line |
| `.identicon/repository-identicon.sextant` | the pattern in sextants, two lines, for a terminal |
| `.identicon/repository-identicon.octant` | the pattern in octants, two lines, where the font carries them |
| `.identicon/repository-identicon.grid` | five rows of `0` and `1`, for anything drawing its own cells |
| `.identicon/repository-identicon.key` | the seed and mapping version this mark was derived from |

`repository-identicon-128.png` and `-256.png` are the same raster at larger
sizes, for a favicon or an avatar. `@4x.png` was removed on 2026-09-03;
`docs/repository-scope.md` gives the reason.

The two-line text form is composed rather than stored: the contents of
`.sextant`, a space, then the contents of `.tricolour`. The pattern is
monochrome because a sextant is one glyph per several cells and cannot be
coloured per cell, so the colour rides in the emoji tricolour — which is also how
it survives a channel that strips ANSI.

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

## Carry the identicon in the session title

On an early turn, run `/tricolour`. It puts this repository's emoji tricolour
at the front of this session's title, and of every other open session on this
repository, so that the session list is scannable by project rather than by
reading each row.

The tricolour is the whole mark for a single line: a session title cannot hold
the 5x5 pattern, which needs two.

Opt out by deleting this section. Nothing regenerates it -- `--session-title`
adds it and `--no-session-title` removes it, and neither is the default.
