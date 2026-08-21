# Session tricolour

Prefix the name of every Claude session with the three coloured squares of the
repository it is working in, so that a list of sessions is readable without
reading it.

The identicon signs a *turn*; this signs a *session*. They answer the same
question — which project is this — in the two places it gets asked, and they are
the same mark in both.

## Whose score is whose

Three projects, and the boundary between them is the thing most often got wrong
— including by the first draft of this document.

| project | writes |
|---|---|
| **Repository Identicon** | the standard: the key, the derivation, the conformance vectors. Nothing in your repository. |
| **the generator** | `.identicon/`, and nothing else. |
| **Claude Colophon** | everything in `CLAUDE.md`, and the session name. |

`CLAUDE.md` is Claude Colophon's score. It is where a mark becomes an
instruction to Claude, which is the whole of what Claude Colophon is for and
none of what a generator is for. A generator that also wrote instructions would be one you
could not replace without re-deciding how Claude behaves.

That is not hypothetical. The vendored generator is going to be replaced when
the tricolour becomes a file of its own, and anything of ours entangled in it is
an entanglement to be undone every single time.

**Today `repo-identicon.py` does write the signing block into `CLAUDE.md`.** That
is the misplacement rather than the precedent: it is owed an extraction, and
until then nothing new goes near it.

## The one rule everything else follows from

**`.identicon/` is the only source of the tricolour. Nothing computes it.**

The squares are produced by the identicon generator, from the key, by a
derivation that is specified and conformance-tested elsewhere. A second thing
that can produce them is a second thing that can disagree, and the disagreement
would be silent and permanent — a repository would have two identities, each
correct according to whatever produced it.

So: read the file. Never the colour, never the key, never the remote URL, never
a re-implementation of the palette. If the file is not there, there is no
tricolour, and that is a complete answer rather than a problem to solve.

### Reading it

    tricolour(root) ->  ".identicon/repository-identicon.tricolour", if present
                        else the last three characters of the last line of
                        ".identicon/repository-identicon.txt"

The dedicated file does not exist yet; the generator will split the tricolour
and the octant grid into separate artifacts. Preferring it and falling back
means that split needs no change here at all — the day the file appears, it
wins. The `.txt` tail is the interim reading and is marked as such at the one
place it happens.

### Matching is not deriving

Deciding *which sessions belong to this repository* compares normalised remote
URLs, using the generator's own `normalise_remote_url`. That answers "is this
the same repository", not "what colour is it", and it never produces a square.
The distinction matters because the two look alike from a distance: one reads a
URL to compare it, the other reads a URL to invent a mark. Only the first is
permitted.

## Three states, one switch

| state | how it arises | what happens |
|---|---|---|
| **no identicon** | no `.identicon/` directory | nothing, ever. Not an error, not a prompt. |
| **opted in** | the tagging section is in `CLAUDE.md` | sessions tag themselves |
| **opted out** | that section removed, or never written | nothing, until someone opts in again |

The presence of the instruction *is* the switch. There is no settings file, no
flag read at runtime, nothing to keep in sync with anything: the mechanism that
causes tagging is the same object that enables it, so the two cannot disagree.

A repository that carries identicon artifacts but not the tagging section is the
supported way to have the mark without the session names — which is the case a
switch exists for.

An opt-out is durable because nothing rewrites the section: this feature's own
tooling is the only thing that writes or removes it. Today's generator, which
still carries a signing block of its own, swaps only that block's literal and
leaves other prose alone — so it does not disturb this section in the meantime,
and will not be in `CLAUDE.md` at all once the extraction above is done.

## Placement and format

    <square><square><square><space><whatever the title already was>

**Prefix, not suffix.** The turn signature goes last because the squares sit
flush against the end of a full line of octants. A session list truncates on the
right, so in a title the mark goes first. Same reasoning, opposite end.

Applying is idempotent and self-correcting: a title already carrying the correct
triple is left alone; one carrying a *different* triple has it replaced, which
is what makes a re-seed or a repository rename converge rather than accumulate.

## Who renames whom

A session renaming itself is the whole mechanism where it works. It needs no
peer, no second process, and no coordination.

