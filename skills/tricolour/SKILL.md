---
name: tricolour
description: Put this repository's emoji tricolour at the front of the session title, for this session and every other open session on the same repository, so the session list is scannable by project at a glance. Use when the user runs /tricolour, asks to "mark this session", "colour the session title", "add the tricolour to my sessions", or asks why one session in the list has no colour. Does nothing at all in a repository with no identicon.
---

# Session tricolour

The turn-end mark says which project a *reply* came from. This puts the same
identity in the session list, where the question is which of eight rows to click.

The whole mark cannot go there — a session title is one line, and the 5×5
pattern needs two. So the title carries the emoji tricolour alone, which the
standard already specifies as the rendering for a medium that affords one line.

## Doing it

**1. Get the sessions.** `mcp__ccd_session_mgmt__list_sessions` returns every
session *but this one*, each with `sessionId`, `cwd` and `title`.

**2. Ask which of them share this repository's mark.** Pass their working
directories to the helper:

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/tricolour/tricolour.py" CWD ...
```

It prints `tricolour<TAB>value` and then one `match<TAB>path` line per candidate
that belongs. It exits 1, printing nothing to match, when the current
repository has no identicon.

**On exit 1, stop.** Say the repository has no identicon and offer
`/repo-identicon`. Do not rename anything, and do not fall back to a colour
picked some other way — a session marked with a mark the repository does not
have is worse than an unmarked one.

**3. Mark this session.** `set_session_title` with the literal `"self"`. It is
the one call that reaches the running session; `list_sessions` excludes it and
`get_session` refuses it.

Its result reports the previous title. If that title was clearly deliberate
rather than generated, set it again immediately as the tricolour plus the
previous title — one extra call, and it respects a name the user chose by hand.

**4. Mark the matches.** For each `match` line, find its session in the listing
by `cwd` and `set_session_title` with the tricolour prefixed to its existing
title.

## Strip before you prefix

Before adding the tricolour, remove any tricolour already at the front of the
title, then add the current one.

This is not tidiness. A repository's mark changes when its mapping version
moves, and every session titled under the old mapping keeps the old tricolour
forever otherwise — two different colours for one project in the same list, with
nothing to say which is current. Stripping and re-adding makes every run
self-healing, and makes the command safe to run twice.

**Recognise it by position and count, not by which glyphs it uses.** A tricolour
is exactly three emoji at the very start of the title, followed by a space or by
the end of the title. It is not always three squares: the palette carries other
shapes, and matching squares specifically would leave every non-square tricolour
behind. Matching the *current* value is worse still — it can only ever find the
marks that are already correct, which are the ones that need no work.

**Or by the end of the title**, because a session whose title is nothing but a
tricolour is a real state — it happens when a title was never generated. Requiring
a following space would fail to see it and prefix a second one.

**Strip repeatedly, not once.** If a title somehow carries two, removing one
leaves the other, and the result still looks wrong to the only person who would
notice. Keep removing while the title starts with a tricolour.

**Count grapheme clusters, not code points.** One emoji is not reliably one
character. The red heart is U+2764 followed by the variation selector U+FE0F —
two code points where every other heart is one — so a tricolour built from
hearts can be four code points rather than three. Counting characters would
read that as "not a tricolour" and leave a stale mark in place, which is the
one thing this step exists to prevent.

Three-and-a-space is also what keeps a title someone decorated with a single
emoji of their own from being eaten.

## Console sessions cannot be marked, and say so

`list_sessions` is a `mcp__ccd*` tool — the desktop app's own session manager —
so it enumerates only the sessions that app hosts. A session started as `claude`
in a terminal is invisible to it: not listed, not listed as archived, not listed
while running with a live pid.

The same session cannot mark itself either, because it has no `mcp__ccd*` tools
at all. That is the identical signal the rule uses to choose the text rendering
over the image, so a session that must emit sextants is exactly a session that
cannot carry a tricolour in its title.

**Say this when it applies rather than reporting a clean sweep.** Verified
2026-09-02: three sessions were open on one repository, two desktop and one
console; `list_sessions` returned only the desktop pair, and reporting "both
done" read as complete when a third was sitting there unmarked.

## What not to do

- **Never install an identicon as a side effect.** A repository with no
  `.identicon/` is left completely alone — not renamed, not offered a default,
  not enumerated further.
- **Never mark a session for a different repository.** The helper decides
  membership; do not widen it by path prefix. Two projects can sit in one parent
  directory, and separate worktrees of one project sit in different ones — which
  is exactly why membership is decided by the artifact's contents.
- **Never guess a tricolour.** It is read from `renders.tricolour` in
  `.identicon/settings.json`, already rendered. Do not rebuild it from the
  shape-and-colour pairs under `identicon.current.tricolour` beside it — that is
  deriving it, and the generator has already done so. Nothing in this plugin
  knows which glyphs it is drawn from.

## Why the helper exists at all

Membership is "does this path's repository carry the same tricolour", which needs
a `git rev-parse` and a file read per candidate. Doing that through individual
tool calls costs one round trip per session and gets slower the more sessions
are open. One call answers it for all of them.

It reads two things and compares strings. It knows nothing about how a mark is
derived, and must not learn.
