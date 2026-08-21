---
name: session-tricolour
description: Prefix a Claude session's name with its repository's tricolour -- the three coloured squares of the repository identicon -- so a list of sessions can be told apart without being read. Use when the user asks to "tag this session", "put the tricolour on the session name", "why is this session untagged", "take the squares off my session names", "turn session tagging on or off for this repo", or to reapply the mark after a re-seed, new vectors or a repository rename.
---

# Session tricolour

The identicon signs a turn; this signs a session. Same mark, same question --
which project is this -- asked in the other place it gets asked.

`docs/session-tricolour-spec.md` in this plugin is the specification. This file
is the procedure.

## The rule that outranks everything else here

**Never work out a tricolour. Read it.**

    "${CLAUDE_PLUGIN_ROOT}/skills/session-tricolour/session-tricolour.py" --triple

It comes from `.identicon/`, which the identicon generator wrote. Do not derive
it from `.identicon/repository-identicon.colour`, from the remote URL, from the
key, or from a palette you happen to know. A second thing that can produce the
mark is a second thing that can disagree with the first, permanently and
silently.

This matters most in the one place it is tempting: a session list hands you
every session's git URL, and the derivation is available. Use the URL to work
out *which sessions are this repository's*, never what colour they are.

## Tagging this session

Do this at the **end** of a turn, never at the start of a session. A session's
name is generated from its first prompt a few seconds in, and anything set
before that is overwritten without a word.

1. Get the triple, as above. Exit code 3 means this repository has no
   identicon, and 4 means it has opted out. Both are complete answers: stop,
   silently.
2. Ask the session-management tool for this session's own identity and current
   name. On Claude Code Remote that is `get_session` with no argument.
3. If the name already begins with the triple, stop. Nothing to do and nothing
   to say.
4. Otherwise compute the new name and set it:

   ```bash
   "${CLAUDE_PLUGIN_ROOT}/skills/session-tricolour/session-tricolour.py" --tag "<the current name>"
   ```

   Then rename the session to exactly that string.
5. **Read it back.** This is the step that matters, and the reason is below.

### If the read-back does not carry the triple

The surface will not let a session rename itself. Verified working on Claude
Code Remote -- web, mobile and remote CLI. Reported not working on Claude
Desktop, where a session could rename every session *except* itself; that
report is unverified and worth re-testing rather than assuming in either
direction, which is why the procedure is try-then-check rather than a table of
clients.

When it fails, another session can apply the tag -- but **it must be given the
three squares, not asked to work them out**, because it is not in this
repository and cannot read this repository's `.identicon/`. Hand over the
literal characters. Do not ask a peer to "tag the sessions for repo X".

Do not go looking for a peer unprompted. Say once that this client will not
rename its own session, and offer.

## Removing it

Removal means three things, and doing fewer is not removal:

1. strip the prefix from this session's name (`--untag "<name>"`);
2. strip it from every **live** session on this repository -- find them by
   matching each session's git URL with `--matches <url>`, and skip archived
   ones;
3. `--disable`, which takes the tagging section out of `CLAUDE.md` so nothing
   re-applies it.

The third is what makes the first two stick: leave the repository opted in and
the next turn's self-heal puts the mark straight back. That is also why there is
no such thing as removing it from one session only -- the decision belongs to
the repository, because the mark does.

`--disable` edits a tracked file. Say so, and say that the opt-out only travels
if it is committed.

## Turning it on

`--enable` writes the section. It refuses if there is no identicon: run
`/repo-identicon` first, since there is no mark to tag with.

`--enable` and `--disable` are the only things that write or remove this
section, which is what makes both the opt-in and the opt-out durable.

`CLAUDE.md` belongs to this plugin, not to the generator. The generator still
writes a signing block there today — that is a misplacement owed an extraction,
not a licence to add more. It swaps only its own literal, so it leaves this
section alone in the meantime. Never put an instruction for Claude into the
generator.

## Reapplying

For when the mark itself changed -- new vectors, a new seed, a renamed
repository. Never scheduled, always asked for.

**One repository at a time, run from a checkout of it.** A session cannot get
another repository's tricolour without deriving it (forbidden) or copying a
sibling session's (which is the stale value the reapply exists to replace). To
cover several projects, run it in each.

Climb only as far as you are told, and confirm each rung:

| rung | what to do |
|---|---|
| this session | just do it |
| live sessions on this repository | **list them by name first, then ask** |
| archived sessions | only if named explicitly, and then still ask |

Archived sessions are in scope and are never in the default. Show what will
change, change what was agreed, report what changed -- by name, not by count.

## Degrade silently

No renaming tool, no session identity, no `.identicon/`, or a rename that is
refused: do nothing and say nothing. This is a convenience about legibility and
must not become the loudest thing in the transcript. A rename that reverts gets
reported once and not retried.

## The interim reading

The triple currently comes from the last three characters of the last line of
`.identicon/repository-identicon.txt`, because it does not yet have a file of
its own. `--triple` already prefers `.identicon/repository-identicon.tricolour`
and will use it the moment the generator starts writing it. Keep reading through
the script rather than opening either file yourself, and that change costs
nothing here.