**Verified working** on Claude Code Remote — web, mobile and remote CLI — on
2026-08-21: a session read its own identity, set its own title, and read the
change back, emoji intact.

**Reported not working** on Claude Desktop, where a session could rename every
session except itself. Unverified, and worth re-testing before anything is built
on either answer.

So the procedure is: **try, then read back**. If the title comes back carrying
the triple, done. If it does not, this surface cannot self-tag, and the tag has
to be applied by a peer.

### The peer path, and the rule it must not break

A peer session cannot read the target repository's `.identicon/` — it is not in
that checkout. It must therefore **never work out the triple itself**. The
triple travels to it as data, read by the session that *is* in the repository
and handed over.

Derivation happens exactly once, in the checkout that owns the mark. Everything
downstream of that is a copy. This is what makes an unbounded number of peers
safe: none of them can invent a mark, so none of them can be wrong about one.

### Timing

The server titles a session from its first prompt, seconds after it starts —
observed at about forty-five seconds. **A tag applied before that is silently
overwritten.**

So tagging happens at the *end* of a turn, not the start of a session, and any
later turn that notices the prefix missing restores it. Repetition costs a
string comparison and removes the need to know the auto-titler's schedule, which
is not documented and is not ours.

## Removal

"Remove the tricolour" means three things, together:

1. strip the prefix from this session's title;
2. strip it from every **live** session on this repository;
3. remove the tagging section from `CLAUDE.md`, so nothing re-applies it.

The third is what makes the first two mean anything. A removal that left the
repository opted in would be undone by the next turn's self-heal — a switch that
switches nothing. So there is deliberately **no per-session removal**: the unit
of the decision is the repository, because the unit of the mark is the
repository.

It edits a tracked file, so say so, and say that the opt-out lives or dies with
the commit.

## Reapply

Needed when the mark itself changes: new vectors, a new seed, a renamed
repository. It is **always user-invoked**. There is no schedule.

**Scope is one repository, run from a checkout of it.** This is a direct
consequence of the source-of-truth rule rather than a limitation of effort: a
session cannot obtain another repository's tricolour without either deriving it
(forbidden) or copying a sibling's (which is exactly the stale value a reapply
exists to replace). Reapplying across projects means invoking it in each. The
side benefit is that the blast radius of any single invocation is one project's
sessions.

The ladder, each rung requiring an explicit yes:

| rung | default |
|---|---|
| this session | the ordinary act; no confirmation |
| live sessions on this repository | **confirm**, listing them by name first |
| archived sessions on this repository | never unless named; then confirm |

Archived sessions are in scope for the feature and out of scope for its default:
they are the ones most likely to be re-read later and least likely to be
watched. Show what will change, change what was agreed, report what changed.

## Degradation

Every one of these is silent. A feature about legibility must not become the
noisiest thing in the transcript.

- **No session-renaming tool** (a plain terminal with no session manager): do
  nothing, say nothing.
- **No session identity available**: same.
- **No `.identicon/`**: same.
- **A rename that is refused or reverts**: report once, do not retry, do not
  fall back to asking a peer without being asked.

## Deliberately not here

- **No cron, no scheduled sweep.** It is external to the architecture, it is
  invasive, and a schedule assumes a machine that is always the same machine.
  Refresh is a thing the user asks for.
- **No hook.** A hook cannot call a session-management tool, so it could only
  ask the model to — which is what the instruction already does, without the
  cost of running in every session in every repository.
- **No derivation from the remote URL**, though it is sitting right there in the
  session list and would work. See the one rule.
- **No blanket cross-repository sweep**, for the reason under Reapply.

## Deferred

- **Take `CLAUDE.md` out of the generator.** The signing block is Claude
  Colophon's instruction, living in the generator's file. Doing it now would collide with
  the file split already under way there, so it waits — but nothing is added to
  that file in the meantime, and the tagging section is written by this
  feature's own tooling from the start rather than being put in the wrong place
  and moved later.

The switch is `--enable` and `--disable` here, and does not become a flag on the
generator. A generator has no opinion about whether Claude renames a session.
