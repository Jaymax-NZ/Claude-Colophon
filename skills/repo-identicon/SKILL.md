---
name: repo-identicon
description: Give a repository a visual identity that Claude emits at the end of every turn — a small deterministic identicon derived from the repository's git remote, so parallel sessions in different projects are distinguishable at a glance. Use when the user asks to "add the identicon to this repo", "give this project an identicon", "set up the turn identicon", "make this repo identifiable", or asks why the identicon is wrong, stale, or missing after a rename, a move between forges, or a fresh clone. Runs once per repository; re-run only if the remote changes.
---

# Repository identicon

Install a per-repository identicon that gets emitted as the last line of every
response, so that several Claude windows open on different projects can be told
apart without reading them.

## What lands in the repository

A `.identicon/` directory holding one mark in several forms, and a section in
`CLAUDE.md` carrying it as an inline markdown image with the instruction to
emit that line last on every turn.

| file | consumer | why not one of the others |
|---|---|---|
| `.identicon/repository-identicon.png` | a README; anywhere SVG is refused | PyPI and some aggregators strip SVG |
| `.identicon/repository-identicon.svg` | a README on a forge that renders it | scales; a size is declared so `![]()` renders it as an inline mark rather than at column width |
| `.identicon/repository-identicon.colour` | a prompt, a badge, a theme | `#rrggbb` and a newline, so `$(cat …)` is the whole parser |

Every one is usable by a consumer that knows nothing about this tool and does
no parsing. That is the design, and it is why these are separate files rather
than one: a combined file would be readable by every tool that knows the
format, which is one tool. A README cannot address a fragment inside a blob,
and `![](.identicon/repository-identicon.svg)` is the entire integration.

**Each filename repeats the directory deliberately.** The directory is context,
and context is what does not travel — copied out, fetched from a raw URL or
dropped into `docs/`, a file called `icon.png` describes nothing. The
`repository-` prefix anticipates a project carrying more than one mark, a
user's alongside the repository's, at which point the unqualified name is the
ambiguous one.

The `CLAUDE.md` literal is base64 of the PNG. There is no file holding it: that
would be a second copy of one image, free to disagree with the first.

**No code is installed in the target repository** and it gains no dependency on
this skill. The identicon is a constant for a repository, derived once.

Earlier layouts used other names — a single `repository-identicon-png.b64` at
the root, then `icon.png` and friends inside the directory. The installer
removes any it finds, because a repository carrying both leaves every consumer
guessing which is current.

## Offer the README line

The artifacts are inert until something points at them. After installing, offer
to add the mark to the repository's README:

```markdown
![](.identicon/repository-identicon.svg)
```

Use the SVG where the forge renders it, the PNG where it does not. To scale it,
the consumer supplies the size — `<img src=".identicon/repository-identicon.svg" width="120">` —
which is the right way round, since the default use is an inline mark beside a
title.

## Doing it

Run the script. It resolves the key, derives the identicon, writes the
artifacts, and reports what changed:

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/repo-identicon/repo-identicon.py"
```

It takes an optional path argument and defaults to the working directory;
either way it writes at the repository root, so running it from a subdirectory
is fine. It is idempotent — a second run on an unchanged repository writes
nothing and says so.

## The one choice worth offering

**How heavy the mark sits beside a line of text**, set by the pixel size of one
grid square: `--cell 1` through `--cell 5`, defaulting to 3. Each gives a canvas
that divides exactly — 7, 12, 17, 22 or 27 pixels square.

Don't interrogate the user about it on a first install; the default is chosen
and fine. Offer it once the mark is in place and they can see it, since this is
a judgement about how something looks and nobody has an opinion until they are
looking at it. Show them rather than describing it — emit two candidate sizes
as inline markdown images in your reply and let them pick:

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/repo-identicon/repo-identicon.py" --cell 2 --b64
```

A repository's choice is read back out of its own installed PNG, so re-running
never silently resizes a mark someone settled on. Pass `--cell` only to change
it. Changing it rewrites the `CLAUDE.md` literal and three of the four
artifacts; the colour is unaffected.

