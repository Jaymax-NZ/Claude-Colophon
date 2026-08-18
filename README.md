# Claude Colophon

A Claude Code plugin. Give every repository an identicon derived from its git
remote, and have Claude sign each turn with it — so four sessions open on four
projects are distinguishable without reading a word.

A *colophon* is the printer's mark at the end of a book, identifying who made
it. That is precisely what this is: a mark, at the end, saying where you are.

## Install

```
/plugin marketplace add Justin-Maxwell/Claude-Colophon
/plugin install claude-colophon
```

Then, in any repository:

```
/repo-identicon
```

## What it puts in a repository

A `.identicon/` directory holding one mark in four forms, and a section in
`CLAUDE.md` carrying it as an inline image with the instruction to emit it last
on every turn.

| file | consumer |
|---|---|
| `.identicon/png.b64` | the `CLAUDE.md` literal; a `data:` URI cannot reference a path |
| `.identicon/icon.png` | a README, or anywhere SVG is refused |
| `.identicon/icon.svg` | a README on a forge that renders it; anything scalable |
| `.identicon/colour` | `#rrggbb`, for a prompt, a badge, or a theme |

Each is usable by a consumer that knows nothing about this plugin and does no
parsing at all: `cat .identicon/colour` yields a colour,
`![](.identicon/icon.svg)` yields an image. That is why they are four files and
not one — a README cannot address a fragment inside a blob.

**No code is installed into your repository** and it gains no dependency on this
plugin. An identicon is a constant for a repository; it is derived once.

## What it will ask to run

Two local commands, both documented with their reasons in
[PERMISSIONS.md](PERMISSIONS.md): the installer, once per repository, and a read
of one environment variable, at most once per session and usually not at all.
No network access, no writes outside the repository you point it at, and no
hooks.

## Why an instruction rather than a hook

An instruction depends on the model complying; a hook does not. The hook route
was built first and abandoned, because no hook output field can display an
image — a `systemMessage` arrives as plain text with the event name prefixed to
every line. The only channel in a GUI chat client that renders markdown is an
assistant message, and only the model writes those.

So the deterministic mechanism cannot render, and the mechanism that renders
cannot be made deterministic. This is the second of the two, chosen knowingly.

## The derivation

Specified by [Repository Identicon](../Repository-Identicon) — the key is the
git remote, normalised so every spelling of one repository collapses to one key,
which is what makes the mark survive being cloned. The pattern and colour
conform to `stewartlord/identicon.js`.

`skills/repo-identicon/repo-identicon.py` carries its own copy of that
derivation and depends on nothing. It has to: a Claude Code plugin is copied
whole and has no dependency mechanism. The conformance apparatus — the vendored
library and its pinned vectors — stays with the standard, and a test there holds
this implementation to it.

## Licence

Not yet chosen.
