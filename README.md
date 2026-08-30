# Claude Colophon

![](.identicon/repository-identicon.svg)

A Claude Code plugin. Give every repository an identicon derived from its git
remote, and have Claude sign each turn with it — so four sessions open on four
projects are distinguishable without reading a word.

A *colophon* is the printer's mark at the end of a book, identifying who made
it. That is precisely what this is: a mark, at the end, saying where you are.

## Install

[Repository Identicon](https://github.com/Justin-Maxwell/Repository-Identicon)
is a prerequisite. It is the standard and its reference implementation, and it
derives the mark; this plugin does not carry a copy of that and will not fall
back to one. Put `repository-identicon` on your `PATH`.

```
/plugin marketplace add Justin-Maxwell/Claude-Colophon
/plugin install claude-colophon
```

Then, in any repository:

```
/repo-identicon
```

## What it puts in a repository

Two things, written by two tools.

The generator writes a `.identicon/` directory holding the mark in every form a
consumer might want — a raster, a vector, the colour as `#rrggbb`, and the text
renderings for a terminal. Each is usable by a consumer that knows nothing about
either tool and does no parsing at all: `cat` the colour file and you have a
colour, `![](.identicon/repository-identicon.svg)` and you have an image. What
is in the directory is the generator's business, and its documentation is the
list.

This plugin writes one thing: a section in `CLAUDE.md` carrying the mark as an
inline `data:` image, with the instruction to emit it last on every turn. That
is the one form the directory cannot supply, because a `data:` URI carries bytes
and cannot reference a path.

**No code is installed into your repository** and it gains no dependency on this
plugin. An identicon is a constant for a repository; it is derived once.

## What it will ask to run

The installer, once per repository, documented with its reasons in
[PERMISSIONS.md](PERMISSIONS.md). It runs the generator and a read-only `git
rev-parse`, and writes `CLAUDE.md` itself. No network access, no writes outside
the repository you point it at, and no hooks.

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

None of it is implemented here. `skills/repo-identicon/repo-identicon.py` runs
the generator and then embeds the PNG it wrote.

It used to carry its own copy, on the argument that a Claude Code plugin is
copied whole and has no dependency mechanism. That argument is real, and it was
outweighed: two implementations of one constant are free to drift, and a mark
that differs between the plugin and the standard is worse than a mark that needs
a second tool installed, because nothing tells you it has happened. Packaging —
how a plugin-only user obtains the generator — is unresolved and deliberately
so; a missing generator is a clear error rather than a quiet second derivation.

## Tests

```
python3 -m unittest discover -s tests -t tests
```

Standard library and git, nothing else. No network, and no dependency on either
sibling repository being checked out.

[tests/test_repo_identicon.py](tests/test_repo_identicon.py) covers the
`CLAUDE.md` write and nothing else: that a block is added where there is none,
that a re-run swaps only the literal and leaves edited prose intact, that two
literals are refused rather than one being picked, that an undecodable file is
an error rather than an absent one, and that a generator flag is only accepted
after the `--` separator.

There are no pinned colours, rasters or vectors. Those would be testing the
standard through a copy, which is the arrangement that was removed.

One end-to-end test runs the generator for real and checks the literal against
the PNG it wrote. It skips when the generator is not installed — and it is a
single test rather than a suite-wide condition, so an absent generator is
visible as one skip instead of a green run that checked nothing.

## Licence

AGPL-3.0-or-later, matching the sibling projects. [LICENSE](LICENSE) carries the
text.

Nothing third-party is vendored here. The derivation conforms to
stewartlord/identicon.js rather than copying it, and the reference library and
its pinned vectors stay with the standard — so this covers the repository's own
code and carries no onward attribution obligation.