Useful flags: `--dry-run` (report the key and cell, write nothing), `--key`,
`--b64`, `--svg`, `--colour`, `--png` (raw bytes to stdout). All of them honour
`--cell`, and without it they preview the repository's own current size rather
than the default. An unrecognised flag or an out-of-range `--cell` is refused
rather than falling through to a real install, so a typo cannot write files.

`${CLAUDE_PLUGIN_ROOT}` is set for a plugin's own files and is the only correct
way to reach them — the plugin's location on disk is not fixed and is not
guessable. Quote it, since an install path may contain spaces.

Issue it as a single Bash call with nothing chained to it, so the invocation
reduces to a reusable prefix rule. The rule has to name the **resolved** path
rather than the variable, because permission matching happens after expansion —
so it differs per machine and cannot be quoted from here. `claude plugin details
claude-colophon` reports the location.

This is a once-per-repository action, so approving the prompt each time is a
perfectly reasonable choice and should be offered as one. Do not press for an
allowlist entry. `PERMISSIONS.md` in the plugin explains what is asked for and
why; point at it rather than restating it.

## What the script will and will not do

Worth knowing before approving it, and worth saying to a user who asks:

- It writes into `.identicon/` and `CLAUDE.md`, both at the repository root, and
  refuses any path that resolves outside it.
- Both writes go through a temp file and a rename, so an interrupted or crashed
  run leaves the previous `CLAUDE.md` intact rather than truncated.
- Nothing is written until everything has been read and decided, so a refusal
  leaves the repository exactly as it was found.
- The only subprocesses are read-only git queries — `rev-parse --show-toplevel`,
  `remote get-url`. It never mutates git state, never touches the index or a
  branch, and never commits.
- No network access, and nothing outside the target repository is read or
  written.
- It is idempotent: a second run on an unchanged repository writes nothing.

Then tell the user what to commit — both files, together. Committing one
without the other leaves the repository inconsistent with itself, and the
identicon is only portable across clones if it is committed.

## Read the reported source before declaring success

The script prints which source the key came from. Only two of them survive a
clone:

| source | key | portable |
|---|---|---|
| `override` | a committed `.repository-identicon` at the root | yes |
| `remote` | `host/owner/repo` from the git remote | **yes** |
| `toplevel` | the repository root path | no |
| `path` | the directory itself, outside a repository | no |

On `toplevel` or `path` the script warns, and that warning is worth relaying
rather than passing over: a path-keyed identicon changes identity when the
repository is cloned to another machine **or opened in a git worktree**, and
the desktop app gives every parallel session its own worktree — which would
give each parallel session in one project a different mark, precisely
inverting what the identicon is for. Offer to add a remote, or to commit a
one-line `.repository-identicon` naming a stable key.

## When it is already installed

If `CLAUDE.md` already carries an identicon literal, the script swaps that one
literal in place and leaves the surrounding prose alone, so a repository that
has rewritten the explanation keeps its wording. If it finds more than one
literal it refuses and says so, because two literals can disagree and nothing
would catch it.

## If the user asks why this is an instruction and not a hook

Because no hook output field can display an image. A hook's `systemMessage` is
delivered as plain text with the event name prefixed to each line. The only
channel in a GUI chat client that renders markdown is an assistant message, and
only the model writes those. So the deterministic mechanism cannot render, and
the mechanism that renders cannot be made deterministic. The instruction is the
second of the two, chosen knowingly — do not "improve" it into a `Stop` hook,
which was tried and produces `Stop says: ![](data:...)` under every turn.

## Where the derivation is specified

`~/Code/Projects/Claude-State-Panel` — `docs/project-identicon-spec.md` for the
key and the rendering, with the pattern and colour conforming to
stewartlord/identicon.js, vendored there alongside pinned test vectors. That
apparatus stays in that repository, where it is checked; this script carries
only the derivation. The two are proven to agree because that repository's own
identicon is produced by this script and its test suite compares the committed
literal against a fresh derivation from its full implementation.
