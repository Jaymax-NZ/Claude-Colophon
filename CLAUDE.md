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
| `.identicon/repository-identicon.txt` | a terminal; the pattern in octants and the colour in emoji, which is how colour survives a channel that strips ANSI |

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
