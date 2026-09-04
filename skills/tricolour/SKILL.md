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

**Without `mcp__ccd*` tools, print a line for the user to paste instead:**

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/tricolour/tricolour.py" --self
```

It reads this session's title off disk, strips any tricolour already at the
front, and prints `rename<TAB>/rename <tricolour> <name>`. Emit that command on
its own line, prefixed with `Enter this prompt:`, and nothing else — no code
fence. A fence is presentational in a terminal, where there is no click-to-copy,
and it risks the mouse selection picking up indentation.

When it prints `current<TAB>yes` the title is already correct. Say so and emit
no line: a command that changes nothing invites a pointless paste.

`/rename` takes the rest of the line raw, so the name needs no quoting and no
escaping even when it contains spaces or an apostrophe.

**This marks only the session that runs it**, which is the whole of what a
session without the tools can do. It cannot reach a peer, and a peer console
session cannot be reached by anything — it has to run `/tricolour` itself.

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

## `list_sessions` is not a complete list. Never report a sweep

**It is local-only.** Every id it returns is prefixed `local_`, and that prefix
is the whole answer: a **cloud session** working on the same repository is
invisible to it, has no transcript on this machine, no local process, and is not
returned by `get_session` or `search_session_transcripts` either. Confirmed
2026-09-02, after three wrong explanations — the sidebar showed three sessions
for this repository and the listing returned one.

**`ListAgents` fills part of the gap, with Remote Control connected.** On
2026-09-04 it returned 16 peers labelled by kind — 12 `Remote Control`, 2
`cloud`, 2 local `interactive` — so cloud sessions were visible there while
`list_sessions` could not see them. An earlier version of this note said a cloud
session "need not appear there" and concluded nothing could see across surfaces;
that conclusion was wrong.

It still does not let you act. `ListAgents` reports no `cwd`, and membership is
decided by reading each candidate's `.identicon/settings.json` — so its rows
cannot be matched to this repository, and a title that looks like a match is a
guess. Never mark on the strength of one.

So a cloud session cannot be marked from here at all. It also cannot run this
skill, which is not installed in that environment.

So report what was marked and how it was found. Do not say "all sessions for
this repository", because that cannot be known from here. If the user names a
session the listing missed, the fix is to run `/tricolour` inside it: a session
can always mark itself with `"self"`, whatever the listing does or does not
know about it.

A session with no `mcp__ccd*` tools cannot mark itself, since
`set_session_title` is one of those tools. That is the same signal the rule uses
to choose the text rendering over the image. It prints a line to paste instead —
see step 3.

**Four routes were tested on 2026-09-04 and three are closed.** `/rename` is a
built-in the client executes; it arrives already done and the model never gets
to call it. A prompt enqueued by `CronCreate` reaches the model as text, so a
leading `/` is just a character — skill-backed commands still work that way,
because the model can invoke the skill, but a built-in has no tool behind it.
Writing `custom-title.json` persists and changes nothing, because the client
holds the title in memory and writes that file on change rather than reading it
back; `sessions/<pid>.json` was rewritten by the client during the test, so a
write there would have been clobbered. Only a person typing `/rename` works.

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
